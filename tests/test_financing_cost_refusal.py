"""A located figure refused the concept the statement's structure disproves.

The mandatory specimens and the controls that keep the rule from decaying
into *if the label says net* or *if the company is a bank*. Both failure
modes are pinned by construction rather than by convention: the positive
controls carry `net` in the label and are not refused, and the negative
specimens carry no such word and are.
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

from app.domain.financial_statement_consensus import statement_consensus_of
from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.financing_cost_refusal import (
    GOVERNED,
    RefusalStanding,
    precedes_in_one_column,
    refusal_for,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.financial_statement_service import FinancialStatementService
from tests.test_financial_statement_store import source


def _code_of(path: str, *, only: str | None = None) -> str:
    """The module's executable source, every docstring removed.

    Written with `ast` rather than a string split because the prose in
    this rule cites the filings that earned it — as it should — and a
    scan that could not tell prose from code would either fail on the
    citation or pass on a company name in a branch.

    `only` narrows to one function, which is what lets a scan distinguish
    *deciding* from *wording*: the rule may quote a filer's row label in
    the sentence it produces, and may never read one to reach a verdict.
    """

    import ast

    tree: ast.AST = ast.parse(pathlib.Path(path).read_text())

    for node in ast.walk(tree):
        if not isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            continue

        body = node.body

        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node.body = body[1:] or [ast.Pass()]

    if only is not None:
        found = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == only
        ]

        assert found, f"{only} is not defined in {path}"

        tree = found[0]

    return ast.unparse(tree)


INCOME = StatementKind.INCOME_STATEMENT
REVENUE = StatementConcept.TOTAL_REVENUE
NET_OF_INTEREST = StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE
NII = StatementConcept.NET_INTEREST_INCOME
EARNINGS = StatementConcept.NET_INCOME

#: The live corpus, read through the ordinary door. These tests are the
#: acceptance evidence for the ruling, so they read the same store every
#: surface reads.
PRODUCTION = "data/statements"


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


def reading(
    *figures: tuple[StatementConcept, ReportedFigure],
) -> FinancialStatementObservation:
    """One reading that located each concept at the cell given."""

    return FinancialStatementObservation(
        symbol="EXA",
        statement=INCOME,
        facts=tuple(
            StatementFact(concept=concept, anchor=anchor, row=(anchor,))
            for concept, anchor in figures
        ),
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 17, tzinfo=UTC)
        ),
    )


def consensus_of(*figures: tuple[StatementConcept, ReportedFigure]):
    return statement_consensus_of(tuple(reading(*figures) for _ in range(5)))


def held(symbol: str):
    """One company's income-statement consensus, from the live store."""

    return FinancialStatementService(
        JsonFinancialStatementStore(PRODUCTION)
    ).established(symbol)[INCOME]


# ── the rule reads structure, and only structure ─────────────────────


def test_the_rule_governs_one_predicate_read_both_ways_and_names_no_company() -> None:
    """Two concepts, one marker, opposite polarity — and no company list.

    The pair is the design: the same net interest subtotal that disproves
    a gross top line is what establishes a net-of-financing one, so a
    statement can support neither reading twice nor both at once.
    """

    from app.domain.financing_cost_refusal import Requirement

    assert GOVERNED == {
        REVENUE: (NII, Requirement.ABSENT_ABOVE),
        NET_OF_INTEREST: (NII, Requirement.PRESENT_ABOVE),
    }

    module = "app/domain/financing_cost_refusal.py"

    # No company may be named in the rule. Docstrings are stripped, so the
    # prose that cites the filings which earned it is not searched.
    #
    # Word boundaries, not containment: a substring scan reported `GS`
    # inside the identifier `STANDINGS`, which is the same false-positive
    # shape that once let a ticker corroborate itself on the letters
    # *etf*. A ticker is a word or it is not a ticker.
    import re

    code = _code_of(module)

    for name in ("GS", "JPM", "AXP", "Goldman", "JPMorgan", "American Express"):
        assert not re.search(rf"\b{re.escape(name)}\b", code), name

    # No text comparison of any kind, anywhere in the module.
    for word in ("casefold", "lower()", "startswith", "endswith", "match"):
        assert word not in code, word

    # And the two functions that *decide* never read a row label at all.
    # `_because` does, because it words the refusal — which is the
    # distinction this scan exists to hold: quoting a label is not reading
    # one.
    for deciding in ("refusal_for", "precedes_in_one_column"):
        body = _code_of(module, only=deciding)

        assert "label" not in body, deciding
        assert "printed" not in body, deciding

    assert "label" in _code_of(module, only="_because")


def test_a_marker_below_the_total_disproves_nothing() -> None:
    """Order is the rule. An interest subtotal beneath a top line is a cost."""

    total = figure("Total revenues", "100", 100.0, row=4)
    marker = figure("Net interest income", "10", 10.0, row=17)

    assert not precedes_in_one_column(marker, total)
    assert refusal_for(REVENUE, total, (total,), {NII: marker}) is None


def test_a_marker_in_another_table_or_column_disproves_nothing() -> None:
    """`comparable`'s discipline: one table is one scale, one column one period."""

    total = figure("Total revenues", "100", 100.0, row=9)

    other_table = figure("Net interest income", "10", 10.0, row=2, table=1)
    other_column = figure("Net interest income", "10", 10.0, row=2, column=9)

    assert refusal_for(REVENUE, total, (total,), {NII: other_table}) is None
    assert refusal_for(REVENUE, total, (total,), {NII: other_column}) is None


def test_no_marker_at_all_leaves_the_total_alone() -> None:
    """The state eleven of thirteen live top lines are in."""

    total = figure("Total revenues", "100", 100.0, row=9)

    assert refusal_for(REVENUE, total, (total,), {}) is None


def test_only_the_governed_concept_can_be_refused() -> None:
    """Net income sits below net interest income on every bank statement."""

    marker = figure("Net interest income", "10", 10.0, row=11)
    bottom = figure("Net income", "5", 5.0, row=27)

    assert refusal_for(EARNINGS, bottom, (bottom,), {NII: marker}) is None


def test_the_disproving_concept_is_never_itself_refused() -> None:
    """Otherwise a statement could argue itself out of its own marker."""

    marker = figure("Net interest income", "10", 10.0, row=11)

    assert refusal_for(NII, marker, (marker,), {NII: marker}) is None


# ── mandatory specimen: GS ───────────────────────────────────────────


def test_goldman_total_net_revenues_is_refused() -> None:
    """`Total net revenues` 58,283 = 44,724 + 13,559, and it is not revenue.

    The reconciliation is stated here because it is the reason the rule
    exists, and checked from the filer's own printed subtotals: the two
    figures the statement prints above the total add to it exactly.
    """

    income = held("GS")
    fact = income.fact(REVENUE)

    assert fact is not None
    assert fact.agreement.by_majority
    assert fact.agreement.readings == 5

    # The concept is unanswered...
    assert not fact.is_located
    assert fact.anchor is None

    # ...and the figure is still here, with the reason.
    assert fact.refused is not None
    assert fact.refused.standing is RefusalStanding.NET_OF_FINANCING_COST
    assert fact.refused.figure.label == "Total net revenues"
    assert fact.refused.figure.value == 58283.0
    assert fact.refused.disproved_by.label == "Net interest income"
    assert fact.refused.disproved_by.value == 13559.0

    # The reconciliation, from the statement's own subtotals.
    assert 44724.0 + fact.refused.disproved_by.value == fact.refused.figure.value


def test_goldman_keeps_every_other_fact() -> None:
    """The refusal is concept-local, exactly as supersession is."""

    income = held("GS")

    earnings = income.fact(EARNINGS)
    interest = income.fact(NII)

    assert earnings is not None and earnings.is_located
    assert earnings.anchor is not None and earnings.anchor.value == 17176.0
    assert earnings.refused is None

    assert interest is not None and interest.is_located
    assert interest.refused is None


# ── mandatory specimen: JPM ──────────────────────────────────────────


def test_jpmorgan_total_net_revenue_is_refused() -> None:
    """`Total net revenue` 182,447 = 87,004 + 95,443, same construction."""

    income = held("JPM")
    fact = income.fact(REVENUE)

    assert fact is not None
    assert not fact.is_located
    assert fact.refused is not None
    assert fact.refused.standing is RefusalStanding.NET_OF_FINANCING_COST
    assert fact.refused.figure.label == "Total net revenue"
    assert fact.refused.figure.value == 182447.0
    assert fact.refused.disproved_by.value == 95443.0

    assert 87004.0 + fact.refused.disproved_by.value == fact.refused.figure.value


# ── mandatory specimen: AXP, and it must not move ────────────────────


def test_american_express_stays_a_settled_absence() -> None:
    """The same construction, refused already, and refused the same way.

    AXP holds five readings that answer *no figure located* — its label
    was never in the vocabulary — and the new rule must not turn that
    settled absence into something else. It is the consistency check the
    ruling rests on: one economic quantity, one outcome, whichever route
    reaches it.
    """

    income = held("AXP")
    fact = income.fact(REVENUE)

    assert fact is not None
    assert not fact.is_located
    assert fact.agreement.by_majority
    assert fact.agreement.answers[0].stated == "no figure located"

    # Refused by vocabulary rather than by structure: there is no located
    # figure for the structural rule to refuse.
    assert fact.refused is None

    # And its net interest income — the marker that would have refused a
    # located total — is established, at the same 5 of 5.
    interest = income.fact(NII)

    assert interest is not None and interest.is_located
    assert interest.anchor is not None and interest.anchor.value == 17364.0


# ── mandatory negative controls, from the live corpus ────────────────


def test_the_eleven_gross_top_lines_are_untouched() -> None:
    """Every class-A occurrence keeps its concept, and three say `net`.

    The three are the control that matters: `Total net sales`,
    `Net sales` and `NET SALES` are net of returns and allowances, which
    is a revenue adjustment rather than an expense line — so a rule that
    read the word would refuse them and this one does not.
    """

    expected = {
        "AAPL": "Total net sales",
        "ALL": "Total revenues",
        "CB": "Total revenues",
        "DIS": "Total revenues",
        "HON": "Net sales",
        "MET": "Total revenues",
        "PG": "NET SALES",
        "TRV": "Total revenues",
        "TSLA": "Total revenues",
        "UNP": "Total operating revenues",
        "WMT": "Total revenues",
    }

    for symbol, label in expected.items():
        fact = held(symbol).fact(REVENUE)

        assert fact is not None, symbol
        assert fact.is_located, symbol
        assert fact.refused is None, symbol
        assert fact.anchor is not None and fact.anchor.label == label, symbol

    # Three of the eleven carry the word, and none is refused.
    said_net = [
        symbol for symbol, label in expected.items() if "net" in label.casefold()
    ]

    assert sorted(said_net) == ["AAPL", "HON", "PG"]


def test_union_pacific_is_named_because_it_is_the_nearest_miss() -> None:
    """`Total operating revenues`, earned by BQ19, and it must stay earned."""

    fact = held("UNP").fact(REVENUE)

    assert fact is not None
    assert fact.is_located
    assert fact.refused is None
    assert fact.anchor is not None and fact.anchor.value == 24510.0

    # And UNP prints interest expense *below* its top line, which is the
    # ordinary industrial shape the rule must not read as a bank's.
    assert held("UNP").fact(NII) is None or not held("UNP").fact(NII).is_located


def test_a_marker_present_but_structurally_apart_does_not_refuse() -> None:
    """The control the live corpus cannot supply, constructed.

    No company in the corpus prints a net interest income subtotal *and*
    a gross top line above it, so the case is built: the same two
    concepts, the marker below the total. It must not refuse — otherwise
    the rule is *financial statements are refused* wearing a structural
    disguise.
    """

    total = figure("Total revenues", "1,000", 1000.0, row=4)
    marker = figure("Net interest income", "120", 120.0, row=18)

    consensus = consensus_of((REVENUE, total), (NII, marker))
    fact = consensus.fact(REVENUE)

    assert fact is not None
    assert fact.is_located
    assert fact.refused is None


def test_the_same_two_concepts_the_other_way_round_do_refuse() -> None:
    """The paired positive, so the control above proves the order matters."""

    marker = figure("Net interest income", "120", 120.0, row=4)
    total = figure("Total revenues", "1,000", 1000.0, row=18)

    fact = consensus_of((REVENUE, total), (NII, marker)).fact(REVENUE)

    assert fact is not None
    assert not fact.is_located
    assert fact.refused is not None

    # And the label carried no `net` at all, which is the other half of
    # the same proof.
    assert "net" not in fact.refused.figure.label.casefold()


# ── the refusal is not an absence, anywhere it is read ───────────────


def test_a_refusal_never_words_itself_as_the_filer_printing_nothing() -> None:
    """The claim would be false: Goldman prints the line and the figure."""

    fact = held("GS").fact(REVENUE)

    assert fact is not None
    assert fact.unlocated_because is None

    because = fact.absent_because

    assert because is not None
    assert "no figure located" not in because.casefold()
    assert "located no cell" not in because.casefold()
    assert "The filer did print it" in because


def test_the_reason_reaches_the_measure_that_needed_the_figure() -> None:
    """A margin says why it has no denominator, in the rule's own words."""

    from app.domain.financial_understanding import FinancialMeasure
    from app.services.financial_engine import measure

    understanding = measure(
        "GS",
        FinancialStatementService(JsonFinancialStatementStore(PRODUCTION)).established(
            "GS"
        ),
    )

    net_margin = understanding.of(FinancialMeasure.NET_MARGIN)

    assert net_margin is not None
    assert net_margin.value is None
    assert net_margin.absent_because is not None
    assert "total after financing cost" in net_margin.absent_because


def test_the_consensus_reports_what_it_declined() -> None:
    """Beside the located facts, never subtracted from them."""

    income = held("GS")

    refused = income.refused_facts

    assert [fact.concept for fact in refused] == [REVENUE]
    assert REVENUE not in [fact.concept for fact in income.located_facts]

    caveat = income.refusal_caveat()

    assert caveat is not None and "total_revenue" in caveat

    # And a statement with nothing refused says nothing.
    assert held("AAPL").refusal_caveat() is None
    assert held("AAPL").refused_facts == ()


# ── the observations are untouched ───────────────────────────────────


def test_the_readings_are_byte_identical_after_the_derivation() -> None:
    """Derived on read. Nothing is rewritten, nothing is deleted."""

    store = JsonFinancialStatementStore(PRODUCTION)

    before = store.read("GS", "0000886982-26-000091", INCOME)

    statement_consensus_of(before)

    after = store.read("GS", "0000886982-26-000091", INCOME)

    assert before == after

    # The store now holds both generations — five pre-BQ17 positives and
    # five stamped natives, since BQ28's phase-0 append — and neither was
    # rewritten. The old five still say they located the figure and still
    # carry no provenance; the natives still carry theirs.
    old = [observation for observation in after if observation.produced_under == ()]
    native = [observation for observation in after if observation.produced_under != ()]

    assert len(old) == 5 and len(native) == 5

    for observation in old:
        fact = observation.fact(REVENUE)

        assert fact is not None
        assert fact.anchor is not None
        assert fact.anchor.label == "Total net revenues"
        assert observation.produced_contract_for(REVENUE) is None

    for observation in native:
        assert observation.produced_contract_for(REVENUE) == "ea9df9c5adbc7f44"


def test_no_vocabulary_moved_and_no_fingerprint_with_it() -> None:
    """The rule is downstream of extraction, so the contract cannot have moved.

    Pinned rather than described: a slice that widened or narrowed
    `CONCEPT_LABELS` would change this fingerprint, and BQ20's registry
    would then have to be extended in the same commit. Neither happened,
    and this is what says so.
    """

    from app.domain.financial_statements import (
        CONCEPT_LABELS,
        concept_vocabulary_fingerprint,
    )
    from app.domain.vocabulary_contracts import PUBLISHED, registry_is_current

    assert concept_vocabulary_fingerprint(REVENUE) == "ea9df9c5adbc7f44"
    assert len(CONCEPT_LABELS[REVENUE]) == 14

    # Both accepted forms are still accepted *as vocabulary*. The rule
    # refuses a figure, never a label — which is why the words survive.
    assert "total net revenue" in CONCEPT_LABELS[REVENUE]
    assert "total net revenues" in CONCEPT_LABELS[REVENUE]

    # And the published lineage still covers the live vocabulary, so
    # absence supersession keeps working.
    assert registry_is_current(REVENUE)
    assert PUBLISHED[-1].fingerprint == "ea9df9c5adbc7f44"


# ── the regression control: Barclays and NatWest ─────────────────────


def test_the_next_two_candidates_would_be_refused_on_the_same_ground() -> None:
    """`Total income` at Barclays and NatWest, simulated, never promoted.

    BQ19 refused `total income` for a parent-company collision at M&T —
    a reason about the label. This is the independent semantic ground:
    both filers print their own net interest income above the line, so
    were the label ever accepted, the figure would still not be a gross
    top line.

    Each company's marker is its **own established** net interest income,
    read from the store. Only the total's position is supplied, at the row
    BQ22 measured, because no located figure exists to read it from — the
    label is refused, which is the whole point of simulating it.
    """

    measured_total_row = {"BCS": 12, "NWG": 11}

    for symbol, total_row in measured_total_row.items():
        income = held(symbol)

        marker_fact = income.fact(NII)
        revenue_fact = income.fact(REVENUE)

        assert marker_fact is not None and marker_fact.anchor is not None
        marker = marker_fact.anchor

        # Today: no located top line at all, so nothing to refuse.
        assert revenue_fact is not None and not revenue_fact.is_located
        assert revenue_fact.refused is None

        # The marker precedes the row the filer prints `Total income` on.
        assert marker.cell.row < total_row

        proposed = figure(
            "Total income",
            "29,140",
            29140.0,
            row=total_row,
            table=marker.cell.table,
            column=marker.cell.column,
            header=marker.column_header,
        )

        refusal = refusal_for(REVENUE, proposed, (proposed,), {NII: marker})

        assert refusal is not None, symbol
        assert refusal.standing is RefusalStanding.NET_OF_FINANCING_COST
        assert refusal.disproved_by is marker


# ── the production baseline, derived rather than pinned ──────────────


def test_only_the_refused_companies_lost_their_revenue_dependent_factors() -> None:
    """The whole corpus, and the movement traced to its cause.

    Nothing here asserts an aggregate. It asserts the relation: a company
    carries a refusal exactly where the structural predicate holds, and a
    refusal removes exactly the factors that need a top line — leaving
    earnings growth, which needs none.
    """

    from app.domain.business_quality import QualityBand
    from app.domain.financial_question import FinancialQuestionKey
    from app.infrastructure.evidence_root import evidence_path
    from app.services.business_quality_service import quality_of
    from app.services.financial_engine import measure

    del evidence_path  # the declared store below is the evidence set

    store = JsonFinancialStatementStore(PRODUCTION)
    service = FinancialStatementService(store)

    symbols = sorted(
        {path.name.split(".")[0] for path in pathlib.Path(PRODUCTION).glob("*.json")}
    )

    refused_companies = []

    for symbol in symbols:
        held_statements = service.established(symbol)
        income = held_statements.get(INCOME)

        if income is None:
            continue

        fact = income.fact(REVENUE)

        if fact is None or fact.refused is None:
            continue

        refused_companies.append(symbol)

        # The two revenue-dependent factors are gone, and gone with the
        # rule's own reason rather than with a silence.
        understanding = measure(symbol, held_statements)
        quality = quality_of(symbol, understanding)

        assert quality is not None

        by_key = {factor.question: factor for factor in quality.factors}

        for key in (
            FinancialQuestionKey.PROFITABILITY,
            FinancialQuestionKey.REVENUE_GROWTH,
        ):
            factor = by_key[key]

            assert not factor.is_answered, (symbol, key)

            # The refusal is named among the factor's gaps — one per
            # measure the question consults. `because` quotes the first
            # of them, which for profitability is the gross profit this
            # filer prints no line for; that ordering predates this
            # slice and is not what it rules on.
            assert any("total after financing cost" in gap for gap in factor.gaps), (
                symbol,
                key,
            )

        # Revenue growth consults one measure, so its own sentence is the
        # refusal.
        growth = by_key[FinancialQuestionKey.REVENUE_GROWTH]

        assert growth.because is not None
        assert "total after financing cost" in growth.because, symbol

        # Earnings growth needs no top line, so it survives untouched.
        earnings = by_key[FinancialQuestionKey.EARNINGS_GROWTH]

        assert earnings.is_answered, symbol

        # One answered factor never bands, and that is the completeness
        # rule rather than anything this slice decided.
        assert quality.answered == 1
        assert quality.band is QualityBand.UNKNOWN
        assert quality.score is None

    # Exactly the companies the structural predicate identifies, and the
    # list is derived from the corpus rather than written down.
    structurally = [
        symbol
        for symbol in symbols
        if (income := service.established(symbol).get(INCOME)) is not None
        and (marker := income.fact(NII)) is not None
        and marker.is_located
        and (revenue := income.fact(REVENUE)) is not None
        and revenue.refused is not None
    ]

    assert refused_companies == structurally
    assert refused_companies, "the corpus must contain at least one specimen"


def test_every_other_company_keeps_the_band_it_had() -> None:
    """No company without a refusal may move, which is the blast radius.

    Derived by running the assessment twice: once as production does, and
    once over a consensus with the refusal reversed by hand. Only the
    companies carrying a refusal may differ.
    """

    from dataclasses import replace as replace_fact

    from app.services.business_quality_service import quality_of
    from app.services.financial_engine import measure

    store = JsonFinancialStatementStore(PRODUCTION)
    service = FinancialStatementService(store)

    symbols = sorted(
        {path.name.split(".")[0] for path in pathlib.Path(PRODUCTION).glob("*.json")}
    )

    def band_of(symbol: str, held_statements: dict) -> str:
        try:
            understanding = measure(symbol, held_statements)
        except ValueError:
            return "UNKNOWN"

        quality = quality_of(symbol, understanding)

        return quality.band.value if quality is not None else "UNKNOWN"

    moved = []

    for symbol in symbols:
        statements = service.established(symbol)

        if not statements:
            continue

        income = statements.get(INCOME)
        restored = dict(statements)

        if income is not None:
            undone = tuple(
                replace_fact(
                    fact,
                    anchor=fact.refused.figure,
                    row=fact.refused.row,
                    refused=None,
                )
                if fact.refused is not None
                else fact
                for fact in income.facts
            )
            restored[INCOME] = replace_fact(income, facts=undone)

        if band_of(symbol, statements) != band_of(symbol, restored):
            moved.append(symbol)

    refused = [
        symbol
        for symbol in symbols
        if (income := service.established(symbol).get(INCOME)) is not None
        and any(fact.refused is not None for fact in income.facts)
    ]

    assert moved == refused
