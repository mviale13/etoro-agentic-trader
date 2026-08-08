"""One reading of a primary financial statement: an observation.

The knowledge platform's second acquisition, opened by a measured
demand: the first live decision reached `MONITOR` because filing-grade
financial facts did not exist, and the accepted assessment design fixed
the road — the primary statements enter through the same tabular chain
that earned trust on segment sizes, as their own stream with its own
measurements (`docs/architecture/FINANCIAL_STATEMENT_ACQUISITION.md`).

An observation here is one draw, exactly as a
`CompanyKnowledgeObservation` is: admissible, checked, and one of
several a quorum will hold. Nothing downstream consumes one directly —
what the platform serves is the consensus derived over the set, in
`app.domain.financial_statement_consensus`.

Deliberately its own stream, never pooled with the segment
observations. The two readings are shown different text — the
statement's tables against Item 1 and the discussion's — and a
consensus over readings of different strings would call the difference
instability, which is the rule that forced the segment stream's own
schema 10.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.evidence import normalised
from app.domain.primary_source import PrimarySource
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import ReportedFigure


class StatementKind(StrEnum):
    """Which primary statement a reading was of.

    One member, deliberately. The mechanism below is general; the
    vocabulary is not, and the balance sheet and the cash flow
    statement enter one at a time, when a consumer's demand for their
    figures is measured — never because a taxonomy would be tidier
    complete.
    """

    INCOME_STATEMENT = "income_statement"


class StatementConcept(StrEnum):
    """One figure this platform asks a statement for.

    A concept is a contract, not a label: the question it asks, worded
    in `CONCEPT_QUESTIONS`; and the row labels this platform accepts
    as answering it, declared in `CONCEPT_LABELS` and grown only by a
    live refusal naming the label a real filer used. A reading cannot
    relabel a row into a concept, because the label check reads the
    document, never the reading.
    """

    TOTAL_REVENUE = "total_revenue"
    NET_INCOME = "net_income"


#: What each concept asks for, in words a refusal can carry.
CONCEPT_QUESTIONS: dict[StatementConcept, str] = {
    StatementConcept.TOTAL_REVENUE: (
        "the company's total revenue for the most recent period the statement reports"
    ),
    StatementConcept.NET_INCOME: (
        "the company's net income for the most recent period the statement reports"
    ),
}

#: The row labels this platform reads as answering each concept,
#: compared after `normalised` so typography and case cannot decide.
#: Declared, deterministic, and deliberately short: every form here was
#: chosen because filers print it as the statement's own line, and a
#: label outside the list is refused with the filer's words in the
#: refusal — which is exactly the sentence that earns the next entry.
CONCEPT_LABELS: dict[StatementConcept, tuple[str, ...]] = {
    StatementConcept.TOTAL_REVENUE: (
        "total net revenue",
        "total net revenues",
        "total revenue",
        "total revenues",
        "net revenues",
        "net revenue",
        "revenues",
        "revenue",
        "net sales",
        "total net sales",
        "total sales and revenues",
        "total revenues and other income",
    ),
    StatementConcept.NET_INCOME: (
        "net income",
        "net income (loss)",
        "net earnings",
        "net earnings (loss)",
        "profit for the year",
        "profit for the period",
    ),
}


def matches_concept(concept: StatementConcept, label: str) -> bool:
    """Whether a filer's row label answers this concept.

    Equality after `normalised`, never containment. "Total net
    revenue" contains "revenue", and so does "Revenue from contracts
    with related parties" — a containment rule would read the second
    as the company's revenue. A declared form matches exactly or the
    cell is refused.
    """

    printed = normalised(label)

    return any(printed == normalised(form) for form in CONCEPT_LABELS[concept])


@dataclass(frozen=True, slots=True)
class StatementFact:
    """One concept, either located and checked or absent with its reason.

    Two claims travel together when located, and they are not equals:

    - **The anchor** is what the reading asserted and this platform
      checked — the cell for the most recent period, read back out of
      the document and compared with what the reading said is there.
    - **The row** is what this platform then read for itself: every
      figure the anchored row prints under a named column, prior
      periods included, each carrying its header verbatim. No model
      claim stands anywhere in it.

    Which column is which period is never interpreted here. The
    headers say, in the filer's words, and a consumer that needs the
    period reads the header it stored.
    """

    concept: StatementConcept

    #: The checked cell, or None where nothing was located.
    anchor: ReportedFigure | None

    #: The anchored row as this platform read it, anchor's cell
    #: included. Empty exactly when the anchor is absent.
    row: tuple[ReportedFigure, ...] = ()

    #: Why there is no figure, in words. "The reading located no cell"
    #: and "this platform located no statement" are different facts,
    #: and only one of them is about the filing.
    unlocated_because: str | None = None

    @property
    def is_located(self) -> bool:
        """Whether the statement was shown to print this figure."""

        return self.anchor is not None


@dataclass(frozen=True, slots=True)
class FinancialStatementObservation:
    """One reading of one primary statement of one immutable document.

    Facts, never conclusions — and observed facts, never the settled
    account. Immutable once taken, for the same reason every
    observation is: correcting one would destroy the disagreement the
    consensus exists to measure.

    Carries one fact per concept, always: a concept that could not be
    located is present as a worded absence, so a reader never has to
    infer whether a missing entry was refused, unlocated, or simply
    never asked about.
    """

    symbol: str

    statement: StatementKind

    facts: tuple[StatementFact, ...]

    source: PrimarySource

    reading: Provenance

    def fact(self, concept: StatementConcept) -> StatementFact | None:
        """This reading's answer for one concept, if it was asked."""

        for fact in self.facts:
            if fact.concept is concept:
                return fact

        return None

    @property
    def located_facts(self) -> tuple[StatementFact, ...]:
        """The concepts this reading located and this platform checked."""

        return tuple(fact for fact in self.facts if fact.is_located)

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()
