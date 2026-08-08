"""The financial analysts on established facts, and never on a provider's."""

from datetime import UTC, datetime

import pytest

from app.analysts.filing_analysts import (
    filing_balance_sheet,
    filing_cash_flow,
    filing_growth,
    filing_profitability,
)
from app.domain.agreement import agreement
from app.domain.financial_statements import StatementKind
from app.domain.financial_understanding import (
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
)
from app.domain.profitability_opinion import ProfitabilityVerdict
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure


def figure(label: str = "Net income", value: float = 57048.0) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header="2025",
        printed=f"{value:,.0f}",
        value=value,
        cell=CellReference(table=0, row=1, column=1),
        caption="(in millions)",
    )


def established(
    name: FinancialMeasure,
    value: float | None,
    *,
    because: str | None = None,
) -> EstablishedMeasure:
    if value is None:
        return EstablishedMeasure(
            measure=name,
            value=None,
            absent_because=because or "The filing establishes no such figure.",
        )

    return EstablishedMeasure(
        measure=name,
        value=value,
        basis=(figure(),),
        stated='"Net income" 57,048 over "Total net revenue" 182,447',
        support=agreement("where it prints", ["found"] * 5),
    )


def understanding(*measures: EstablishedMeasure) -> FinancialUnderstanding:
    return FinancialUnderstanding(
        symbol="JPM",
        source="10-K, via SEC EDGAR",
        reading=Provenance(
            source="computed by this platform",
            observed_at=datetime(2026, 2, 14, tzinfo=UTC),
        ),
        quorate=True,
        observation_count=5,
        quorum=5,
        statements=(StatementKind.INCOME_STATEMENT,),
        measures=measures,
    )


def test_an_opinion_is_scored_from_figures_read_out_of_the_filing() -> None:
    opinion = filing_profitability().analyze(
        understanding(
            established(FinancialMeasure.GROSS_MARGIN, 0.65),
            established(FinancialMeasure.OPERATING_MARGIN, 0.35),
            established(FinancialMeasure.NET_MARGIN, 0.31),
        )
    )

    assert opinion.verdict is ProfitabilityVerdict.EXCELLENT
    assert opinion.confidence == pytest.approx(1.0)
    assert opinion.uncertainty == ()


def test_every_evidence_line_names_the_cells_it_was_computed_from() -> None:
    opinion = filing_profitability().analyze(
        understanding(established(FinancialMeasure.NET_MARGIN, 0.31))
    )

    assert opinion.evidence == (
        'Net margin is 31.0% — "Net income" 57,048 over "Total net revenue" 182,447.',
    )


def test_an_absent_measure_is_uncertainty_in_the_filings_own_words() -> None:
    """Never "data is unavailable" — which fact is missing, and whose."""

    opinion = filing_profitability().analyze(
        understanding(
            established(FinancialMeasure.NET_MARGIN, 0.31),
            established(
                FinancialMeasure.GROSS_MARGIN,
                None,
                because="The income statement prints no gross profit line.",
            ),
        )
    )

    assert "The income statement prints no gross profit line." in opinion.uncertainty


def test_a_missing_figure_is_never_filled_from_anywhere_else() -> None:
    """The two routes do not blend: an absence stays an absence."""

    opinion = filing_cash_flow().analyze(
        understanding(
            established(
                FinancialMeasure.OPERATING_CASH_FLOW,
                None,
                because="No cash flow statement was located.",
            ),
            established(
                FinancialMeasure.FREE_CASH_FLOW,
                None,
                because="No cash flow statement was located.",
            ),
        )
    )

    assert opinion.verdict.value == "unknown"
    assert opinion.evidence == ()
    assert opinion.confidence == pytest.approx(0.0)


def test_confidence_falls_with_how_much_the_filing_established() -> None:
    partial = filing_profitability().analyze(
        understanding(established(FinancialMeasure.NET_MARGIN, 0.31))
    )

    assert partial.confidence == pytest.approx(1 / 3)


def test_growth_reads_both_rows_and_scores_them_by_the_owning_rule_table() -> None:
    opinion = filing_growth().analyze(
        understanding(
            established(FinancialMeasure.REVENUE_GROWTH, 0.0275),
            established(FinancialMeasure.EARNINGS_GROWTH, -0.0243),
        )
    )

    assert len(opinion.evidence) == 2
    assert opinion.uncertainty == ()


def test_the_balance_sheet_route_scores_liquidity_and_not_leverage() -> None:
    """Total liabilities is not debt, so the debt thresholds do not apply."""

    analyst = filing_balance_sheet()

    opinion = analyst.analyze(
        understanding(
            established(FinancialMeasure.CURRENT_RATIO, 1.8),
            established(FinancialMeasure.LIABILITIES_TO_EQUITY, 11.14),
        )
    )

    assert analyst.expected_observation_count == 1
    assert len(opinion.evidence) == 1
    assert "Current ratio" in opinion.evidence[0]
    assert all("iabilities" not in line for line in opinion.evidence)


def test_a_currency_measure_keeps_the_scale_its_caption_states() -> None:
    """182,447 under "(in millions)" must never be printed as $182.4K."""

    opinion = filing_cash_flow().analyze(
        understanding(established(FinancialMeasure.OPERATING_CASH_FLOW, 100000.0))
    )

    assert "100,000 (in millions)" in opinion.evidence[0]
