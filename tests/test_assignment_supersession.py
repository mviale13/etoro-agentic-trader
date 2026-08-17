"""A positive assignment stops voting where a qualified reading reassigned it.

BQ27. The regression this repairs was measured before it was repaired:
combining Goldman's five production readings with BQ26's five natives
deadlocked `total_revenue` 5-against-5 — `majority=False`, `refused=None` —
because the old readings positively assigned the row to `TOTAL_REVENUE` and
the new ones, asked about both concepts, assigned the same physical fact to
`REVENUE_NET_OF_INTEREST_EXPENSE`. That is not disagreement about a figure;
it is a later, semantically qualified assignment, and BQ23's truthful
refusal dissolved into *unsettled*.

The mandatory controls pin the rule's six proof obligations one at a time,
because each one missing must keep the assignment voting.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from app.domain.assignment_supersession import (
    AssignmentStanding,
    assignment_voting,
    rule_assignments,
    same_reported_fact,
)
from app.domain.financial_statement_consensus import statement_consensus_of
from app.domain.financial_statements import (
    ConceptContract,
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
    concept_vocabulary_fingerprint,
    producing_contract,
)
from app.domain.financing_cost_refusal import RefusalStanding
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from tests.test_financial_statement_store import source

INCOME = StatementKind.INCOME_STATEMENT
REVENUE = StatementConcept.TOTAL_REVENUE
TARGET = StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE
NII = StatementConcept.NET_INTEREST_INCOME
EARNINGS = StatementConcept.NET_INCOME

PRODUCTION = "data/statements"
PRESERVED = "data/experiments/statement-observations/bq26/statements"

#: Goldman's shape, from the filing itself: the marker one row above the
#: contested total, net income far below, one table, one column.
TOTAL = ("Total net revenues", "58,283", 58283.0, 12)
MARKER = ("Net interest income", "13,559", 13559.0, 11)
INCOME_LINE = ("Net earnings", "17,176", 17176.0, 26)


def figure(
    label: str,
    printed: str,
    value: float,
    *,
    row: int,
    table: int = 0,
    column: int = 3,
    header: str = "2025",
) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header=header,
        printed=printed,
        value=value,
        cell=CellReference(table=table, row=row, column=column),
        caption="(in millions)",
    )


def observation(
    facts: tuple[StatementFact, ...],
    stamped: tuple[ConceptContract, ...] = (),
) -> FinancialStatementObservation:
    return FinancialStatementObservation(
        symbol="EXA",
        statement=INCOME,
        facts=facts,
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 17, tzinfo=UTC)
        ),
        produced_under=stamped,
    )


def located(concept: StatementConcept, anchor: ReportedFigure) -> StatementFact:
    return StatementFact(concept=concept, anchor=anchor, row=(anchor,))


def absent(concept: StatementConcept, because: str) -> StatementFact:
    return StatementFact(concept=concept, anchor=None, unlocated_because=because)


def old_reading() -> FinancialStatementObservation:
    """A pre-BQ24 reading: the row positively assigned to `total_revenue`."""

    return observation(
        (
            located(REVENUE, figure(*TOTAL[:3], row=TOTAL[3])),
            located(NII, figure(*MARKER[:3], row=MARKER[3])),
            located(EARNINGS, figure(*INCOME_LINE[:3], row=INCOME_LINE[3])),
        )
    )


def native_reading(
    *,
    target_anchor: ReportedFigure | None = None,
    marker_anchor: ReportedFigure | None = None,
    stamped: tuple[ConceptContract, ...] | None = None,
) -> FinancialStatementObservation:
    """A BQ24-era reading: asked both questions, the row assigned to the
    new concept, `total_revenue` declined by arbitration."""

    target = (
        target_anchor if target_anchor is not None else figure(*TOTAL[:3], row=TOTAL[3])
    )
    marker = (
        marker_anchor
        if marker_anchor is not None
        else figure(*MARKER[:3], row=MARKER[3])
    )

    return observation(
        (
            absent(
                REVENUE,
                "The reading cited the row for total_revenue, and this "
                "statement's own structure reads that row as "
                "revenue_net_of_interest_expense instead.",
            ),
            located(TARGET, target),
            located(NII, marker),
            located(EARNINGS, figure(*INCOME_LINE[:3], row=INCOME_LINE[3])),
        ),
        stamped if stamped is not None else producing_contract(INCOME),
    )


def standings(observations) -> list[AssignmentStanding]:
    return [r.standing for r in rule_assignments(REVENUE, tuple(observations))]


# ── the formal rule, obligation by obligation ────────────────────────


def test_the_specimen_shape_supersedes() -> None:
    """All six obligations met: the assignment stops voting."""

    old, native = old_reading(), native_reading()

    rulings = rule_assignments(REVENUE, (old, native))

    assert [r.standing for r in rulings] == [AssignmentStanding.SUPERSEDED]
    assert "revenue_net_of_interest_expense" in rulings[0].because
    assert "only its authority" in rulings[0].because

    assert assignment_voting(REVENUE, (old, native)) == (native,)


def test_without_a_stored_superseder_nothing_is_superseded() -> None:
    """§3: what today's extractor would choose is never evidence.

    Five old positives alone — the state production is in — stay ACTIVE
    even though today's code, replayed over the document, would assign
    the row differently. No observed later assignment, no supersession.
    """

    olds = tuple(old_reading() for _ in range(5))

    assert standings(olds) == [AssignmentStanding.ACTIVE] * 5
    assert assignment_voting(REVENUE, olds) == olds


def test_a_materially_different_value_is_not_the_same_fact() -> None:
    """A conflict is not removed by calling it a reassignment."""

    other_value = native_reading(
        target_anchor=figure("Total net revenues", "59,000", 59000.0, row=12)
    )

    assert standings((old_reading(), other_value)) == [AssignmentStanding.ACTIVE]


def test_the_same_number_on_a_different_row_is_not_the_same_fact() -> None:
    """Figure equality alone must never trigger supersession."""

    other_row = native_reading(target_anchor=figure(*TOTAL[:3], row=18))

    assert standings((old_reading(), other_row)) == [AssignmentStanding.ACTIVE]


def test_a_different_period_is_not_the_same_fact() -> None:
    other_period = native_reading(
        target_anchor=figure(
            "Total net revenues", "58,283", 58283.0, row=12, header="2024"
        )
    )

    assert standings((old_reading(), other_period)) == [AssignmentStanding.ACTIVE]


def test_concepts_without_mutually_exclusive_predicates_supersede_nothing() -> None:
    """§7: same cell, different concept, no discriminating rules — ambiguity
    remains. `GROSS_PROFIT` declares no qualification, so a reading that
    assigned the cell there is not semantic evidence about anything."""

    gross = observation(
        (
            absent(REVENUE, "declined"),
            located(StatementConcept.GROSS_PROFIT, figure(*TOTAL[:3], row=TOTAL[3])),
            located(NII, figure(*MARKER[:3], row=MARKER[3])),
        ),
        producing_contract(INCOME),
    )

    assert standings((old_reading(), gross)) == [AssignmentStanding.ACTIVE]

    # And a concept with no rule of its own can never lose a positive:
    # there are no rulings at all, not a ruling of ACTIVE.
    assert rule_assignments(StatementConcept.GROSS_PROFIT, (gross,)) == ()


def test_a_superseder_must_be_native_to_both_questions() -> None:
    """§2.6: declining A must be an arbitrated choice, never ignorance.

    A reading stamped only for the new concept — or only for the old —
    proves it was not asked both questions, and withdraws nothing.
    """

    only_target = native_reading(
        stamped=(
            ConceptContract(
                concept=TARGET, fingerprint=concept_vocabulary_fingerprint(TARGET)
            ),
        )
    )
    only_revenue = native_reading(
        stamped=(
            ConceptContract(
                concept=REVENUE, fingerprint=concept_vocabulary_fingerprint(REVENUE)
            ),
        )
    )
    unstamped = native_reading(stamped=())

    for superseder in (only_target, only_revenue, unstamped):
        assert standings((old_reading(), superseder)) == [AssignmentStanding.ACTIVE]


def test_the_deciding_evidence_must_be_in_the_superseding_reading() -> None:
    """§2.5: the marker is read from the statement by the same observation."""

    no_marker = observation(
        (
            absent(REVENUE, "declined"),
            located(TARGET, figure(*TOTAL[:3], row=TOTAL[3])),
            located(EARNINGS, figure(*INCOME_LINE[:3], row=INCOME_LINE[3])),
        ),
        producing_contract(INCOME),
    )

    assert standings((old_reading(), no_marker)) == [AssignmentStanding.ACTIVE]


def test_a_marker_below_the_fact_supports_neither_reassignment() -> None:
    """The structure must positively support B and refute A — a marker
    printed below the total does neither, so an assignment moved only by
    lexical or ordering accident withdraws nothing."""

    marker_below = native_reading(
        target_anchor=figure(*TOTAL[:3], row=5),
        marker_anchor=figure(*MARKER[:3], row=9),
    )

    old_at_five = observation(
        (
            located(REVENUE, figure(*TOTAL[:3], row=5)),
            located(EARNINGS, figure(*INCOME_LINE[:3], row=INCOME_LINE[3])),
        )
    )

    assert standings((old_at_five, marker_below)) == [AssignmentStanding.ACTIVE]


def test_an_unrelated_concept_contract_changes_nothing() -> None:
    """§7: a stamp moving on a concept outside the pair has no effect."""

    weird = list(producing_contract(INCOME))
    weird = [
        ConceptContract(concept=c.concept, fingerprint="feedfacefeedface")
        if c.concept is StatementConcept.PREMIUM_REVENUE
        else c
        for c in weird
    ]

    assert standings((old_reading(), native_reading(stamped=tuple(weird)))) == [
        AssignmentStanding.SUPERSEDED
    ]


def test_the_ruling_is_order_independent() -> None:
    """Recency is not evidence; reversing the set moves nothing."""

    old, native = old_reading(), native_reading()

    forward = rule_assignments(REVENUE, (old, native))
    backward = rule_assignments(REVENUE, (native, old))

    assert (
        [r.standing for r in forward]
        == [r.standing for r in backward]
        == [AssignmentStanding.SUPERSEDED]
    )


def test_the_rule_names_no_company_and_reads_no_label_text() -> None:
    """No company, no banking, no hard-coded label anywhere in the code."""

    from tests.test_financing_cost_refusal import _code_of

    code = _code_of("app/domain/assignment_supersession.py")

    for name in ("GS", "JPM", "AXP", "Goldman", "JPMorgan", "American Express"):
        assert not re.search(rf"\b{re.escape(name)}\b", code), name

    for word in (
        '"total net revenue',
        '"net interest income"',
        "'net'",
        "casefold",
        "lower()",
        "startswith",
        "bank",
    ):
        assert word not in code, word


# ── identity ─────────────────────────────────────────────────────────


def test_the_identity_is_five_conjuncts_and_value_is_never_sufficient() -> None:
    base = figure(*TOTAL[:3], row=12)

    assert same_reported_fact(base, figure(*TOTAL[:3], row=12))

    different = (
        figure("Total revenues", "58,283", 58283.0, row=12),
        figure("Total net revenues", "58,283", 58283.0, row=13),
        figure("Total net revenues", "58,283", 58283.0, row=12, table=1),
        figure("Total net revenues", "58,283", 58283.0, row=12, column=9),
        figure("Total net revenues", "58,283", 58283.0, row=12, header="2024"),
        figure("Total net revenues", "58,284", 58284.0, row=12),
    )

    for candidate in different:
        assert not same_reported_fact(base, candidate)


# ── the live specimens ───────────────────────────────────────────────


def mixed(symbol: str, key: str):
    production = JsonFinancialStatementStore(PRODUCTION).read(symbol, key, INCOME)
    preserved = JsonFinancialStatementStore(PRESERVED).read(symbol, key, INCOME)

    assert len(production) == 5 and len(preserved) == 5

    return statement_consensus_of((*production, *preserved))


def test_goldman_resolves_to_a_refusal_not_a_tie() -> None:
    """The mandatory GS control, on the real ten readings."""

    consensus = mixed("GS", "0000886982-26-000091")

    revenue = consensus.fact(REVENUE)

    assert revenue is not None
    assert revenue.withdrawn_assignments == 5
    assert not revenue.is_located

    # Semantically refused, not tied — BQ23's reason, once.
    assert revenue.refused is not None
    assert revenue.refused.standing is RefusalStanding.NET_OF_FINANCING_COST
    assert revenue.refused.figure.value == 58283.0
    assert revenue.unlocated_because is None
    assert revenue.absent_because is not None
    assert "total after financing cost" in revenue.absent_because

    # The new concept gains consensus.
    target = consensus.fact(TARGET)

    assert target is not None and target.anchor is not None
    assert target.anchor.value == 58283.0
    assert target.agreement.by_majority

    # Concept locality: the withdrawn readings' other facts still vote.
    for concept, value in ((EARNINGS, 17176.0), (NII, 13559.0)):
        fact = consensus.fact(concept)

        assert fact is not None and fact.anchor is not None
        assert fact.anchor.value == value
        assert fact.agreement.readings == 10, concept
        assert fact.withdrawn_assignments == 0, concept


def test_jpmorgan_resolves_the_same_way() -> None:
    consensus = mixed("JPM", "0001628280-26-008131")

    revenue = consensus.fact(REVENUE)

    assert revenue is not None
    assert revenue.withdrawn_assignments == 5
    assert revenue.refused is not None
    assert revenue.refused.figure.value == 182447.0

    target = consensus.fact(TARGET)

    assert target is not None and target.anchor is not None
    assert target.anchor.value == 182447.0
    assert target.agreement.by_majority

    earnings = consensus.fact(EARNINGS)

    assert earnings is not None and earnings.agreement.readings == 10


def test_american_express_needs_no_supersession_and_gets_none() -> None:
    """The control: no historical positive, so nothing to withdraw."""

    consensus = mixed("AXP", "0000004962-26-000080")

    revenue = consensus.fact(REVENUE)

    assert revenue is not None
    assert revenue.withdrawn_assignments == 0
    assert revenue.refused is None
    assert not revenue.is_located
    assert revenue.agreement.by_majority
    assert revenue.unlocated_because is not None

    target = consensus.fact(TARGET)

    assert target is not None and target.anchor is not None
    assert target.anchor.value == 72229.0
    assert target.agreement.by_majority


def test_the_live_mixed_set_is_order_independent() -> None:
    production = JsonFinancialStatementStore(PRODUCTION).read(
        "GS", "0000886982-26-000091", INCOME
    )
    preserved = JsonFinancialStatementStore(PRESERVED).read(
        "GS", "0000886982-26-000091", INCOME
    )

    forward = statement_consensus_of((*production, *preserved)).fact(REVENUE)
    backward = statement_consensus_of((*preserved, *production)).fact(REVENUE)

    assert forward is not None and backward is not None
    assert forward.withdrawn_assignments == backward.withdrawn_assignments == 5
    assert forward.refused is not None and backward.refused is not None
    assert forward.refused.because == backward.refused.because


def test_a_genuine_tie_is_never_masked_by_the_composition() -> None:
    """Unstamped later readings withdraw nothing, and the tie stays a tie.

    The composition fires only behind a withdrawal, so a real 5-vs-5 —
    two sets of readings the rule cannot tell apart — stays honestly
    unsettled rather than being papered over with a refusal.
    """

    olds = tuple(old_reading() for _ in range(5))
    unstamped = tuple(native_reading(stamped=()) for _ in range(5))

    revenue = statement_consensus_of((*olds, *unstamped)).fact(REVENUE)

    assert revenue is not None
    assert revenue.withdrawn_assignments == 0
    assert revenue.refused is None
    assert not revenue.agreement.by_majority
    assert revenue.unlocated_because is not None
    assert "unsettled" in revenue.unlocated_because


# ── history and the corpus ───────────────────────────────────────────


def test_the_stored_readings_are_byte_identical_after_the_derivation() -> None:
    store = JsonFinancialStatementStore(PRODUCTION)

    before = store.read("GS", "0000886982-26-000091", INCOME)

    mixed("GS", "0000886982-26-000091")

    after = store.read("GS", "0000886982-26-000091", INCOME)

    assert before == after

    for observation_ in after:
        fact = observation_.fact(REVENUE)

        assert fact is not None and fact.anchor is not None
        assert fact.anchor.label == "Total net revenues"
        assert observation_.produced_under == ()


def test_the_rule_is_inert_on_production() -> None:
    """No production consensus withdraws an assignment, and no fact moved.

    Production holds no observation of the new concept, so obligation 1
    can never be met — checked across the whole corpus rather than
    asserted.
    """

    import pathlib

    from app.services.financial_statement_service import FinancialStatementService

    service = FinancialStatementService(JsonFinancialStatementStore(PRODUCTION))

    symbols = sorted(
        {p.name.split(".")[0] for p in pathlib.Path(PRODUCTION).glob("*.json")}
    )

    for symbol in symbols:
        for consensus in service.established(symbol).values():
            for fact in consensus.facts:
                assert fact.withdrawn_assignments == 0, (symbol, fact.concept)


def test_no_fingerprint_and_no_schema_moved() -> None:
    from app.repositories.financial_statement_store import STATEMENT_SCHEMA_VERSION

    assert concept_vocabulary_fingerprint(REVENUE) == "ea9df9c5adbc7f44"
    assert concept_vocabulary_fingerprint(TARGET) == "3e077c247f109a37"
    assert STATEMENT_SCHEMA_VERSION == 3
