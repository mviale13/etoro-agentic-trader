"""The concept for a total struck after financing cost, and its offline gate.

BQ24. Everything here runs before a model is asked anything: the three
specimens qualify from held evidence, the negative controls fail, BQ23
still refuses all three as `TOTAL_REVENUE`, no stored observation gains the
concept, and nothing consumes it.

The specimens are proved *structurally* rather than by re-reading. For
Goldman and JPMorgan the candidate figure is the one BQ23 refused, read
back out of the live consensus; for American Express there is no located
figure — its label was never a `TOTAL_REVENUE` form — so the candidate is
supplied at the cell BQ22 measured, which is what makes it a simulation and
is said so here rather than implied.
"""

from __future__ import annotations

import pathlib

from app.domain.financial_statements import (
    CONCEPT_LABELS,
    CONCEPT_QUESTIONS,
    CONCEPT_STATEMENT,
    StatementConcept,
    StatementKind,
    concept_vocabulary_fingerprint,
    concepts_of,
    matches_concept,
)
from app.domain.financing_cost_refusal import (
    GOVERNED,
    RefusalStanding,
    Requirement,
    refusal_for,
)
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.financial_statement_service import FinancialStatementService

INCOME = StatementKind.INCOME_STATEMENT
REVENUE = StatementConcept.TOTAL_REVENUE
NET_OF_INTEREST = StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE
NII = StatementConcept.NET_INTEREST_INCOME

PRODUCTION = "data/statements"

#: The fingerprint of the concept's vocabulary as this commit publishes it.
#: Pinned so that widening it later is a visible act, and so the report's
#: figure and the code's cannot drift apart.
FINGERPRINT = "3e077c247f109a37"


def held(symbol: str):
    return FinancialStatementService(
        JsonFinancialStatementStore(PRODUCTION)
    ).established(symbol)[INCOME]


def marker_of(symbol: str) -> ReportedFigure:
    """The company's own established net interest income."""

    fact = held(symbol).fact(NII)

    assert fact is not None and fact.anchor is not None, symbol

    return fact.anchor


def candidate_of(symbol: str) -> ReportedFigure:
    """The figure BQ23 refused as `TOTAL_REVENUE`, from the live consensus."""

    fact = held(symbol).fact(REVENUE)

    assert fact is not None and fact.refused is not None, symbol

    return fact.refused.figure


def qualifies(figure: ReportedFigure, marker: ReportedFigure) -> bool:
    """Whether the candidate establishes the concept against this marker."""

    return refusal_for(NET_OF_INTEREST, figure, (figure,), {NII: marker}) is None


# ── the concept ──────────────────────────────────────────────────────


def test_the_concept_is_named_for_the_quantity_and_not_for_the_word_net() -> None:
    """`Net sales` is net of returns; this is net of an expense.

    The name is the invariant's first line of defence: three of the eleven
    gross top lines this platform establishes carry the word *net*, so a
    concept called `NET_REVENUE` would invite exactly the confusion the
    slice exists to end.
    """

    assert NET_OF_INTEREST.value == "revenue_net_of_interest_expense"

    assert "net_revenue" not in NET_OF_INTEREST.value
    assert "interest_expense" in NET_OF_INTEREST.value

    # It is a claim about the income statement, like the concept it is
    # distinguished from.
    assert CONCEPT_STATEMENT[NET_OF_INTEREST] is INCOME
    assert NET_OF_INTEREST in concepts_of(INCOME)


def test_the_question_states_the_structural_relationship() -> None:
    """A reading is *asked* for the relationship, not only for a total.

    One cell may answer only one concept, so the question has to carry the
    whole distinction — and it has to carry it without touching
    `total_revenue`'s own wording, which no stored reading may be
    retroactively asked to have seen.
    """

    asked = CONCEPT_QUESTIONS[NET_OF_INTEREST]

    assert "includes net interest income" in asked
    assert "This concept, and not total revenue, answers such a total" in asked

    # Each exclusion the invariant names.
    for excluded in (
        "Not a gross revenue line struck before any financing cost",
        "not a component of the total",
        "not a subtotal struck after a provision for credit losses",
        "not a total of a parent company alone",
    ):
        assert excluded in asked, excluded

    # And `total_revenue`'s question is untouched, byte for byte.
    assert CONCEPT_QUESTIONS[REVENUE] == (
        "the company's total revenue for the most recent period the statement reports"
    )


def test_the_rule_is_one_predicate_read_both_ways() -> None:
    """The marker that disproves a gross total is what establishes this one."""

    assert GOVERNED[REVENUE] == (NII, Requirement.ABSENT_ABOVE)
    assert GOVERNED[NET_OF_INTEREST] == (NII, Requirement.PRESENT_ABOVE)


def test_a_label_alone_never_establishes_it() -> None:
    """Every accepted form, with no marker: refused, one and all.

    This is the property that separates the concept from a lexical list.
    `Total income` names this quantity at two filers and a parent-company
    aggregate at a third, and the vocabulary cannot tell them apart.
    """

    for form in CONCEPT_LABELS[NET_OF_INTEREST]:
        figure = ReportedFigure(
            label=form,
            column_header="2025",
            printed="1,000",
            value=1000.0,
            cell=CellReference(table=0, row=9, column=3),
            caption="(in millions)",
        )

        assert matches_concept(NET_OF_INTEREST, form), form

        refusal = refusal_for(NET_OF_INTEREST, figure, (figure,), {})

        assert refusal is not None, form
        assert refusal.standing is RefusalStanding.FINANCING_COST_NOT_EVIDENCED
        assert refusal.disproved_by is None


# ── the three specimens ──────────────────────────────────────────────


def test_goldman_qualifies_and_reconciles() -> None:
    """`Total net revenues` 58,283 = 44,724 + 13,559."""

    candidate, marker = candidate_of("GS"), marker_of("GS")

    assert candidate.label == "Total net revenues"
    assert candidate.value == 58283.0
    assert marker.value == 13559.0

    assert qualifies(candidate, marker)
    assert 44724.0 + marker.value == candidate.value


def test_jpmorgan_qualifies_and_reconciles() -> None:
    """`Total net revenue` 182,447 = 87,004 + 95,443."""

    candidate, marker = candidate_of("JPM"), marker_of("JPM")

    assert candidate.label == "Total net revenue"
    assert candidate.value == 182447.0
    assert marker.value == 95443.0

    assert qualifies(candidate, marker)
    assert 87004.0 + marker.value == candidate.value


def test_american_express_qualifies_and_reconciles() -> None:
    """`Total revenues net of interest expense` 72,229 = 54,865 + 17,364.

    Simulated at the cell BQ22 measured, because AXP holds no located
    figure to read back: its label is not a `TOTAL_REVENUE` form, so there
    was never anything for BQ23 to refuse. The marker is its own.
    """

    marker = marker_of("AXP")

    assert marker.value == 17364.0
    assert marker.cell.table == 0 and marker.cell.row == 16

    candidate = ReportedFigure(
        label="Total revenues net of interest expense",
        column_header=marker.column_header,
        printed="72,229",
        value=72229.0,
        cell=CellReference(table=0, row=17, column=marker.cell.column),
        caption=marker.caption,
    )

    assert matches_concept(NET_OF_INTEREST, candidate.label)
    assert qualifies(candidate, marker)
    assert 54865.0 + marker.value == candidate.value

    # And it is *not* a `TOTAL_REVENUE` form — BQ11's refusal stands.
    assert not matches_concept(REVENUE, candidate.label)


# ── the negative controls ────────────────────────────────────────────


def test_no_industrial_top_line_can_reach_the_concept() -> None:
    """Two independent reasons, and either alone is enough.

    The eleven gross top lines the corpus establishes are excluded first
    lexically — not one of their labels is an accepted form — and second
    structurally, because not one of those statements establishes a net
    interest income at all.
    """

    labels = {}

    for symbol in (
        "AAPL",
        "ALL",
        "CB",
        "DIS",
        "HON",
        "MET",
        "PG",
        "TRV",
        "TSLA",
        "UNP",
        "WMT",
    ):
        income = held(symbol)
        fact = income.fact(REVENUE)

        assert fact is not None and fact.anchor is not None, symbol

        labels[symbol] = fact.anchor.label

        # 1. lexically out of reach.
        assert not matches_concept(NET_OF_INTEREST, fact.anchor.label), symbol

        # 2. structurally out of reach: no marker on the statement.
        marker = income.fact(NII)

        assert marker is None or not marker.is_located, symbol

        # And were the label ever accepted, the absent marker would refuse
        # it anyway.
        assert (
            refusal_for(NET_OF_INTEREST, fact.anchor, (fact.anchor,), {}) is not None
        ), symbol

    # Three of the eleven carry the word `net`, which is the control that
    # matters: the concept is not reachable by wording.
    assert sorted(s for s, label in labels.items() if "net" in label.casefold()) == [
        "AAPL",
        "HON",
        "PG",
    ]


def test_the_parent_company_total_income_specimen_does_not_qualify() -> None:
    """M&T's `Total income` 2,916, refused on the evidence rather than a boundary.

    BQ19 refused `total income` as a `TOTAL_REVENUE` form because M&T
    prints it over `Dividends from consolidated subsidiaries` in a table
    captioned *Condensed Statement of Income* — and said in the same breath
    that only the concept-to-statement partition kept the two apart, "a
    boundary rather than a property of the label".

    The structural gate makes it a property of the evidence. Measured in
    M&T's own filing: that table prints no net interest income above the
    line, so a candidate there is refused whatever section it sits in.
    """

    parent = ReportedFigure(
        label="Total income",
        column_header="2025",
        printed="2,916",
        value=2916.0,
        cell=CellReference(table=73, row=7, column=3),
        caption="Condensed Statement of Income",
    )

    # The label *is* an accepted form — which is the whole point.
    assert matches_concept(NET_OF_INTEREST, parent.label)

    refusal = refusal_for(NET_OF_INTEREST, parent, (parent,), {})

    assert refusal is not None
    assert refusal.standing is RefusalStanding.FINANCING_COST_NOT_EVIDENCED
    assert "no net interest income" in refusal.standing.value

    # And a net interest income established elsewhere in the filing must
    # not rescue it. One table is one scale, and the consolidated
    # statement's subtotal is no evidence about a parent-company table.
    elsewhere = ReportedFigure(
        label="Net interest income",
        column_header="2025",
        printed="6,948",
        value=6948.0,
        cell=CellReference(table=0, row=14, column=3),
        caption="(in millions)",
    )

    assert refusal_for(NET_OF_INTEREST, parent, (parent,), {NII: elsewhere}) is not None


def test_a_component_of_the_total_cannot_pass_as_the_total() -> None:
    """A non-interest subtotal sits *above* the marker, not below it."""

    component = ReportedFigure(
        label="Total net revenues",
        column_header="2025",
        printed="44,724",
        value=44724.0,
        cell=CellReference(table=0, row=8, column=3),
        caption="(in millions)",
    )

    marker = marker_of("GS")

    assert marker.cell.row > component.cell.row

    assert (
        refusal_for(NET_OF_INTEREST, component, (component,), {NII: marker}) is not None
    )


# ── BQ23 is untouched ────────────────────────────────────────────────


def test_bq23_still_refuses_all_three_as_total_revenue() -> None:
    """A new concept for the quantity is not a licence for the old one."""

    for symbol in ("GS", "JPM"):
        fact = held(symbol).fact(REVENUE)

        assert fact is not None
        assert not fact.is_located, symbol
        assert fact.refused is not None
        assert fact.refused.standing is RefusalStanding.NET_OF_FINANCING_COST

    # AXP was refused by vocabulary and still is.
    axp = held("AXP").fact(REVENUE)

    assert axp is not None and not axp.is_located
    assert axp.refused is None
    assert axp.agreement.answers[0].stated == "no figure located"


def test_the_two_concepts_are_not_aliases() -> None:
    """Distinct members, distinct vocabularies, distinct fingerprints."""

    assert NET_OF_INTEREST is not REVENUE
    assert CONCEPT_LABELS[NET_OF_INTEREST] != CONCEPT_LABELS[REVENUE]
    assert concept_vocabulary_fingerprint(NET_OF_INTEREST) != (
        concept_vocabulary_fingerprint(REVENUE)
    )

    # Two forms are shared, and sharing a form is not being an alias: the
    # structural requirement is opposite for the two concepts, so one row
    # can satisfy only one of them.
    shared = set(CONCEPT_LABELS[NET_OF_INTEREST]) & set(CONCEPT_LABELS[REVENUE])

    assert shared == {"total net revenue", "total net revenues"}


# ── provenance: prospective only ─────────────────────────────────────


def _symbols() -> list[str]:
    return sorted(
        {path.name.split(".")[0] for path in pathlib.Path(PRODUCTION).glob("*.json")}
    )


def test_the_new_concept_is_pinned_and_no_other_vocabulary_moved() -> None:
    """Every other fingerprint is exactly what BQ23 left it."""

    assert concept_vocabulary_fingerprint(NET_OF_INTEREST) == FINGERPRINT

    unchanged = {
        REVENUE: "ea9df9c5adbc7f44",
        StatementConcept.GROSS_PROFIT: "36b11e47cf234c1f",
        StatementConcept.OPERATING_INCOME: "668db132db8b57bd",
        StatementConcept.NET_INCOME: "c5983f89b332a0c7",
        NII: "8c3e67f9872329b5",
        StatementConcept.PREMIUM_REVENUE: "87e065f39c345a37",
    }

    for concept, fingerprint in unchanged.items():
        assert concept_vocabulary_fingerprint(concept) == fingerprint, concept


def test_the_concept_appears_only_where_it_was_natively_asked() -> None:
    """No backfill: a reading carries what it was asked, and nothing more.

    Until BQ28's phase-0 append this asserted the concept appeared nowhere
    in production. The appended natives carry it — they were asked it, and
    stamp it — and the invariant that survives the append is the real one:
    every stored observation that holds a fact for the concept also holds
    a native `produced_under` stamp for it, and no observation without the
    stamp gained the fact. `_addressed` reads the concepts from the
    observations rather than from the live vocabulary, "because a stored
    reading may predate a concept the vocabulary gained since".
    """

    store = JsonFinancialStatementStore(PRODUCTION)
    service = FinancialStatementService(store)

    holders = []

    for symbol in _symbols():
        for statement, consensus in service.established(symbol).items():
            assert statement is not None

            for observation in store.read(
                symbol, consensus.source.key, consensus.statement
            ):
                asked = NET_OF_INTEREST in {fact.concept for fact in observation.facts}
                stamped = observation.produced_contract_for(NET_OF_INTEREST) is not None

                assert asked == stamped, symbol

                if asked:
                    holders.append(symbol)

    # Exactly the three filers the ruling appended, five readings each.
    from collections import Counter

    assert Counter(holders) == {"GS": 5, "JPM": 5, "AXP": 5}


def test_the_concept_needs_no_registry_entry_and_stays_safe_without_one() -> None:
    """An unlisted lineage refuses to reason, which is the safe direction."""

    from app.domain.vocabulary_contracts import registry_is_current

    # `TOTAL_REVENUE` keeps its lineage, so absence supersession keeps
    # working exactly as BQ20 built it.
    assert registry_is_current(REVENUE)

    # The new concept has none, so its absences are never superseded.
    assert not registry_is_current(NET_OF_INTEREST)


def test_a_new_reading_pools_with_an_old_one_for_every_shared_concept() -> None:
    """No schema bump: the transport question has the same answer as before.

    The schema version exists to stop two readings pooling when one was
    shown, asked or interpreted differently. Adding a concept changes none
    of that for any concept either reading carries — proved by deriving a
    consensus over one observation that knows the concept and one that does
    not, and requiring every shared claim to be identical to the old-only
    consensus.
    """

    import dataclasses
    from datetime import UTC, datetime

    from app.domain.financial_statement_consensus import statement_consensus_of
    from app.domain.financial_statements import (
        FinancialStatementObservation,
        StatementFact,
    )
    from app.domain.provenance import Provenance
    from tests.test_financial_statement_store import source

    top = ReportedFigure(
        label="Total revenues",
        column_header="2025",
        printed="1,000",
        value=1000.0,
        cell=CellReference(table=0, row=4, column=3),
        caption="(in millions)",
    )

    def reading(*concepts: StatementConcept) -> FinancialStatementObservation:
        return FinancialStatementObservation(
            symbol="EXA",
            statement=INCOME,
            facts=tuple(
                StatementFact(
                    concept=concept,
                    anchor=top if concept is REVENUE else None,
                    row=(top,) if concept is REVENUE else (),
                    unlocated_because=None if concept is REVENUE else "not located",
                )
                for concept in concepts
            ),
            source=source(),
            reading=Provenance(
                source="reader", observed_at=datetime(2026, 8, 17, tzinfo=UTC)
            ),
        )

    old = tuple(reading(REVENUE, StatementConcept.NET_INCOME) for _ in range(5))
    new = tuple(
        reading(REVENUE, StatementConcept.NET_INCOME, NET_OF_INTEREST) for _ in range(5)
    )

    old_only = statement_consensus_of(old)
    mixed = statement_consensus_of(old + new)

    for concept in (REVENUE, StatementConcept.NET_INCOME):
        before = old_only.fact(concept)
        after = mixed.fact(concept)

        assert before is not None and after is not None

        # The settled claim is identical. The counts are not, and must not
        # be: ten readings answered rather than five, which is more
        # evidence for the same claim and exactly what pooling means.
        assert (before.anchor, before.row) == (after.anchor, after.row), concept
        assert before.refused == after.refused, concept
        assert before.is_located == after.is_located, concept

        assert before.agreement.modal is not None
        assert after.agreement.modal is not None
        assert before.agreement.modal.stated == after.agreement.modal.stated, concept
        assert (before.agreement.readings, after.agreement.readings) == (5, 10)

    del dataclasses

    # And the new concept appears only because half the readings were asked.
    assert mixed.fact(NET_OF_INTEREST) is not None
    assert old_only.fact(NET_OF_INTEREST) is None


# ── consumed by nothing ──────────────────────────────────────────────


def test_the_concept_reaches_no_measure_no_factor_and_no_band() -> None:
    """Named and acquirable, and analytically inert — by construction.

    A correctly named fact is not automatically a correctly comparable
    quality factor. This is the guard that keeps the two apart until a
    slice earns the second.
    """

    import ast

    from app.services.financial_engine import RECIPES

    for measure, recipe in RECIPES.items():
        assert NET_OF_INTEREST not in recipe.concepts, measure

    # Nothing in the decision, quality or analyst layers mentions it.
    for module in (
        "app/domain/business_quality.py",
        "app/domain/financial_question.py",
        "app/domain/financial_understanding.py",
        "app/services/financial_questions.py",
        "app/services/business_quality_service.py",
        "app/analysts/profitability_analyst.py",
    ):
        text = pathlib.Path(module).read_text()

        assert NET_OF_INTEREST.value not in text, module
        assert "REVENUE_NET_OF_INTEREST_EXPENSE" not in text, module

    # And no module anywhere computes the sum this concept names, which is
    # the other thing a bank profitability factor would need.
    for path in pathlib.Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text())

        for node in ast.walk(tree):
            if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Add):
                continue

            rendered = ast.unparse(node)

            assert "net_interest" not in rendered, f"{path}: {rendered}"


def test_the_production_bands_are_exactly_what_bq23_left() -> None:
    """Acquiring a name changes no assessment. The corpus proves it."""

    import collections

    from app.services.business_quality_service import quality_of
    from app.services.financial_engine import measure

    store = JsonFinancialStatementStore(PRODUCTION)
    service = FinancialStatementService(store)

    tally: collections.Counter[str] = collections.Counter()

    for symbol in _symbols():
        statements = service.established(symbol)

        if not statements:
            tally["UNKNOWN"] += 1
            continue

        try:
            understanding = measure(symbol, statements)
        except ValueError:
            tally["UNKNOWN"] += 1
            continue

        quality = quality_of(symbol, understanding)
        tally[quality.band.value if quality is not None else "UNKNOWN"] += 1

    assert dict(tally) == {"HIGH": 3, "MEDIUM": 4, "LOW": 3, "UNKNOWN": 14}
