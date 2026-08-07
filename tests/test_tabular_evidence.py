"""A citation that resolves is not a citation that supports anything."""

import pytest

from app.domain.tabular_evidence import (
    CellReference,
    EvidenceNotApplicable,
    MeasuredShare,
    ReportedFigure,
    SourceTable,
    TableRow,
    figure_at,
    read_number,
)

TABLE = SourceTable(
    index=0,
    caption="Sales revenue by division (€ million)",
    rows=(
        TableRow(cells=("", "2024", "2023")),
        TableRow(cells=("Passenger Cars", "122,321", "118,004")),
        TableRow(cells=("Commercial Vehicles", "48,507", "45,220")),
        TableRow(cells=("Total", "322,284", "312,000")),
    ),
)

TABLES = (TABLE,)


def at(row: int, column: int = 1) -> CellReference:
    return CellReference(table=0, row=row, column=column)


# ── reading a printed number ────────────────────────────────────────


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        ("322,284", 322284.0),
        ("322.284", 322284.0),
        ("1,234.5", 1234.5),
        ("1.234,5", 1234.5),
        ("$ 42,466", 42466.0),
        ("(1,869)", -1869.0),
        ("3.5", 3.5),
        ("0", 0.0),
    ],
)
def test_a_printed_number_is_read_by_pattern_rather_than_by_locale(
    printed: str,
    expected: float,
) -> None:
    """
    A document's language is not always the one its numbers are typeset in.

    Guessing at the separators is a thousandfold error when the guess is
    wrong, so the digits themselves decide: exact groups of three are a
    thousands separator, and where both marks appear the last one is the
    decimal.
    """

    assert read_number(printed) == expected


@pytest.mark.parametrize(
    "printed", ["", "  ", "Passenger Cars", "n/a", "—", "($ in millions)"]
)
def test_a_cell_that_prints_no_number_reads_as_none(printed: str) -> None:
    """Most cells in a filing's tables are labels, and that is not a failure."""

    assert read_number(printed) is None


# ── applicability ───────────────────────────────────────────────────


def test_a_figure_is_read_back_out_of_the_document() -> None:
    """
    What the citation binds together, and none of it taken on trust.

    The row label, the column header and the caption are read off the
    table rather than supplied by whatever asserted the fact, because
    those three are what turn "122,321" into something a reader can check.
    """

    figure = figure_at(TABLES, at(row=1), 122321.0, "Passenger Cars revenue")

    assert figure.label == "Passenger Cars"
    assert figure.column_header == "2024"
    assert figure.printed == "122,321"
    assert figure.caption == "Sales revenue by division (€ million)"
    assert 'under "2024"' in figure.stated()


def test_a_citation_of_a_column_header_is_refused() -> None:
    """The live failure. The words were there; they supported nothing."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at(TABLES, at(row=0), 2024.0, "Passenger Cars revenue")

    assert "header row" in str(refused.value)


def test_a_citation_of_the_label_column_is_refused() -> None:
    """The mirror of the header row: it names the rows and measures nothing."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at(TABLES, at(row=1, column=0), 122321.0, "Passenger Cars revenue")

    assert "label column" in str(refused.value)


def test_a_citation_of_a_cell_that_prints_words_is_refused() -> None:
    """A cell that prints no number cannot be evidence of a quantity."""

    worded = SourceTable(
        index=0,
        caption="Revenue",
        rows=(
            TableRow(cells=("", "2024")),
            TableRow(cells=("Passenger Cars", "not reported")),
            TableRow(cells=("Total", "322,284")),
        ),
    )

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((worded,), at(row=1), 122321.0, "Passenger Cars revenue")

    assert "not a number" in str(refused.value)
    assert "supports nothing" in str(refused.value)


def test_a_citation_the_document_contradicts_is_refused() -> None:
    """The reading and the document disagreeing is the whole check."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at(TABLES, at(row=1), 999.0, "Passenger Cars revenue")

    assert "disagree about what is there" in str(refused.value)


def test_a_citation_of_a_cell_that_is_not_there_is_refused() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at(TABLES, at(row=9), 1.0, "Passenger Cars revenue")

    assert "no cell" in str(refused.value)


def test_a_citation_of_a_table_that_is_not_there_is_refused() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at(TABLES, CellReference(table=4, row=1, column=1), 1.0, "Revenue")

    assert "1 tables" in str(refused.value)


def test_a_figure_neither_coordinate_names_is_refused() -> None:
    """
    Both coordinates must be named, because either one may name the part.

    Which of the two names the part of the business and which names the
    period depends on how the filer laid the table out, and that is not
    known when the cell is resolved. A figure missing either name is a
    figure nothing can describe — refused rather than kept with a blank,
    because a size whose subject is unproven is exactly the plausible
    figure that reads as a measurement.
    """

    unlabelled = SourceTable(
        index=0,
        caption="Revenue",
        rows=(
            TableRow(cells=("", "", "")),
            TableRow(cells=("Passenger Cars", "122,321", "118,004")),
            TableRow(cells=("", "322,284", "312,000")),
        ),
    )

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((unlabelled,), at(row=1), 122321.0, "Passenger Cars revenue")

    assert "column carries no header" in str(refused.value)

    unnamed_row = SourceTable(
        index=0,
        caption="Revenue",
        rows=(
            TableRow(cells=("Mio. €", "2024")),
            TableRow(cells=("", "122,321")),
        ),
    )

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((unnamed_row,), at(row=1), 122321.0, "Passenger Cars revenue")

    assert "row carries no label" in str(refused.value)


# ── the relationship ────────────────────────────────────────────────


def figure(row: int, value: float, column: int = 1) -> ReportedFigure:
    return figure_at(TABLES, at(row=row, column=column), value, "a figure")


def test_a_share_is_computed_from_two_figures_that_were_both_checked() -> None:
    share = MeasuredShare(
        numerator=figure(row=1, value=122321.0),
        denominator=figure(row=3, value=322284.0),
    )

    assert round(share.share, 4) == 0.3795
    assert share.stated().startswith("38% — ")


def test_two_figures_sharing_neither_coordinate_are_not_related() -> None:
    """
    This year's segment over last year's total is arithmetic about nothing.

    Both figures are real and the division is sound, and the answer
    covers no period at all. Requiring the two to agree on one of their
    coordinates is what closes it — here they agree on neither.
    """

    with pytest.raises(EvidenceNotApplicable) as refused:
        MeasuredShare(
            numerator=figure(row=1, value=122321.0, column=1),
            denominator=figure(row=3, value=312000.0, column=2),
        )

    assert "neither a row nor a column" in str(refused.value)


# ── the same relationship, laid out the other way ───────────────────
#
# Volkswagen's segment note runs the segments across the top and the line
# items down the side. The figures are as real and the relationship as
# checkable; what changes is which coordinate names the part.


TRANSPOSED = SourceTable(
    index=0,
    caption="BERICHTSSEGMENTE 2025 (Mio. €)",
    rows=(
        TableRow(
            cells=(
                "Mio. €",
                "Pkw und leichte Nutzfahrzeuge",
                "Nutzfahrzeuge",
                "Volkswagen Konzern",
            )
        ),
        TableRow(cells=("Umsatzerlöse", "244.484", "42.540", "321.913")),
        TableRow(cells=("Kosten der Umsatzerlöse", "210.987", "34.696", "270.671")),
    ),
)


def test_a_share_reads_the_same_when_the_segments_are_columns() -> None:
    """
    The invariant is the shared coordinate, not the shape of the table.

    An earlier design required both figures to share a column, which is
    right for an American filing and wrong for an IFRS segment note —
    where the parts run across the page and the shared coordinate is the
    row. Fitting the rule to one layout would have left every European
    filing's sizes permanently unmeasurable.
    """

    share = MeasuredShare(
        numerator=figure_at((TRANSPOSED,), CellReference(0, 1, 1), 244484.0, "a part"),
        denominator=figure_at((TRANSPOSED,), CellReference(0, 1, 3), 321913.0, "total"),
    )

    assert round(share.share, 4) == 0.7595

    # The row is what the two agree on, so the row names the measure and
    # the column headers name the part and the whole.
    assert share.part == "Pkw und leichte Nutzfahrzeuge"
    assert share.whole == "Volkswagen Konzern"
    assert share.basis == "Umsatzerlöse"
    assert 'on "Umsatzerlöse"' in share.stated()


def test_the_part_is_named_by_the_row_when_the_segments_are_rows() -> None:
    """The same three questions, answered off the other axis."""

    share = MeasuredShare(
        numerator=figure(row=1, value=122321.0),
        denominator=figure(row=3, value=322284.0),
    )

    assert share.part == "Passenger Cars"
    assert share.whole == "Total"
    assert share.basis == "2024"
    assert 'under "2024"' in share.stated()


def test_two_figures_from_different_tables_are_not_known_to_share_a_scale() -> None:
    """
    Millions over thousands is wrong by a factor of a thousand, silently.

    Keeping the arithmetic inside one table is what makes the scale
    irrelevant, without this platform having to parse a caption to
    discover what the scale was.
    """

    elsewhere = ReportedFigure(
        label="Total",
        column_header="2024",
        printed="322,284",
        value=322284.0,
        cell=CellReference(table=3, row=3, column=1),
        caption="in € thousand",
    )

    with pytest.raises(EvidenceNotApplicable) as refused:
        MeasuredShare(numerator=figure(row=1, value=122321.0), denominator=elsewhere)

    assert "another table" in str(refused.value)


def test_the_right_number_at_the_wrong_coordinate_is_still_refused() -> None:
    """
    The acceptance case for the whole model: matching the text is not enough.

    This table prints 122,321 four times over — as Passenger Cars in
    2024, as Commercial Vehicles in 2023, as a total, and inside a row
    that is not revenue at all. A check that asked only "does the
    document contain this number?" passes on every one of them, and so
    would a check that asked "are these words in the document?".

    Only the coordinate relationship distinguishes them. Each citation
    below names a cell that genuinely prints 122,321 and genuinely means
    something else, and each is refused — not because the number is
    wrong, but because the cited coordinate does not measure what the
    citation says it measures. The one true coordinate passes.
    """

    misleading = SourceTable(
        index=0,
        caption="Segment revenue and capital expenditure (€ million)",
        rows=(
            TableRow(cells=("", "2024", "2023")),
            TableRow(cells=("Passenger Cars", "122,321", "118,004")),
            TableRow(cells=("Commercial Vehicles", "48,507", "122,321")),
            TableRow(cells=("Capital expenditure", "122,321", "31,004")),
            TableRow(cells=("Total", "322,284", "312,000")),
        ),
    )

    tables = (misleading,)

    def cited(row: int, column: int) -> str:
        with pytest.raises(EvidenceNotApplicable) as refused:
            MeasuredShare(
                numerator=figure_at(
                    tables,
                    CellReference(0, row, column),
                    122321.0,
                    "Passenger Cars revenue",
                ),
                denominator=figure_at(
                    tables, CellReference(0, 4, 1), 322284.0, "total revenue"
                ),
            )

        return str(refused.value)

    # The prior year's figure for another segment. Same number, same
    # table, and it is neither this segment nor this period.
    assert "neither a row nor a column" in cited(row=2, column=2)

    # A row of the same table that is not revenue at all. The column is
    # right, the number is right, and the row measures capital spending.
    capital = figure_at(
        tables, CellReference(0, 3, 1), 122321.0, "Passenger Cars revenue"
    )

    assert capital.label == "Capital expenditure"

    # Nothing in the arithmetic objects — it is the label that gives it
    # away, which is why the label is read off the document and carried.
    share = MeasuredShare(
        numerator=capital,
        denominator=figure_at(
            tables, CellReference(0, 4, 1), 322284.0, "total revenue"
        ),
    )

    assert share.part == "Capital expenditure"

    # And the coordinate that actually measures what was claimed.
    correct = MeasuredShare(
        numerator=figure_at(
            tables, CellReference(0, 1, 1), 122321.0, "Passenger Cars revenue"
        ),
        denominator=figure_at(
            tables, CellReference(0, 4, 1), 322284.0, "total revenue"
        ),
    )

    assert correct.part == "Passenger Cars"
    assert correct.basis == "2024"
    assert round(correct.share, 4) == 0.3795


def test_a_figure_measured_against_itself_is_refused() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        MeasuredShare(
            numerator=figure(row=3, value=322284.0),
            denominator=figure(row=3, value=322284.0),
        )

    assert "against itself" in str(refused.value)


#: Caterpillar's shape: the filer typesets the table's own title into a
#: row of the table, so the row carrying the periods is the second one.
TITLED = SourceTable(
    index=0,
    caption="We expect machine dealer inventory to increase in 2026.",
    rows=(
        TableRow(cells=("Sales and Revenues by Segment", "", "", "")),
        TableRow(cells=("(Millions of dollars)", "2024", "2025", "$ Change")),
        TableRow(cells=("Construction Industries", "25,455", "25,060", "(395)")),
        TableRow(
            cells=("Consolidated Sales and Revenues", "64,809", "67,589", "2,780")
        ),
    ),
)


def test_a_title_the_filer_typeset_into_the_table_names_no_column() -> None:
    """
    So the row beneath it does. Taking row 0 as the header regardless
    refused every figure in Caterpillar's segment table as measuring
    nothing — including the consolidated total, which is the one cell
    every segment's size is a share of.
    """

    figure = figure_at(
        (TITLED,),
        CellReference(table=0, row=3, column=2),
        67589.0,
        "Total sales and revenues",
    )

    assert figure.column_header == "2025"
    assert figure.label == "Consolidated Sales and Revenues"


def test_the_row_that_names_the_columns_is_still_refused_as_a_figure() -> None:
    """Wherever it sits. A header labels; it measures nothing."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((TITLED,), CellReference(table=0, row=1, column=2), 2025.0, "Revenue")

    assert "header row" in str(refused.value)


def test_the_title_row_above_the_header_is_refused_too() -> None:
    """It is further from measuring anything, not closer."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((TITLED,), CellReference(table=0, row=0, column=1), 1.0, "Revenue")

    assert "header row" in str(refused.value)


def test_a_first_row_that_names_nothing_is_a_missing_header_not_a_title() -> None:
    """
    A row holding nothing is not a title, so nothing is promoted into
    its place. Refusing the figures of a table with no header is the
    correct outcome; reading the first row of data as one would invent
    the very relationship this platform checks.
    """

    headerless = SourceTable(
        index=0,
        caption="Revenue",
        rows=(
            TableRow(cells=("", "", "")),
            TableRow(cells=("Passenger Cars", "122,321", "118,004")),
        ),
    )

    assert headerless.header_row == 0

    with pytest.raises(EvidenceNotApplicable) as refused:
        figure_at((headerless,), at(row=1), 122321.0, "Passenger Cars revenue")

    assert "column carries no header" in str(refused.value)
