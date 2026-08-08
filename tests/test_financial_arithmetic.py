"""Arithmetic over checked figures: what it computes and what it refuses."""

import pytest

from app.domain.evidence import EvidenceNotApplicable
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredChange,
    MeasuredNet,
    MeasuredRatio,
    ReportedFigure,
    comparable,
    preceding,
    stated_year,
)


def figure(
    label: str = "Total net revenue",
    header: str = "2025",
    printed: str = "182,447",
    value: float = 182447.0,
    table: int = 0,
    row: int = 1,
    column: int = 1,
) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header=header,
        printed=printed,
        value=value,
        cell=CellReference(table=table, row=row, column=column),
        caption="(in millions)",
    )


# ── what makes two figures comparable ────────────────────────────────


def test_two_tables_are_two_scales_and_are_refused() -> None:
    with pytest.raises(EvidenceNotApplicable, match="share a scale"):
        comparable(figure(), figure(row=2, table=1))


def test_two_columns_are_two_periods_and_are_refused() -> None:
    with pytest.raises(EvidenceNotApplicable, match="share a period"):
        comparable(figure(), figure(row=2, column=2))


def test_a_figure_is_not_comparable_with_itself() -> None:
    with pytest.raises(EvidenceNotApplicable, match="against itself"):
        comparable(figure(), figure())


# ── ratios ───────────────────────────────────────────────────────────


def test_a_ratio_is_computed_from_two_checked_cells() -> None:
    ratio = MeasuredRatio(
        numerator=figure("Net income", printed="57,048", value=57048.0, row=2),
        denominator=figure(),
    )

    assert ratio.ratio == pytest.approx(0.3127, abs=1e-4)
    assert ratio.period == "2025"
    assert '"Net income" 57,048 over "Total net revenue" 182,447' in ratio.stated()


def test_a_ratio_is_not_bounded_the_way_a_share_is() -> None:
    """Liabilities exceed equity at every bank, and that is not an error."""

    ratio = MeasuredRatio(
        numerator=figure("Total liabilities", printed="3,900,000", value=3.9e6, row=2),
        denominator=figure("Total stockholders' equity", value=350000.0),
    )

    assert ratio.ratio > 1.0


def test_a_negative_numerator_is_a_loss_not_a_refusal() -> None:
    ratio = MeasuredRatio(
        numerator=figure("Net income (loss)", printed="(4,321)", value=-4321.0, row=2),
        denominator=figure(),
    )

    assert ratio.ratio < 0.0


def test_nothing_can_be_measured_against_zero() -> None:
    with pytest.raises(EvidenceNotApplicable, match="nothing can be measured"):
        MeasuredRatio(
            numerator=figure(row=2),
            denominator=figure(printed="—", value=0.0),
        )


# ── subtraction ──────────────────────────────────────────────────────


def test_free_cash_flow_subtracts_the_magnitude_of_a_bracketed_outflow() -> None:
    net = MeasuredNet(
        gross=figure("Net cash provided by operating activities", value=100000.0),
        deducted=figure(
            "Purchases of property and equipment",
            printed="(12,000)",
            value=-12000.0,
            row=2,
        ),
    )

    assert net.net == pytest.approx(88000.0)


def test_the_same_spending_printed_positive_subtracts_identically() -> None:
    """A filer's sign convention must not decide what the company spent."""

    net = MeasuredNet(
        gross=figure("Net cash provided by operating activities", value=100000.0),
        deducted=figure(
            "Purchases of property and equipment",
            printed="12,000",
            value=12000.0,
            row=2,
        ),
    )

    assert net.net == pytest.approx(88000.0)


# ── the period a column names ────────────────────────────────────────


def test_a_year_is_read_off_the_header_the_filer_printed() -> None:
    assert stated_year("2025") == 2025
    assert stated_year("December 31, 2024") == 2024
    assert stated_year("Year ended December 31, 2023") == 2023


def test_a_header_naming_no_year_or_two_years_establishes_no_period() -> None:
    assert stated_year("Total") is None
    assert stated_year("") is None
    assert stated_year("2025 and 2024") is None


def test_a_year_inside_a_longer_number_is_not_a_year() -> None:
    assert stated_year("120250") is None


def test_the_prior_period_is_the_closest_earlier_year_on_the_row() -> None:
    anchor = figure(column=1)
    row = (
        anchor,
        figure(header="2024", printed="177,556", value=177556.0, column=2),
        figure(header="2023", printed="158,104", value=158104.0, column=3),
    )

    earlier = preceding(row, anchor)

    assert earlier is not None
    assert earlier.column_header == "2024"


def test_the_prior_period_is_found_when_the_filer_prints_oldest_first() -> None:
    """Chronology comes from the headers, never from column position."""

    anchor = figure(column=3)
    row = (
        figure(header="2023", printed="158,104", value=158104.0, column=1),
        figure(header="2024", printed="177,556", value=177556.0, column=2),
        anchor,
    )

    earlier = preceding(row, anchor)

    assert earlier is not None
    assert earlier.column_header == "2024"


def test_two_columns_naming_one_earlier_year_settle_nothing() -> None:
    """A restatement printed beside the original: two could answer, so none does."""

    anchor = figure(column=1)
    row = (
        anchor,
        figure(header="2024", printed="177,556", value=177556.0, column=2),
        figure(header="2024 restated", printed="177,000", value=177000.0, column=3),
    )

    assert preceding(row, anchor) is None


def test_an_undated_anchor_has_no_prior_period() -> None:
    anchor = figure(header="Total", column=1)
    row = (anchor, figure(header="2024", value=177556.0, column=2))

    assert preceding(row, anchor) is None


# ── change ───────────────────────────────────────────────────────────


def test_a_change_is_computed_against_the_earlier_figure() -> None:
    change = MeasuredChange(
        later=figure(column=1),
        earlier=figure(header="2024", printed="177,556", value=177556.0, column=2),
    )

    assert change.change == pytest.approx(0.02754, abs=1e-5)
    assert 'against 177,556 under "2024"' in change.stated()


def test_a_change_against_a_loss_is_refused_rather_than_reported() -> None:
    """A rise from a loss to a profit is real, and is not a growth rate."""

    with pytest.raises(EvidenceNotApplicable, match="not a growth rate"):
        MeasuredChange(
            later=figure(column=1),
            earlier=figure(header="2024", printed="(1,000)", value=-1000.0, column=2),
        )


def test_a_change_across_two_lines_is_refused() -> None:
    with pytest.raises(EvidenceNotApplicable, match="different line"):
        MeasuredChange(
            later=figure(column=1),
            earlier=figure(header="2024", value=177556.0, row=2, column=2),
        )
