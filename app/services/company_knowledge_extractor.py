"""Read structural facts out of a filing, and refuse anything else."""

from __future__ import annotations

import json
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
from app.domain.tabular_evidence import (
    CellReference,
    EvidenceNotApplicable,
    MeasuredShare,
    ReportedFigure,
    SourceTable,
    figure_at,
    normalised,
)
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

#: Segments sum past a consolidated total, and legitimately: consolidated
#: revenue is the segments *less* what they sold each other. Measured,
#: Disney's three segments are 102% of its group revenue and Volkswagen's
#: three are 108.5% of its — the difference being how much business the
#: parts do with each other, which no constant can predict.
#:
#: So this is a backstop rather than the guard it once was. What catches
#: a misread figure now is the cell it was read from: two segments cannot
#: cite one cell, and a cell whose label does not correspond to the
#: segment is refused. This only has to separate heavy intersegment trade
#: from a segment counted twice, which in a three-segment company would
#: land near 140%. A mix past it is discarded rather than normalised,
#: because a silently rescaled revenue mix is a fabricated one.
SHARE_TOLERANCE = 1.25

MIX_SYSTEM_PROMPT = """\
You locate numbers in tables a company printed in its annual report. You
do not analyse the company, and you do not calculate anything at all.

You are given the tables exactly as they were parsed out of the document.
Every cell is addressed: `[table N]`, then `rR` for the row, then `cC`
for the column. Row `r0` is the header row, which names the columns.

Tables are laid out one of two ways, and both are normal:
- Segments as ROWS, periods as columns. Then the total is another row,
  and every segment cell sits in the SAME COLUMN as the total.
- Segments as COLUMNS, line items as rows. Then the total is another
  column — "Group", "Konzern", "Total" — and every segment cell sits in
  the SAME ROW as the total, the row for revenue.

Rules:
- First locate `total`: the one cell holding TOTAL revenue for the whole
  company, for the most recent period the table reports.
- Then, for each segment name you are given, locate the cell holding THAT
  SEGMENT's revenue. Use the names you are given and no others.
- Every segment cell must be in the SAME TABLE as the total, and must
  share either its row or its column with the total — whichever the
  table's layout calls for. Omit any segment whose revenue is not there.
- Never cite row `r0` or column `c0`. They name the rows and columns and
  measure nothing.
- Never cite a cell holding a percentage, a change, a margin, an operating
  income or a label. Revenue only.
- `value` is the number that cell prints, written plainly: no thousands
  separators, no currency, no scale applied. 322,284 is 322284.
- Omit a segment rather than guess at it. Every cell you cite is read back
  out of the document and compared with what you said is in it, and an
  answer that disagrees with the document is discarded in full.
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
- Report the revenue models the filing describes for each segment.
- Report no figures and no sizes. You are reading what the business is,
  not how large its parts are. Anything you could only get by reading a
  table belongs to a different question and is not asked here.
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


def _cell_schema(described: str) -> dict[str, Any]:
    """The address of one printed number, and what it is said to print."""

    return {
        "type": "object",
        "description": described,
        "properties": {
            "table": {"type": "integer"},
            "row": {"type": "integer"},
            "column": {"type": "integer"},
            "value": {
                "type": "number",
                "description": (
                    "The number this cell prints, with no separators, no "
                    "currency and no scale applied."
                ),
            },
        },
        "required": ["table", "row", "column", "value"],
        "additionalProperties": False,
    }


def mix_schema() -> dict[str, Any]:
    """
    The contract a revenue-mix reading must fill.

    Cells, not shares. A share is arithmetic over two figures, and asking
    a reading for the arithmetic is asking it for something the document
    does not contain — which is why the old contract's quotes could be
    exact and prove nothing. Here the reading points at two cells and the
    platform does the dividing.
    """

    segment = _cell_schema("The cell holding this segment's revenue.")

    properties = dict(segment["properties"])
    properties["segment"] = {"type": "string"}

    return {
        "type": "object",
        "properties": {
            "total": {
                "anyOf": [
                    _cell_schema("The cell holding total revenue."),
                    {"type": "null"},
                ],
                "description": (
                    "Null where no table reports a total revenue you can read."
                ),
            },
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": properties,
                    "required": [*segment["required"], "segment"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["total", "segments"],
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
            "Locate total revenue, and each segment's revenue, in the tables "
            "below. Omit any segment whose revenue does not share a row or a "
            "column with the total, in the same table.",
            "",
            "--- TABLES BEGIN ---",
            *(table.stated() for table in document.performance_tables),
            "--- TABLES END ---",
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
        How large each segment is, measured out of the tables that state it.

        A second reading, of a second section, because the two facts live
        apart: Item 1 describes the segments and reports no figures, and
        the discussion reports the figures against names it assumes you
        already have. Knowing that a company sells subscriptions, tickets
        and licences is directional; knowing which of them is most of the
        revenue is the fact a classification can rest on.

        And it is a reading of the *tables*, not of the prose beside them.
        A share is not something a filing says; it is arithmetic over two
        figures a filing prints, and a span quoted from flattened prose
        cannot show that a number belongs to the row it was found next to.
        So the reading locates cells, this platform reads those cells back
        out of the document, and it divides one by the other itself.

        A filing whose tables could not be read, or in which no total was
        found, keeps its segments and leaves their sizes absent. That is
        the honest outcome and the shares are never apportioned from what
        is left over.
        """

        if not knowledge.segments or not document.performance_tables:
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

        measured = self._measured(knowledge, document.performance_tables, payload)

        if not measured:
            return knowledge

        return replace(
            knowledge,
            segments=tuple(
                replace(segment, revenue=measured.get(segment.name.casefold()))
                for segment in knowledge.segments
            ),
        )

    def _measured(
        self,
        knowledge: CompanyKnowledge,
        tables: tuple[SourceTable, ...],
        payload: dict[str, Any],
    ) -> dict[str, MeasuredShare]:
        """
        Each segment's size, checked against the cells it was read from.

        Every one of them is measured against the *same* total cell. A
        mix whose segments were each divided by a different denominator
        would not be a mix of anything — the parts would not be parts of
        one whole — and requiring one denominator makes the shares add up
        to something a reader can interpret rather than a coincidence.
        """

        try:
            total = self._total(tables, payload.get("total"))
        except EvidenceNotApplicable as inapplicable:
            raise ExtractionRejected(str(inapplicable)) from inapplicable

        if total is None:
            return {}

        known = {segment.name.casefold() for segment in knowledge.segments}

        measured: dict[str, MeasuredShare] = {}
        cited: set[CellReference] = {total.cell}

        for raw in payload.get("segments") or ():
            name = str(raw.get("segment") or "").strip()

            if name.casefold() not in known:
                raise ExtractionRejected(
                    f"The revenue mix names a segment, {name!r}, that the "
                    "filing's business description never reported."
                )

            try:
                figure = figure_at(
                    tables,
                    _reference(raw),
                    _number(raw, "value"),
                    f"The revenue of {name!r}",
                )

                if figure.cell in cited:
                    raise EvidenceNotApplicable(
                        f"The revenue of {name!r} cites a cell already read as "
                        "another figure, so one of the two is not what it "
                        "was said to be."
                    )

                share = MeasuredShare(numerator=figure, denominator=total)

                # Against the coordinate that names the part, which is
                # the row where the segments run down the page and the
                # column header where they run across it.
                if not _corresponds(name, share.part):
                    raise EvidenceNotApplicable(
                        f"The revenue of {name!r} cites a cell the filing "
                        f"labels {share.part!r}, which is a different thing."
                    )

                measured[name.casefold()] = share
            except (EvidenceNotApplicable, TypeError, ValueError) as inapplicable:
                raise ExtractionRejected(str(inapplicable)) from inapplicable

            cited.add(figure.cell)

        stated = sum(share.share for share in measured.values())

        if stated > SHARE_TOLERANCE:
            raise ExtractionRejected(
                f"The measured revenue shares sum to {stated:.0%} of "
                f"{total.printed}, which cannot be a share of one company's "
                "revenue. The mix was discarded rather than rescaled."
            )

        return measured

    @staticmethod
    def _total(
        tables: tuple[SourceTable, ...],
        raw: Any,
    ) -> ReportedFigure | None:
        """The cell every segment is measured against, or nothing at all."""

        if not isinstance(raw, dict):
            # No table reported a total this reading could locate. The
            # segments keep their descriptions and lose their sizes,
            # which is the honest outcome rather than a failure.
            return None

        try:
            return figure_at(
                tables,
                _reference(raw),
                _number(raw, "value"),
                "The company's total revenue",
            )
        except (TypeError, ValueError) as unreadable:
            raise EvidenceNotApplicable(
                "The total revenue arrived without a number, so nothing "
                "could be measured against it."
            ) from unreadable

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

        text = normalised(document.business_description)

        segments = tuple(
            self._segment(raw, text) for raw in payload.get("segments") or ()
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
        #
        # It proves the filing describes this segment, and it proves
        # nothing about how large the segment is — which is why no size
        # is asked for here. A span establishes that content exists; a
        # quantity needs its row and its column, and this reading has
        # neither.
        if normalised(quoted) not in text:
            raise ExtractionRejected(
                f"The segment {name!r} quotes words that are not in the "
                "filing, so the whole reading was discarded."
            )

        models = tuple(
            RevenueModel(value)
            for value in raw.get("revenue_models") or ()
            if value in {model.value for model in RevenueModel}
        )

        return BusinessSegment(
            name=name,
            revenue=None,
            revenue_models=models,
            quoted=quoted,
        )


def _reference(raw: dict[str, Any]) -> CellReference:
    """The address a reading gave, as an address."""

    return CellReference(
        table=int(_number(raw, "table")),
        row=int(_number(raw, "row")),
        column=int(_number(raw, "column")),
    )


def _number(raw: dict[str, Any], named: str) -> float:
    """One number out of a citation, or a refusal to guess at it."""

    value = raw.get(named)

    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(
            f"A citation arrived without a {named}, so it points at nothing."
        )

    return float(value)


def _corresponds(name: str, label: str) -> bool:
    """
    Whether a filing's own label and a segment name are the same thing.

    The last applicability check, and the one the live failure needed: a
    cell whose figure is real, in the right table and on the right axis,
    and about a different part of the company. The two readings are of
    two sections, so the wording is rarely identical — "Experiences" is
    labelled "Experiences" in one and "Experiences segment" in the other
    — and containment either way is what tolerates that without
    tolerating a different part.
    """

    segment, printed = normalised(name), normalised(label)

    if not segment or not printed:
        return False

    return segment in printed or printed in segment
