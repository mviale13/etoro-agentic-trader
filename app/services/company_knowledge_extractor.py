"""Read structural facts out of a filing, and refuse anything else."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledge,
    RevenueModel,
)
from app.domain.provenance import Provenance
from app.providers.edgar_filings import Filing
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)

#: How much room the extraction gets. The business section runs to tens
#: of thousands of characters and the answer is a short structured list.
MAX_TOKENS = 8000

#: Shares are read to the nearest percent, so a set that sums a little
#: past 1.0 is rounding. One that sums well past it is a segment counted
#: twice, and the extraction is refused rather than normalised — a
#: silently rescaled revenue mix is a fabricated one.
SHARE_TOLERANCE = 1.05

_NOISE = re.compile(r"[^a-z0-9]+")

SYSTEM_PROMPT = """\
You extract structural facts from a company's annual report. You do not
analyse the company, rate it, or classify it.

Rules:
- Use only the filing text supplied. Never use anything you know about
  the company from elsewhere.
- Every segment you report must include `quoted`: a verbatim span copied
  from the filing text that names or describes that segment. Copy it
  exactly, character for character. An answer whose quotes are not found
  in the filing is discarded in full.
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


def user_prompt(filing: Filing) -> str:
    reference = filing.reference

    return "\n".join(
        (
            f"Company: {reference.company}",
            f"Filing: {reference.form} filed {reference.filed_on.isoformat()}",
            "",
            "Report the operating segments this filing describes, what each "
            "one sells, and the share of revenue where the filing states it.",
            "",
            "--- FILING TEXT BEGINS ---",
            filing.business_text,
            "--- FILING TEXT ENDS ---",
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

    async def extract(self, symbol: str, filing: Filing) -> CompanyKnowledge:
        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(filing),
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

        return self._validated(symbol, filing, payload, draft.model)

    def _validated(
        self,
        symbol: str,
        filing: Filing,
        payload: dict[str, Any],
        model: str,
    ) -> CompanyKnowledge:
        description = str(payload.get("description") or "").strip()

        if not description:
            raise ExtractionRejected(
                "The extractor described no business, so nothing was read."
            )

        document = _normalised(filing.business_text)

        segments = tuple(
            self._segment(raw, document) for raw in payload.get("segments") or ()
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

        reference = filing.reference

        return CompanyKnowledge(
            symbol=symbol.upper().strip(),
            description=description,
            segments=segments,
            source_form=reference.form,
            source_filed_on=reference.filed_on.isoformat(),
            source_accession=reference.accession,
            source_url=reference.url,
            reading=Provenance(
                source=f"{reference.form} via SEC EDGAR, read by {model}",
                observed_at=datetime.now(UTC),
            ),
        )

    @staticmethod
    def _segment(raw: dict[str, Any], document: str) -> BusinessSegment:
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
        if _normalised(quoted) not in document:
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
