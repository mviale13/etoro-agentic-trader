"""A cell occupies every column and row its own markup asserts — and no more.

BQ28. Honeywell's income statement returned zero headed figures because the
grid ignored two assertions the filer wrote:

- a `rowspan` — the empty label stub above the year row spans down, so the
  year row's cells begin at the fourth column, and a grid that dropped the
  stub shifted every year three columns left, onto the label columns;
- a numeric colspan's *extent* — `2025` spans three columns and the figure
  sits in the span, and while the number is rightly not repeated into the
  covered cells, the extent itself is the only record of which columns the
  year heads.

Both repairs are structural, derived from the markup alone. Nothing here
reads a company, an expected value, a desired concept or a quality result —
and the ambiguity controls pin that a blank the filer did not span stays
blank.
"""

from __future__ import annotations

from tests.test_document_text import read_tables

#: Honeywell's header block, structure verbatim from the filing: the
#: sizing row, the phrase row whose empty stub spans down, the year row
#: written without a leading stub because the rowspan supplies it, the
#: caption, and two data rows. Simplified only in column count (one pad
#: column per block rather than three).
HONEYWELL = """
<table>
  <tr><td/><td/><td/><td/><td/><td/><td/><td/><td/></tr>
  <tr><td colspan="3" rowspan="2"></td>
      <td colspan="6">Years Ended December 31,</td></tr>
  <tr><td colspan="2">2025</td><td colspan="2"></td>
      <td colspan="2">2024</td></tr>
  <tr><td colspan="3"></td><td colspan="6">(Dollars in millions)</td></tr>
  <tr><td colspan="3">Net sales</td><td>$ 37,442</td><td/><td/><td/>
      <td>$ 34,717</td><td/></tr>
  <tr><td colspan="3">Net income</td><td>4,772</td><td/><td/><td/>
      <td>5,740</td><td/></tr>
</table>
"""


def test_the_honeywell_shape_heads_its_figures() -> None:
    """The year lands on the figure column, because the stub spans down."""

    table = read_tables(HONEYWELL)[0]

    # The phrase row is a title (one distinct string of words); the year
    # row beneath it names the columns.
    header = table.rows[table.header_row]

    assert "2025" in header.cells

    year_at = header.cells.index("2025")

    # The years begin after the three columns the rowspan'd stub occupies
    # — the exact displacement that left them on the label columns.
    assert year_at >= 3

    # And the figure sits under its year.
    net_sales = next(
        index for index, row in enumerate(table.rows) if row.label == "Net sales"
    )
    figure_at = next(
        column
        for column, cell in enumerate(table.rows[net_sales].cells)
        if "37,442" in cell
    )

    assert table.column_header(figure_at) == "2025"


def test_a_rowspanned_label_names_every_row_it_covers() -> None:
    """Words repeat downward, on the same rule colspan repeats them across."""

    grouped = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td rowspan="2">Automotive</td><td>10</td><td>20</td></tr>
      <tr><td>30</td><td>40</td></tr>
    </table>
    """

    table = read_tables(grouped)[0]

    assert table.rows[1].label == "Automotive"
    assert table.rows[2].label == "Automotive"

    # And the covered row's own cells landed beside it, not under it.
    assert table.cell(2, 1) == "30"
    assert table.cell(2, 2) == "40"


def test_a_rowspanned_number_occupies_but_never_repeats() -> None:
    """A figure spanning down stays one addressable cell."""

    centered = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Backlog</td><td rowspan="2">42,466</td><td>91,361</td></tr>
      <tr><td>Of which firm</td><td>88,000</td></tr>
    </table>
    """

    table = read_tables(centered)[0]

    assert table.cell(1, 1) == "42,466"

    # The second row's figure lands in the column after the occupied one,
    # which is empty rather than a second copy of 42,466.
    assert table.cell(2, 1) == ""
    assert table.cell(2, 2) == "88,000"


def test_an_ordinary_single_header_table_is_untouched() -> None:
    """No rowspan, no numeric span: the grid is exactly what it was."""

    plain = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Total revenues</td><td>94,425</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(plain)[0]

    assert table.header_row == 0
    assert table.column_header(1) == "2025"
    assert table.column_header(2) == "2024"
    assert table.rows[0].spans == ()


def test_a_spanned_year_heads_the_columns_its_extent_asserts() -> None:
    """The number is not repeated, and the extent still heads the span."""

    spanned = """
    <table>
      <tr><td>(in millions)</td><td colspan="2">2025</td>
          <td colspan="2">2024</td></tr>
      <tr><td>Total revenues</td><td>94,425</td><td>1%</td>
          <td>91,361</td><td>2%</td></tr>
    </table>
    """

    table = read_tables(spanned)[0]

    header = table.rows[table.header_row]

    # The year itself sits once, in the first cell of its span.
    assert header.cells.count("2025") == 1
    assert header.spans == ((1, 2), (3, 2))

    # And every column of the extent is headed by it — the second one
    # through the extent, since its own cell is blank.
    assert table.column_header(1) == "2025"
    assert table.column_header(2) == "2025"
    assert table.column_header(3) == "2024"
    assert table.column_header(4) == "2024"


def test_currency_absorption_collapses_a_span_onto_its_figure() -> None:
    """The $-and-value pair inside a spanned year prunes to one column.

    The absorption moves the value into the symbol's cell and empties the
    one it came from; the emptied column is pruned whole, and the year
    then sits directly over its figure. The extent, reduced to a single
    surviving column, is not recorded — there is nothing left for it to
    cover.
    """

    spanned = """
    <table>
      <tr><td>(in millions)</td><td colspan="2">2025</td><td colspan="2">2024</td></tr>
      <tr><td>Total revenues</td><td>$</td><td>94,425</td><td>$</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(spanned)[0]

    header = table.rows[table.header_row]

    assert header.cells.count("2025") == 1
    assert header.spans == ()

    year_at = header.cells.index("2025")

    assert table.column_header(year_at) == "2025"
    assert table.rows[1].cells[year_at] == "$ 94,425"


def test_a_blank_the_filer_did_not_span_stays_unheaded() -> None:
    """Ambiguity is refused, never guessed — the anti-forward-fill control.

    The blank between the two years is an explicit unspanned cell. A
    neighbour-filling rule would head it with 2025; the extent rule
    cannot, because no extent covers it, and a figure beneath it stays a
    number whose period is unproven.
    """

    gapped = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td/><td>2024</td></tr>
      <tr><td>Total revenues</td><td>94,425</td><td>1.2%</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(gapped)[0]

    assert table.column_header(1) == "2025"
    assert table.column_header(2) == ""
    assert table.column_header(3) == "2024"


def test_extra_cells_do_not_shift_a_period_onto_the_wrong_column() -> None:
    """The misalignment control: explicit pads move nothing.

    Every cell is written out, no colspan and no rowspan anywhere, with
    pad cells between the years. Each figure must stay under its own
    year and the pads under nothing.
    """

    padded = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td/><td/><td>2024</td></tr>
      <tr><td>Total revenues</td><td>94,425</td><td/><td/><td>91,361</td></tr>
    </table>
    """

    table = read_tables(padded)[0]

    assert table.column_header(1) == "2025"

    # The pads were pruned as whole empty columns, so 2024 is adjacent —
    # and still heads its own figure, not 2025's.
    figures = table.rows[1].cells

    year_2024 = table.rows[0].cells.index("2024")

    assert figures[year_2024] == "91,361"


def test_an_empty_spanned_cell_covers_nothing() -> None:
    """A stretch of nothing heads nothing, spanned or not."""

    hollow = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td colspan="2"></td><td>2024</td></tr>
      <tr><td>Total revenues</td><td>94,425</td><td>7</td><td>8</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(hollow)[0]

    assert table.column_header(1) == "2025"
    assert table.column_header(2) == ""
    assert table.column_header(3) == ""
    assert table.column_header(4) == "2024"


def test_a_rowspan_written_absurdly_deep_is_capped() -> None:
    """The bound the colspan already has, held downward too."""

    deep = """
    <table>
      <tr><td rowspan="10000">A</td><td>2025</td></tr>
      <tr><td>1</td></tr>
      <tr><td>2</td></tr>
    </table>
    """

    table = read_tables(deep)[0]

    # The words repeat down into the covered rows without an explosion.
    assert table.rows[1].label == "A"
    assert table.rows[2].label == "A"
