"""Measure a business from its own statements, by arithmetic alone.

The statement stream's counterpart to `understanding_engine`, and the
same kind of function: deterministic, total, and incapable of producing
a number that does not trace to cells this platform read back out of a
filing.

Every measure is declared as a **recipe** — which statement it is read
from, which figures it consumes, and which of four arithmetic forms
relates them. Declaring them keeps the recipes readable as a list of
what this platform can measure and why, and keeps the code that
computes them one function rather than nine.

Nothing here scores, ranks or judges. A current ratio of 0.8 comes out
as 0.8; whether that is comfortable is a rule table's business, one
layer up.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto

from app.domain.agreement import Agreement
from app.domain.evidence import EvidenceNotApplicable
from app.domain.financial_statement_consensus import (
    ConsensusFact,
    FinancialStatementConsensus,
)
from app.domain.financial_statements import (
    STATEMENT_NAMES,
    StatementConcept,
    StatementKind,
)
from app.domain.financial_understanding import (
    MEASURE_NAMES,
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    MeasuredChange,
    MeasuredNet,
    MeasuredRatio,
    ReportedFigure,
    preceding,
)


class Arithmetic(StrEnum):
    """How a recipe relates the figures it consumes."""

    #: The first over the second, both in one column of one table.
    RATIO = auto()

    #: The first less the magnitude of the second, same discipline.
    NET_OF = auto()

    #: One figure against the same line in the closest earlier year the
    #: row prints, read off the filer's own column headers.
    CHANGE = auto()

    #: One figure as the filer printed it, at the caption's scale.
    LEVEL = auto()


@dataclass(frozen=True, slots=True)
class Recipe:
    """What one measure is computed from, declared rather than coded."""

    statement: StatementKind
    arithmetic: Arithmetic
    concepts: tuple[StatementConcept, ...]


#: Every measure this platform can compute, and exactly how.
#:
#: The list is short because the door only opens for a named consumer:
#: each entry is a figure one of the four financial analysts' rule
#: tables scores. Nothing is here because a taxonomy of ratios would
#: have looked more complete.
RECIPES: dict[FinancialMeasure, Recipe] = {
    FinancialMeasure.GROSS_MARGIN: Recipe(
        StatementKind.INCOME_STATEMENT,
        Arithmetic.RATIO,
        (StatementConcept.GROSS_PROFIT, StatementConcept.TOTAL_REVENUE),
    ),
    FinancialMeasure.OPERATING_MARGIN: Recipe(
        StatementKind.INCOME_STATEMENT,
        Arithmetic.RATIO,
        (StatementConcept.OPERATING_INCOME, StatementConcept.TOTAL_REVENUE),
    ),
    FinancialMeasure.NET_MARGIN: Recipe(
        StatementKind.INCOME_STATEMENT,
        Arithmetic.RATIO,
        (StatementConcept.NET_INCOME, StatementConcept.TOTAL_REVENUE),
    ),
    FinancialMeasure.REVENUE_GROWTH: Recipe(
        StatementKind.INCOME_STATEMENT,
        Arithmetic.CHANGE,
        (StatementConcept.TOTAL_REVENUE,),
    ),
    FinancialMeasure.EARNINGS_GROWTH: Recipe(
        StatementKind.INCOME_STATEMENT,
        Arithmetic.CHANGE,
        (StatementConcept.NET_INCOME,),
    ),
    FinancialMeasure.CURRENT_RATIO: Recipe(
        StatementKind.BALANCE_SHEET,
        Arithmetic.RATIO,
        (
            StatementConcept.TOTAL_CURRENT_ASSETS,
            StatementConcept.TOTAL_CURRENT_LIABILITIES,
        ),
    ),
    FinancialMeasure.LIABILITIES_TO_EQUITY: Recipe(
        StatementKind.BALANCE_SHEET,
        Arithmetic.RATIO,
        (StatementConcept.TOTAL_LIABILITIES, StatementConcept.TOTAL_EQUITY),
    ),
    FinancialMeasure.OPERATING_CASH_FLOW: Recipe(
        StatementKind.CASH_FLOW_STATEMENT,
        Arithmetic.LEVEL,
        (StatementConcept.OPERATING_CASH_FLOW,),
    ),
    FinancialMeasure.FREE_CASH_FLOW: Recipe(
        StatementKind.CASH_FLOW_STATEMENT,
        Arithmetic.NET_OF,
        (
            StatementConcept.OPERATING_CASH_FLOW,
            StatementConcept.CAPITAL_EXPENDITURES,
        ),
    ),
}


def measure(
    symbol: str,
    statements: Mapping[StatementKind, FinancialStatementConsensus],
) -> FinancialUnderstanding:
    """
    What these statements measure about the business, computed once.

    Deterministic given the consensuses, in the recipes' order, with no
    model asked and nothing re-read. Raises `ValueError` for an empty
    mapping or for consensuses of different documents: a measure that
    divided this year's revenue by last filing's equity would be
    arithmetic over two companies-in-time and nothing downstream could
    see that it happened.
    """

    if not statements:
        raise ValueError(
            "A financial understanding is derived from statement consensus; "
            "none was given."
        )

    keys = {consensus.source.key for consensus in statements.values()}

    if len(keys) > 1:
        raise ValueError(
            "A financial understanding is a property of one immutable "
            f"document, and these consensuses came from {len(keys)}."
        )

    for kind, consensus in statements.items():
        if consensus.statement is not kind:
            raise ValueError(
                f"A {consensus.statement.value} consensus was given as the "
                f"{kind.value}."
            )

    first = next(iter(statements.values()))

    return FinancialUnderstanding(
        symbol=symbol.upper().strip(),
        source=first.stated_source(),
        reading=_reading(statements),
        quorate=all(consensus.is_quorate for consensus in statements.values()),
        observation_count=min(
            consensus.observation_count for consensus in statements.values()
        ),
        quorum=max(consensus.quorum for consensus in statements.values()),
        statements=tuple(kind for kind in StatementKind if kind in statements),
        measures=tuple(
            _measured(name, recipe, statements.get(recipe.statement))
            for name, recipe in RECIPES.items()
        ),
    )


def _measured(
    name: FinancialMeasure,
    recipe: Recipe,
    consensus: FinancialStatementConsensus | None,
) -> EstablishedMeasure:
    """One measure, computed or absent with the reason it is absent."""

    if consensus is None:
        return EstablishedMeasure(
            measure=name,
            value=None,
            absent_because=(
                f"{MEASURE_NAMES[name]} is read from the "
                f"{STATEMENT_NAMES[recipe.statement]}, and this "
                "platform holds no consensus on that statement for this "
                "filing. Nothing about the company follows from that."
            ),
        )

    facts = [consensus.fact(concept) for concept in recipe.concepts]

    for concept, fact in zip(recipe.concepts, facts, strict=True):
        if fact is None or not fact.is_located:
            return EstablishedMeasure(
                measure=name,
                value=None,
                absent_because=_unestablished(name, concept, fact),
            )

    located = [fact for fact in facts if fact is not None]
    anchors = [fact.anchor for fact in located if fact.anchor is not None]

    try:
        value, basis, stated = _arithmetic(recipe, anchors, located)
    except EvidenceNotApplicable as refused:
        return EstablishedMeasure(
            measure=name,
            value=None,
            absent_because=(f"{MEASURE_NAMES[name]} was not computed: {refused}"),
        )

    return EstablishedMeasure(
        measure=name,
        value=value,
        basis=basis,
        stated=stated,
        support=_narrowest(located),
    )


def _arithmetic(
    recipe: Recipe,
    anchors: list[ReportedFigure],
    facts: list[ConsensusFact],
) -> tuple[float, tuple[ReportedFigure, ...], str]:
    """The four forms, each refusing rather than returning a bad number."""

    if recipe.arithmetic is Arithmetic.RATIO:
        ratio = MeasuredRatio(numerator=anchors[0], denominator=anchors[1])

        return ratio.ratio, (ratio.numerator, ratio.denominator), ratio.stated()

    if recipe.arithmetic is Arithmetic.NET_OF:
        net = MeasuredNet(gross=anchors[0], deducted=anchors[1])

        return net.net, (net.gross, net.deducted), net.stated()

    if recipe.arithmetic is Arithmetic.CHANGE:
        anchor = anchors[0]
        earlier = preceding(facts[0].row, anchor)

        if earlier is None:
            raise EvidenceNotApplicable(
                f'the row "{anchor.label}" prints no earlier period this '
                "platform can date from the filer's own column headers, so "
                "there is nothing to measure a change against"
            )

        change = MeasuredChange(later=anchor, earlier=earlier)

        return change.change, (change.later, change.earlier), change.stated()

    anchor = anchors[0]

    return anchor.value, (anchor,), anchor.stated()


def _unestablished(
    name: FinancialMeasure,
    concept: StatementConcept,
    fact: ConsensusFact | None,
) -> str:
    """Why a measure has no number, in the consensus's own words.

    The consensus already worded why the figure is absent — the reading
    located no such cell, the statement was never located, the claim did
    not settle — and this layer passes that through rather than
    restating it. Compensating for a gap and re-wording one are the same
    mistake at different volumes.
    """

    if fact is None:
        return (
            f"{MEASURE_NAMES[name]} needs {concept.value}, which no "
            "observation of this statement was asked for."
        )

    return (
        f"{MEASURE_NAMES[name]} needs {concept.value}, which is not "
        f"established: {fact.unlocated_because}"
    )


def _narrowest(facts: list[ConsensusFact]) -> Agreement | None:
    """The weakest agreement among the claims a measure consumed.

    A measure is exactly as established as the narrowest figure beneath
    it — the rule the archetype already holds to, applied to arithmetic
    instead of to rules. Chosen by stability alone, so a figure five
    readings agreed on never lends its firmness to one that three did.
    """

    answered = [fact.agreement for fact in facts if fact.agreement.readings > 0]

    if not answered:
        return None

    return min(answered, key=lambda claim: claim.stability or 0.0)


def _reading(
    statements: Mapping[StatementKind, FinancialStatementConsensus],
) -> Provenance:
    """The derivation stated, dated to the newest consensus beneath it."""

    named = ", ".join(
        STATEMENT_NAMES[kind] for kind in StatementKind if kind in statements
    )

    widths = sorted({consensus.observation_count for consensus in statements.values()})

    counted = (
        f"{widths[0]} observations"
        if len(widths) == 1
        else f"{widths[0]}–{widths[-1]} observations"
    )

    return Provenance(
        source=(
            f"computed by this platform from the {named} — "
            f"{counted} apiece, no figure derived by a model"
        ),
        observed_at=max(_observed(consensus) for consensus in statements.values()),
    )


def _observed(consensus: FinancialStatementConsensus) -> datetime:
    return consensus.reading.observed_at
