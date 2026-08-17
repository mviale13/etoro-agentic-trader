"""Read the figures a primary statement prints, and refuse anything else."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.domain.evidence import EvidenceNotApplicable
from app.domain.financial_statements import (
    CONCEPT_LABELS,
    CONCEPT_QUESTIONS,
    STATEMENT_NAMES,
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
    concepts_of,
    matches_concept,
    producing_contract,
    statement_contenders,
    statement_tables,
    statement_text,
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
  per-share figure, not a note. The line the statement prints under the
  label the concept describes is the line, and nothing else is.
- Never cite the naming row, any row above it, or column `c0`. They
  name the rows and columns and measure nothing.
- `value` is the number that cell prints, written plainly: no
  thousands separators, no currency, no scale applied. 322,284 is
  322284. A number in accountants' parentheses is negative.
- Omit a concept rather than guess at it. Every cell you cite is read
  back out of the document and compared with what you said is in it,
  and an answer that disagrees with the document is discarded in full.
"""


def statement_schema(statement: StatementKind) -> dict[str, Any]:
    """The contract a statement reading must fill: cells, never answers.

    A figure is not something the reading asserts; it is something the
    reading points at, which this platform then reads for itself. The
    `value` field exists so a misaddressed citation becomes a
    disagreement between the reading and the document, which is caught.

    The concept enumeration is this statement's own. A reading of the
    cash flow statement cannot name a balance-sheet concept, because the
    schema it answers under does not contain one.
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
                            "enum": [
                                concept.value for concept in concepts_of(statement)
                            ],
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


def statement_prompt(document: SourceDocument, statement: StatementKind) -> str:
    """One statement's tables and one statement's concepts, and no more.

    The partition matters as much as the wording. A reading shown all of
    Item 8 could find "total revenue" on a cash flow statement's
    supplementary schedule and pass every check this platform runs,
    because the checks prove where a figure sits and never which
    statement it belongs to. Showing one statement is what proves it.
    """

    return "\n".join(
        (
            f"Company: {document.source.company}",
            f"Statement: the audited {STATEMENT_NAMES[statement]}.",
            "",
            "Concepts to locate, each as one cell for the most recent "
            "period or date the statement reports:",
            *(_asked(concept) for concept in concepts_of(statement)),
            "",
            "Locate each concept's cell in the tables below, or omit a "
            "concept whose figure is not there.",
            "",
            "--- TABLES BEGIN ---",
            *(table.stated() for table in statement_tables(document, statement)),
            "--- TABLES END ---",
        )
    )


def _asked(concept: StatementConcept) -> str:
    """One concept as the reading is asked it: the question and the rows.

    The accepted row labels are stated because withholding them made the
    reading guess, and a guess costs the whole observation rather than
    the one concept — `_validated` discards a reading that fails any
    check, deliberately, and that rule is not relaxed here.

    Measured: five corpus filings lost every figure on their income
    statement to a single mislabelled citation. Allstate cited "Property
    and casualty insurance premiums" for premium revenue, Citigroup and
    American Express cited "Total revenues, net of interest expense" for
    revenue, Deutsche Bank cited "Profit (loss)" for net income and
    Coca-Cola cited "Net Operating Revenues" — each of them a real row,
    read correctly, that this platform does not accept as answering the
    concept. The instruction to omit rather than guess was already
    there; what was missing was the fact needed to obey it.

    This grants the reading nothing. Every cited cell is still read back
    out of the document, its label still checked against `CONCEPT_LABELS`
    and its address still required to be distinct — so a label named
    here that the statement does not print cannot become a figure. The
    only outcome it can change is a guess into an omission.
    """

    accepted = ", ".join(f'"{form}"' for form in CONCEPT_LABELS[concept])

    lines = [f"- {concept.value}: {CONCEPT_QUESTIONS[concept]}"]
    lines.append(f"    Accepted row labels: {accepted}.")

    if concept is StatementConcept.TOTAL_EQUITY:
        lines.append(
            "    Also accepted: the same line with the company's own name "
            'inside it, such as "Total Example Group shareholders\' equity". '
            "Never a row that also names liabilities or noncontrolling "
            "interests — that is the balance sheet's grand total, not equity."
        )

    lines.append(
        "    A row labelled anything else is not this concept. Omit the "
        "concept rather than citing the closest row you can find."
    )

    return "\n".join(lines)


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
        self,
        symbol: str,
        document: SourceDocument,
        statement: StatementKind = StatementKind.INCOME_STATEMENT,
    ) -> FinancialStatementObservation:
        """
        Read one named statement of this document, retrying a refusal.

        A document in which this platform located no such statement
        yields a deterministic observation — every concept absent, the
        reason worded, no model call and no spend. That absence is a
        finding to store and serve, not a failure: which fact it states
        (no statement located, or a located statement with no readable
        table) travels in the wording.
        """

        if not statement_tables(document, statement):
            return self._unlocated(symbol, document, statement)

        rejection: ExtractionRejected | None = None

        for _ in range(MAX_ATTEMPTS):
            try:
                return await self._attempt(symbol, document, statement)
            except ExtractionRejected as rejected:
                rejection = rejected

        raise rejection or ExtractionRejected(
            f"The {STATEMENT_NAMES[statement]} could not be read."
        )

    async def _attempt(
        self,
        symbol: str,
        document: SourceDocument,
        statement: StatementKind,
    ) -> FinancialStatementObservation:
        request = DraftRequest(
            system_prompt=STATEMENT_SYSTEM_PROMPT,
            user_prompt=statement_prompt(document, statement),
            schema=statement_schema(statement),
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

        facts = self._validated(
            statement_tables(document, statement), payload, statement
        )

        return FinancialStatementObservation(
            symbol=symbol.upper().strip(),
            statement=statement,
            facts=facts,
            # The vocabulary this reading was permitted to accept,
            # stamped at the instant it read. Acquisition is the only
            # place where the live contract *is* the producing contract.
            produced_under=producing_contract(statement),
            located_among=statement_contenders(document, statement),
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
        statement: StatementKind,
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

            if concept not in concepts_of(statement):
                raise ExtractionRejected(
                    f"The reading located {concept.value!r} in the "
                    f"{STATEMENT_NAMES[statement]}, which is not the "
                    "statement this platform reads that figure from."
                )

            if concept in located:
                raise ExtractionRejected(
                    f"The reading located {concept.value!r} twice, so at "
                    "least one of the two is not what it was said to be."
                )

            located[concept] = raw

        facts = []
        cited: set[CellReference] = set()

        for concept in concepts_of(statement):
            raw = located.get(concept)

            if raw is None:
                facts.append(
                    StatementFact(
                        concept=concept,
                        anchor=None,
                        unlocated_because=(
                            f"The reading located no cell holding "
                            f"{CONCEPT_QUESTIONS[concept]} in the tables "
                            f"printed under the {STATEMENT_NAMES[statement]}'s "
                            "title."
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
        symbol: str, document: SourceDocument, statement: StatementKind
    ) -> FinancialStatementObservation:
        """Every concept absent, each absence saying which fact it states."""

        because = _no_statement(document, statement)

        return FinancialStatementObservation(
            symbol=symbol.upper().strip(),
            statement=statement,
            facts=tuple(
                StatementFact(
                    concept=concept,
                    anchor=None,
                    unlocated_because=because,
                )
                for concept in concepts_of(statement)
            ),
            # Stamped here too, and it matters more here than anywhere:
            # every fact in this observation is an absence, and an
            # absence is a claim about the vocabulary that failed to
            # match — the one claim a later reader cannot check against
            # the document.
            produced_under=producing_contract(statement),
            located_among=statement_contenders(document, statement),
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


def _no_statement(document: SourceDocument, statement: StatementKind) -> str:
    """Why a document yielded no statement table to read.

    Two different facts, worded apart, and only one of them might be
    about the company: a statement this platform never located, and a
    located statement that printed no table this platform could read.
    """

    named = STATEMENT_NAMES[statement]

    if not statement_text(document, statement).strip():
        return (
            f"This platform located no {named} in this document — no "
            f"{named} title begins a block here — so it read no figure. "
            "This is a fact about the reading, not about the company."
        )

    return (
        f"This document prints a {named} title, and no table this platform "
        "could read appears under it, so no figure was read."
    )
