"""Read the figures a primary statement prints, and refuse anything else."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.domain.evidence import EvidenceNotApplicable
from app.domain.financial_statements import (
    CONCEPT_QUESTIONS,
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
    matches_concept,
)
from app.domain.primary_source import SourceDocument
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    SourceTable,
    cited_number,
    cited_reference,
    figure_at,
    row_figures,
)
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)
from app.services.company_knowledge_extractor import (
    MAX_ATTEMPTS,
    MAX_TOKENS,
    ExtractionRejected,
)

STATEMENT_SYSTEM_PROMPT = """\
You locate numbers in a company's audited financial statements. You do
not analyse the company, and you do not calculate anything at all.

You are given the tables exactly as they were parsed out of the
statement the filer printed. Every cell is addressed: `[table N]`,
then `rR` for the row, then `cC` for the column.

The columns are named by the first row that labels more than one of
them. That is usually `r0`, but a filer who typesets a title inside
the table puts it in `r0` alone, and then `r1` names the columns.
Read the rows you are given rather than assuming which one it is.

Rules:
- For each concept you are asked for, locate the ONE cell holding that
  figure for the MOST RECENT period the table reports. The most recent
  period is named by the column headers; read them.
- Cite the statement's own line, not a subtotal of part of it, not a
  per-share figure, not a note. "Total net revenue" is the revenue
  line; "Net income" is the net income line.
- Never cite the naming row, any row above it, or column `c0`. They
  name the rows and columns and measure nothing.
- `value` is the number that cell prints, written plainly: no
  thousands separators, no currency, no scale applied. 322,284 is
  322284. A number in accountants' parentheses is negative.
- Omit a concept rather than guess at it. Every cell you cite is read
  back out of the document and compared with what you said is in it,
  and an answer that disagrees with the document is discarded in full.
"""


def statement_schema() -> dict[str, Any]:
    """The contract a statement reading must fill: cells, never answers.

    A figure is not something the reading asserts; it is something the
    reading points at, which this platform then reads for itself. The
    `value` field exists so a misaddressed citation becomes a
    disagreement between the reading and the document, which is caught.
    """

    return {
        "type": "object",
        "properties": {
            "located": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "concept": {
                            "type": "string",
                            "enum": [concept.value for concept in StatementConcept],
                        },
                        "table": {"type": "integer"},
                        "row": {"type": "integer"},
                        "column": {"type": "integer"},
                        "value": {
                            "type": "number",
                            "description": (
                                "The number this cell prints, with no "
                                "separators, no currency and no scale applied."
                            ),
                        },
                    },
                    "required": ["concept", "table", "row", "column", "value"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["located"],
        "additionalProperties": False,
    }


def statement_prompt(document: SourceDocument) -> str:
    return "\n".join(
        (
            f"Company: {document.source.company}",
            "",
            "Concepts to locate, each as one cell for the most recent period:",
            *(
                f"- {concept.value}: {CONCEPT_QUESTIONS[concept]}"
                for concept in StatementConcept
            ),
            "",
            "Locate each concept's cell in the tables below, or omit a "
            "concept whose figure is not there.",
            "",
            "--- TABLES BEGIN ---",
            *(table.stated() for table in document.income_statement_tables),
            "--- TABLES END ---",
        )
    )


class FinancialStatementExtractor:
    """
    Turn a printed statement into checked figures, or a worded refusal.

    The model locates; it never asserts. Every cell it cites is read
    back out of the parsed table and compared with what it said is
    there, the row's label must be one the concept declares, and the
    rest of the row is then read by this platform with no model claim
    anywhere in it. A reading that fails any check is discarded whole
    rather than partly trusted.
    """

    def __init__(self, provider: NarrativeProvider) -> None:
        self._provider = provider

    async def extract(
        self, symbol: str, document: SourceDocument
    ) -> FinancialStatementObservation:
        """
        Read this document's income statement, retrying a refused reading.

        A document in which this platform located no statement yields a
        deterministic observation — every concept absent, the reason
        worded, no model call and no spend. That absence is a finding
        to store and serve, not a failure: which fact it states (no
        statement located, or a located statement with no readable
        table) travels in the wording.
        """

        if not document.income_statement_tables:
            return self._unlocated(symbol, document)

        rejection: ExtractionRejected | None = None

        for _ in range(MAX_ATTEMPTS):
            try:
                return await self._attempt(symbol, document)
            except ExtractionRejected as rejected:
                rejection = rejected

        raise rejection or ExtractionRejected("The statement could not be read.")

    async def _attempt(
        self,
        symbol: str,
        document: SourceDocument,
    ) -> FinancialStatementObservation:
        request = DraftRequest(
            system_prompt=STATEMENT_SYSTEM_PROMPT,
            user_prompt=statement_prompt(document),
            schema=statement_schema(),
            max_tokens=MAX_TOKENS,
        )

        try:
            draft = await self._provider.draft(request)
        except NarrativeDeclined as declined:
            raise ExtractionRejected(str(declined)) from declined

        try:
            payload = json.loads(draft.text)
        except json.JSONDecodeError as error:
            raise ExtractionRejected(
                "The statement reader returned unreadable output."
            ) from error

        facts = self._validated(document.income_statement_tables, payload)

        return FinancialStatementObservation(
            symbol=symbol.upper().strip(),
            statement=StatementKind.INCOME_STATEMENT,
            facts=facts,
            source=document.source,
            reading=Provenance(
                source=(
                    f"{document.source.identifier} via "
                    f"{document.source.provider}, read by {draft.model}"
                ),
                observed_at=datetime.now(UTC),
            ),
        )

    def _validated(
        self,
        tables: tuple[SourceTable, ...],
        payload: dict[str, Any],
    ) -> tuple[StatementFact, ...]:
        """
        Each located concept checked against the cell it cites, in order:
        existence and agreement, correspondence, distinctness — then the
        row expansion, which is this platform's own reading and needs no
        check because nothing asserted it.
        """

        located: dict[StatementConcept, dict[str, Any]] = {}

        for raw in payload.get("located") or ():
            name = str(raw.get("concept") or "").strip()

            try:
                concept = StatementConcept(name)
            except ValueError as unknown:
                raise ExtractionRejected(
                    f"The reading located a concept, {name!r}, that this "
                    "platform never asked for."
                ) from unknown

            if concept in located:
                raise ExtractionRejected(
                    f"The reading located {concept.value!r} twice, so at "
                    "least one of the two is not what it was said to be."
                )

            located[concept] = raw

        facts = []
        cited: set[CellReference] = set()

        for concept in StatementConcept:
            raw = located.get(concept)

            if raw is None:
                facts.append(
                    StatementFact(
                        concept=concept,
                        anchor=None,
                        unlocated_because=(
                            f"The reading located no cell holding "
                            f"{CONCEPT_QUESTIONS[concept]} in the tables "
                            "printed under the statement's title."
                        ),
                    )
                )
                continue

            try:
                anchor = figure_at(
                    tables,
                    cited_reference(raw),
                    cited_number(raw, "value"),
                    f"The figure for {concept.value!r}",
                )

                if not matches_concept(concept, anchor.label):
                    raise EvidenceNotApplicable(
                        f"The figure for {concept.value!r} cites a row the "
                        f"filer labels {anchor.label!r}, which this platform "
                        "does not read as answering it."
                    )

                if anchor.cell in cited:
                    raise EvidenceNotApplicable(
                        f"The figure for {concept.value!r} cites a cell "
                        "already read as another concept, so one of the two "
                        "is not what it was said to be."
                    )
            except (EvidenceNotApplicable, TypeError, ValueError) as inapplicable:
                raise ExtractionRejected(str(inapplicable)) from inapplicable

            cited.add(anchor.cell)

            facts.append(
                StatementFact(
                    concept=concept,
                    anchor=anchor,
                    row=row_figures(tables[anchor.cell.table], anchor.cell.row),
                )
            )

        return tuple(facts)

    @staticmethod
    def _unlocated(
        symbol: str, document: SourceDocument
    ) -> FinancialStatementObservation:
        """Every concept absent, each absence saying which fact it states."""

        because = _no_statement(document)

        return FinancialStatementObservation(
            symbol=symbol.upper().strip(),
            statement=StatementKind.INCOME_STATEMENT,
            facts=tuple(
                StatementFact(
                    concept=concept,
                    anchor=None,
                    unlocated_because=because,
                )
                for concept in StatementConcept
            ),
            source=document.source,
            reading=Provenance(
                source=(
                    f"{document.source.identifier} via "
                    f"{document.source.provider}, located structurally by "
                    "this platform — no model was asked"
                ),
                observed_at=datetime.now(UTC),
            ),
        )


def _no_statement(document: SourceDocument) -> str:
    """Why a document yielded no statement table to read.

    Two different facts, worded apart, and only one of them might be
    about the company: a statement this platform never located, and a
    located statement that printed no table this platform could read.
    """

    if not document.income_statement_text.strip():
        return (
            "This platform located no income statement in this document — "
            "no statement title begins a block here — so it read no figure. "
            "This is a fact about the reading, not about the company."
        )

    return (
        "This document prints an income statement title, and no table this "
        "platform could read appears under it, so no figure was read."
    )
