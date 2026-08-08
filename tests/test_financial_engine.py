"""What the statements measure, derived from consensus by arithmetic alone."""

from datetime import UTC, date, datetime

import pytest

from app.domain.agreement import agreement
from app.domain.financial_statement_consensus import (
    ConsensusFact,
    FinancialStatementConsensus,
)
from app.domain.financial_statements import StatementConcept, StatementKind
from app.domain.financial_understanding import FinancialMeasure, MeasureUnit
from app.domain.knowledge_consensus import ConsensusState
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceType,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.services.financial_engine import measure

ACCESSION = "0000019617-26-000100"


def source(key: str = ACCESSION) -> PrimarySource:
    return PrimarySource(
        symbol="JPM",
        company="Example Bank",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
        published_on=date(2026, 2, 13),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{key}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


def figure(
    label: str,
    value: float,
    *,
    printed: str | None = None,
    header: str = "2025",
    table: int = 0,
    row: int = 1,
    column: int = 1,
) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header=header,
        printed=printed or f"{value:,.0f}",
        value=value,
        cell=CellReference(table=table, row=row, column=column),
        caption="(in millions)",
    )


def fact(
    concept: StatementConcept,
    anchor: ReportedFigure | None,
    *,
    row: tuple[ReportedFigure, ...] = (),
    agreeing: int = 5,
    readings: int = 5,
    because: str | None = None,
) -> ConsensusFact:
    answers = ["found"] * agreeing + [f"other {n}" for n in range(readings - agreeing)]

    return ConsensusFact(
        concept=concept,
        addressed_in=readings,
        observations=readings,
        anchor=anchor,
        row=row or ((anchor,) if anchor else ()),
        unlocated_because=because,
        agreement=agreement("where the statement prints it", answers),
    )


def consensus(
    statement: StatementKind,
    facts: tuple[ConsensusFact, ...],
    *,
    key: str = ACCESSION,
    count: int = 5,
    quorum: int = 5,
) -> FinancialStatementConsensus:
    return FinancialStatementConsensus(
        symbol="JPM",
        statement=statement,
        source=source(key),
        observation_count=count,
        quorum=quorum,
        state=(
            ConsensusState.QUORATE
            if count >= quorum
            else ConsensusState.INSUFFICIENT_QUORUM
        ),
        facts=facts,
        reading=Provenance(
            source="a reader — consensus of statement readings",
            observed_at=datetime(2026, 2, 14, tzinfo=UTC),
        ),
    )


def income(**overrides: object) -> FinancialStatementConsensus:
    revenue = figure("Total net revenue", 182447.0, row=1)
    prior = figure("Total net revenue", 177556.0, header="2024", row=1, column=2)
    income_figure = figure("Net income", 57048.0, row=4)

    return consensus(
        StatementKind.INCOME_STATEMENT,
        (
            fact(StatementConcept.TOTAL_REVENUE, revenue, row=(revenue, prior)),
            fact(StatementConcept.GROSS_PROFIT, None, because="No such line."),
            fact(StatementConcept.OPERATING_INCOME, None, because="No such line."),
            fact(StatementConcept.NET_INCOME, income_figure),
        ),
        **overrides,  # type: ignore[arg-type]
    )


def balance_sheet() -> FinancialStatementConsensus:
    return consensus(
        StatementKind.BALANCE_SHEET,
        (
            fact(
                StatementConcept.TOTAL_CURRENT_ASSETS,
                figure("Total current assets", 143566.0, table=1, row=1),
            ),
            fact(
                StatementConcept.TOTAL_CURRENT_LIABILITIES,
                figure("Total current liabilities", 137207.0, table=1, row=2),
            ),
            fact(
                StatementConcept.TOTAL_LIABILITIES,
                figure("Total liabilities", 3900000.0, table=1, row=3),
                agreeing=3,
            ),
            fact(
                StatementConcept.TOTAL_EQUITY,
                figure("Total stockholders' equity", 350000.0, table=1, row=4),
            ),
        ),
    )


def cash_flow() -> FinancialStatementConsensus:
    return consensus(
        StatementKind.CASH_FLOW_STATEMENT,
        (
            fact(
                StatementConcept.OPERATING_CASH_FLOW,
                figure(
                    "Net cash provided by operating activities",
                    100000.0,
                    table=2,
                    row=1,
                ),
            ),
            fact(
                StatementConcept.CAPITAL_EXPENDITURES,
                figure(
                    "Purchases of property and equipment",
                    -12000.0,
                    printed="(12,000)",
                    table=2,
                    row=2,
                ),
            ),
        ),
    )


# ── what it computes ─────────────────────────────────────────────────


def test_every_measure_is_present_established_or_absent_with_a_reason() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    assert len(understanding.measures) == len(FinancialMeasure)

    for established in understanding.measures:
        assert established.is_established or established.absent_because


def test_a_margin_is_two_checked_cells_divided_by_this_platform() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    net_margin = understanding.of(FinancialMeasure.NET_MARGIN)

    assert net_margin is not None
    assert net_margin.value == pytest.approx(0.3127, abs=1e-4)
    assert net_margin.unit is MeasureUnit.FRACTION
    assert len(net_margin.basis) == 2
    assert '"Net income" 57,048 over "Total net revenue" 182,447' in net_margin.stated


def test_growth_costs_no_reading_because_the_row_was_already_read() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    growth = understanding.of(FinancialMeasure.REVENUE_GROWTH)

    assert growth is not None
    assert growth.value == pytest.approx(0.02754, abs=1e-5)
    assert '"2024"' in growth.stated


def test_free_cash_flow_subtracts_what_the_company_spent() -> None:
    understanding = measure("JPM", {StatementKind.CASH_FLOW_STATEMENT: cash_flow()})

    free = understanding.of(FinancialMeasure.FREE_CASH_FLOW)
    operating = understanding.of(FinancialMeasure.OPERATING_CASH_FLOW)

    assert free is not None and operating is not None
    assert operating.value == pytest.approx(100000.0)
    assert free.value == pytest.approx(88000.0)
    assert free.unit is MeasureUnit.CURRENCY


def test_the_balance_sheet_ratios_are_computed_from_its_own_lines() -> None:
    understanding = measure("JPM", {StatementKind.BALANCE_SHEET: balance_sheet()})

    current = understanding.of(FinancialMeasure.CURRENT_RATIO)
    leverage = understanding.of(FinancialMeasure.LIABILITIES_TO_EQUITY)

    assert current is not None and leverage is not None
    assert current.value == pytest.approx(1.046, abs=1e-3)
    assert current.unit is MeasureUnit.MULTIPLE
    assert leverage.value == pytest.approx(11.142, abs=1e-3)


# ── what it refuses ──────────────────────────────────────────────────


def test_a_measure_whose_statement_is_absent_says_so_and_blames_nothing() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    current = understanding.of(FinancialMeasure.CURRENT_RATIO)

    assert current is not None
    assert current.value is None
    assert current.absent_because is not None
    assert "holds no consensus on that statement" in current.absent_because
    assert "Nothing about the company follows" in current.absent_because


def test_a_measure_missing_one_figure_inherits_the_consensus_wording() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    gross = understanding.of(FinancialMeasure.GROSS_MARGIN)

    assert gross is not None
    assert gross.value is None
    assert gross.absent_because is not None
    assert "No such line." in gross.absent_because


def test_nothing_is_derived_where_the_arithmetic_is_refused() -> None:
    """Two figures in different columns are two periods, and are not a ratio."""

    revenue = figure("Total net revenue", 182447.0, row=1)
    mismatched = figure("Net income", 57048.0, header="2024", row=4, column=2)

    understanding = measure(
        "JPM",
        {
            StatementKind.INCOME_STATEMENT: consensus(
                StatementKind.INCOME_STATEMENT,
                (
                    fact(StatementConcept.TOTAL_REVENUE, revenue),
                    fact(StatementConcept.NET_INCOME, mismatched),
                ),
            )
        },
    )

    net_margin = understanding.of(FinancialMeasure.NET_MARGIN)

    assert net_margin is not None
    assert net_margin.value is None
    assert net_margin.absent_because is not None
    assert "share a period" in net_margin.absent_because


def test_consensuses_of_two_documents_are_refused() -> None:
    with pytest.raises(ValueError, match="one immutable"):
        measure(
            "JPM",
            {
                StatementKind.INCOME_STATEMENT: income(),
                StatementKind.BALANCE_SHEET: consensus(
                    StatementKind.BALANCE_SHEET, (), key="0000019617-25-000001"
                ),
            },
        )


def test_a_consensus_filed_under_the_wrong_statement_is_refused() -> None:
    with pytest.raises(ValueError, match="was given as the"):
        measure("JPM", {StatementKind.BALANCE_SHEET: income()})


def test_nothing_is_derived_from_no_consensus_at_all() -> None:
    with pytest.raises(ValueError, match="none was given"):
        measure("JPM", {})


# ── what it carries ──────────────────────────────────────────────────


def test_a_measure_is_as_established_as_the_narrowest_figure_beneath_it() -> None:
    understanding = measure("JPM", {StatementKind.BALANCE_SHEET: balance_sheet()})

    leverage = understanding.of(FinancialMeasure.LIABILITIES_TO_EQUITY)
    current = understanding.of(FinancialMeasure.CURRENT_RATIO)

    assert leverage is not None and leverage.support is not None
    assert current is not None and current.support is not None

    # Total liabilities settled 3 of 5; equity settled 5 of 5. The ratio
    # is carried by the weaker of the two, never by the stronger.
    assert leverage.support.agreeing == 3
    assert current.support.agreeing == 5
    assert leverage in understanding.narrow_support


def test_the_width_beneath_the_whole_is_taken_at_its_narrowest() -> None:
    understanding = measure(
        "JPM",
        {
            StatementKind.INCOME_STATEMENT: income(),
            StatementKind.CASH_FLOW_STATEMENT: consensus(
                StatementKind.CASH_FLOW_STATEMENT, (), count=2
            ),
        },
    )

    assert understanding.quorate is False
    assert understanding.observation_count == 2


def test_the_provenance_says_the_platform_computed_it() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    assert "computed by this platform" in understanding.reading.source
    assert "no figure derived by a model" in understanding.reading.source


def test_established_and_absent_measures_are_separable() -> None:
    understanding = measure("JPM", {StatementKind.INCOME_STATEMENT: income()})

    established = {found.measure for found in understanding.established}
    absent = {missing.measure for missing in understanding.not_established}

    assert FinancialMeasure.NET_MARGIN in established
    assert FinancialMeasure.GROSS_MARGIN in absent
    assert not established & absent
