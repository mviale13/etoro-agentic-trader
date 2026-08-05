"""Read structural facts out of a filing, and refuse anything else."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledge,
    RevenueModel,
)
from app.domain.primary_source import SourceDocument
from app.domain.provenance import Provenance
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)

#: How much room the extraction gets. The business section runs to tens
#: of thousands of characters and the answer is a short structured list.
MAX_TOKENS = 8000

#: How many times a reading may be asked for before the failure stands.
#:
#: Quoting a filing verbatim is not reliably repeatable: measured over
#: Disney's 10-K, one attempt in three produced a span that survived the
#: grounding check, the others paraphrasing across a table boundary. The
#: contract is not what should give way — a retry asks the same question
#: again and holds the answer to the same rule, where relaxing the check
#: would let the paraphrase through.
MAX_ATTEMPTS = 3

#: Shares are read to the nearest percent, so a set that sums a little
#: past 1.0 is rounding. One that sums well past it is a segment counted
#: twice, and the extraction is refused rather than normalised — a
#: silently rescaled revenue mix is a fabricated one.
SHARE_TOLERANCE = 1.05

_NOISE = re.compile(r"[^a-z0-9]+")

MIX_SYSTEM_PROMPT = """\
You read one number per segment out of a company's management discussion.
You do not analyse the company and you do not classify it.

Rules:
- Report a share only for the segment names you are given. Never invent a
  segment, rename one, or merge two.
- Report `revenue_share` only where the discussion states revenue for that
  segment and you can read it. Where it does not, omit the segment
  entirely. Never apportion, estimate, or infer a share from a total.
- Every share must include `quoted`: a SHORT verbatim span copied from
  the discussion text — between five and fifteen words, from a single
  run of prose — showing that segment's revenue. Copy it exactly. Do not
  join text across a table cell or a line break. An answer whose quotes
  are not found in the text is discarded in full.
- Shares are fractions of total revenue, between 0 and 1.
"""

SYSTEM_PROMPT = """\
You extract structural facts from a company's annual report. You do not
analyse the company, rate it, or classify it.

Rules:
- Use only the filing text supplied. Never use anything you know about
  the company from elsewhere.
- Every segment you report must include `quoted`: a SHORT verbatim span
  copied from the filing text — between five and fifteen words, taken
  from a single run of prose. Copy it exactly, character for character.
  Do not join text across a table cell, a bullet or a line break, and do
  not tidy the wording. A short exact span is always better than a long
  approximate one: an answer whose quotes are not found in the filing is
  discarded in full, including the segments that were right.
- Report `revenue_share` only where the filing gives a figure you can
  read for that segment. Where it does not, use null. Do not estimate,
  apportion, or infer a share from anything.
- Report the revenue models the filing describes for each segment.
- Do not judge the company. Do not say whether a business is good, "high
  quality", durable, moaty, or attractive. You are reading, not deciding.
"""


class ExtractionRejected(Exception):
    """The extraction failed its grounding contract, with the reason worded."""


def extraction_schema() -> dict[str, Any]:
    """The structured contract an extraction must fill."""

    return {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": (
                    "One sentence on what the company does, from the filing."
                ),
            },
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "revenue_share": {
                            "type": ["number", "null"],
                            "description": (
                                "Share of total revenue, 0 to 1. Null unless "
                                "the filing gives a figure you can read."
                            ),
                        },
                        "revenue_models": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [model.value for model in RevenueModel],
                            },
                        },
                        "quoted": {
                            "type": "string",
                            "description": (
                                "A verbatim span from the filing describing "
                                "this segment. Copied exactly."
                            ),
                        },
                    },
                    "required": [
                        "name",
                        "revenue_share",
                        "revenue_models",
                        "quoted",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["description", "segments"],
        "additionalProperties": False,
    }


def user_prompt(document: SourceDocument) -> str:
    source = document.source

    return "\n".join(
        (
            f"Company: {source.company}",
            f"Document: {source.stated()}",
            "",
            "Report the operating segments this document describes and what "
            "each one sells.",
            "",
            "--- DOCUMENT TEXT BEGINS ---",
            document.business_description,
            "--- DOCUMENT TEXT ENDS ---",
        )
    )


def _normalised(text: str) -> str:
    """
    Text reduced to the characters that carry meaning.

    A filing's markup leaves stray spacing inside words — "B USINESS" is
    a real heading — so an exact match would reject quotes that are
    genuinely present. Removing everything but letters and digits keeps
    the check strict about the words and their order while forgiving the
    typography the document arrived with.
    """

    return _NOISE.sub("", text.casefold())


def mix_schema() -> dict[str, Any]:
    """The contract a revenue-mix reading must fill."""

    return {
        "type": "object",
        "properties": {
            "shares": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "segment": {"type": "string"},
                        "revenue_share": {"type": "number"},
                        "quoted": {"type": "string"},
                    },
                    "required": ["segment", "revenue_share", "quoted"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["shares"],
        "additionalProperties": False,
    }


def mix_prompt(document: SourceDocument, segments: tuple[str, ...]) -> str:
    return "\n".join(
        (
            f"Company: {document.source.company}",
            "",
            "Segments, exactly as reported. Use these names and no others:",
            *(f"- {name}" for name in segments),
            "",
            "For each segment the discussion states revenue for, report its "
            "share of total revenue. Omit any segment whose revenue you "
            "cannot read.",
            "",
            "--- DISCUSSION TEXT BEGINS ---",
            document.performance_discussion,
            "--- DISCUSSION TEXT ENDS ---",
        )
    )


class CompanyKnowledgeExtractor:
    """
    Turn a filing into structural facts, or into a worded refusal.

    The model reads; it never decides. What it returns is checked against
    the document it read: every segment carries a span the filing must
    actually contain, and an answer whose quotes are not there is
    discarded whole rather than partly trusted. A model cannot assert a
    segment into existence, because the assertion is not what is stored —
    the sentence from the filing is.

    Nothing here classifies. Which archetype these facts add up to is a
    rule's decision, taken later, from facts that have already survived
    this.
    """

    def __init__(self, provider: NarrativeProvider) -> None:
        self._provider = provider

    async def extract(self, symbol: str, document: SourceDocument) -> CompanyKnowledge:
        """
        Read this document, asking again where the reading is not grounded.

        A rejection is not necessarily a fact about the document: a model
        asked to copy from a filing sometimes paraphrases, and the same
        question put again is usually answered exactly. So the request is
        repeated, and every attempt is held to the identical contract.
        The last failure's wording is what survives, because that is what
        a reader is owed when nothing could be read.
        """

        rejection: ExtractionRejected | None = None

        for _ in range(MAX_ATTEMPTS):
            try:
                return await self._attempt(symbol, document)
            except ExtractionRejected as rejected:
                rejection = rejected

        raise rejection or ExtractionRejected("The document could not be read.")

    async def _attempt(
        self,
        symbol: str,
        document: SourceDocument,
    ) -> CompanyKnowledge:
        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(document),
            schema=extraction_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
        except NarrativeDeclined as declined:
            raise ExtractionRejected(str(declined)) from declined

        if not draft.text.strip():
            raise ExtractionRejected(
                "The extractor returned nothing, so no facts were read from the filing."
            )

        try:
            payload = json.loads(draft.text)
        except json.JSONDecodeError as error:
            raise ExtractionRejected(
                "The extractor returned unreadable output."
            ) from error

        knowledge = self._validated(symbol, document, payload, draft.model)

        return await self._with_revenue_mix(knowledge, document)

    async def _with_revenue_mix(
        self,
        knowledge: CompanyKnowledge,
        document: SourceDocument,
    ) -> CompanyKnowledge:
        """
        How large each segment is, read from the discussion that states it.

        A second reading, of a second section, because the two facts live
        apart: Item 1 describes the segments and reports no figures, and
        the discussion reports the figures against names it assumes you
        already have. Knowing that a company sells subscriptions, tickets
        and licences is directional; knowing which of them is most of the
        revenue is the fact a classification can rest on.

        A filing whose discussion could not be found, or whose figures
        could not be read, keeps its segments and leaves their sizes
        absent. That is the honest outcome and the shares are never
        apportioned from what is left over.
        """

        if not knowledge.segments or not document.performance_discussion:
            return knowledge

        request = DraftRequest(
            system_prompt=MIX_SYSTEM_PROMPT,
            user_prompt=mix_prompt(
                document,
                tuple(segment.name for segment in knowledge.segments),
            ),
            schema=mix_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
            payload = json.loads(draft.text)
        except (NarrativeDeclined, json.JSONDecodeError):
            # The segments stand; only their sizes are unread.
            return knowledge

        discussion = _normalised(document.performance_discussion)

        shares: dict[str, float] = {}

        for raw in payload.get("shares") or ():
            name = str(raw.get("segment") or "").strip()
            quoted = str(raw.get("quoted") or "").strip()
            share = raw.get("revenue_share")

            known = {segment.name.casefold() for segment in knowledge.segments}

            if name.casefold() not in known:
                raise ExtractionRejected(
                    f"The revenue mix names a segment, {name!r}, that the "
                    "filing's business description never reported."
                )

            if not quoted or _normalised(quoted) not in discussion:
                raise ExtractionRejected(
                    f"The revenue share for {name!r} quotes words that are "
                    "not in the discussion, so the mix was discarded."
                )

            if share is None or not 0.0 <= float(share) <= 1.0:
                raise ExtractionRejected(
                    f"The revenue share for {name!r} is {share}, which is not a share."
                )

            shares[name.casefold()] = float(share)

        total = sum(shares.values())

        if total > SHARE_TOLERANCE:
            raise ExtractionRejected(
                f"The revenue shares sum to {total:.0%}, which cannot be a "
                "share of one company's revenue. The mix was discarded "
                "rather than rescaled."
            )

        return replace(
            knowledge,
            segments=tuple(
                replace(
                    segment,
                    revenue_share=shares.get(
                        segment.name.casefold(),
                        segment.revenue_share,
                    ),
                )
                for segment in knowledge.segments
            ),
        )

    def _validated(
        self,
        symbol: str,
        document: SourceDocument,
        payload: dict[str, Any],
        model: str,
    ) -> CompanyKnowledge:
        description = str(payload.get("description") or "").strip()

        if not description:
            raise ExtractionRejected(
                "The extractor described no business, so nothing was read."
            )

        text = _normalised(document.business_description)

        segments = tuple(
            self._segment(raw, text) for raw in payload.get("segments") or ()
        )

        stated = sum(
            segment.revenue_share
            for segment in segments
            if segment.revenue_share is not None
        )

        if stated > SHARE_TOLERANCE:
            raise ExtractionRejected(
                f"The extracted revenue shares sum to {stated:.0%}, which "
                "cannot be a share of one company's revenue. The reading "
                "was discarded rather than rescaled."
            )

        source = document.source

        return CompanyKnowledge(
            symbol=symbol.upper().strip(),
            description=description,
            segments=segments,
            source=source,
            reading=Provenance(
                source=f"{source.identifier} via {source.provider}, read by {model}",
                observed_at=datetime.now(UTC),
            ),
        )

    @staticmethod
    def _segment(raw: dict[str, Any], text: str) -> BusinessSegment:
        name = str(raw.get("name") or "").strip()
        quoted = str(raw.get("quoted") or "").strip()

        if not name:
            raise ExtractionRejected("A segment arrived without a name.")

        if not quoted:
            raise ExtractionRejected(
                f"The segment {name!r} arrived without the words it was read "
                "from, so there is nothing to check it against."
            )

        # The grounding contract, enforced against the document rather
        # than trusted. This is what makes the model an extractor.
        if _normalised(quoted) not in text:
            raise ExtractionRejected(
                f"The segment {name!r} quotes words that are not in the "
                "filing, so the whole reading was discarded."
            )

        share = raw.get("revenue_share")

        if share is not None and not 0.0 <= float(share) <= 1.0:
            raise ExtractionRejected(
                f"The segment {name!r} reports a revenue share of {share}, "
                "which is not a share."
            )

        models = tuple(
            RevenueModel(value)
            for value in raw.get("revenue_models") or ()
            if value in {model.value for model in RevenueModel}
        )

        return BusinessSegment(
            name=name,
            revenue_share=float(share) if share is not None else None,
            revenue_models=models,
            quoted=quoted,
        )
