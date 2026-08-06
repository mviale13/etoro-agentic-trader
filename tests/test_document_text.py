"""Reading a filing as words, and as the tables it prints."""

import html
import re

from app.providers.document_text import flatten, read_tables

_TAGS = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def previously(document: str) -> str:
    """The reduction this platform read filings through before tables."""

    text = html.unescape(_TAGS.sub(" ", document))
    text = _WHITESPACE.sub(" ", text)

    return _BLANK_LINES.sub("\n\n", text)


MARKUP = """\
<html><body>
<p>ITEM 7. Management&#8217;s Discussion</p>
<p>The following table presents revenues from our operating segments:</p>
<table>
  <tr><td>($ in millions)</td><td colspan="2">2025</td><td colspan="2">2024</td></tr>
  <tr><td>Entertainment</td><td>$</td><td>42,466</td><td>$</td><td>41,186</td></tr>
  <tr><td>Experiences</td><td colspan="2">36,156</td><td colspan="2">34,151</td></tr>
  <tr><td>Revenues</td><td>$</td><td>94,425</td><td>$</td><td>91,361</td></tr>
</table>
<p>ITEM 8. Financial Statements</p>
</body></html>
"""


def test_the_words_are_reduced_exactly_as_they_always_were() -> None:
    """
    The sections are found by searching this text.

    A different reduction would silently locate different sections, so
    the one thing the table work must not change is the prose it reads
    beside them.
    """

    assert flatten(MARKUP).text == previously(MARKUP)


def test_every_character_can_be_pointed_back_at_the_markup() -> None:
    """What makes a section found in the text cuttable out of the markup."""

    flat = flatten(MARKUP)

    assert len(flat.origin) == len(flat.text)

    start = flat.text.index("The following table")
    end = flat.text.index("ITEM 8.")

    opens, closes = flat.markup_span(start, end)

    assert MARKUP[opens:closes].count("<table") == 1
    assert "ITEM 8." not in MARKUP[opens:closes]


def test_a_table_is_read_as_rows_and_columns() -> None:
    """
    The structure is the evidence.

    Flattened, this table still contains every word and every figure and
    has lost the only thing that says which figure belongs to which row.
    """

    tables = read_tables(MARKUP)

    assert len(tables) == 1

    table = tables[0]

    assert table.rows[1].cells == ("Entertainment", "$ 42,466", "$ 41,186")
    assert table.column_header(1) == "2025"
    assert table.cell(3, 1) == "$ 94,425"


def test_the_spacing_a_filer_prints_is_kept_so_the_grid_stays_a_grid() -> None:
    """
    Dropping blank cells reads better and moves figures under wrong headings.

    Volkswagen's revenue table leaves the label cell of its total row
    empty. Dropping blanks shifted that one row left by one, so a column
    index meant a different segment on the total row than on every other
    row — the exact assumption a share of a total rests on, broken by the
    tidying that was meant to protect it.
    """

    shifted = """
    <table>
      <tr><td>Mio. EUR</td><td>Cars</td><td>Trucks</td><td>Group</td></tr>
      <tr><td>Revenue</td><td>244.484</td><td>42.540</td><td>321.913</td></tr>
      <tr><td></td><td>244.484</td><td>42.540</td><td>321.913</td></tr>
    </table>
    """

    table = read_tables(shifted)[0]

    assert [len(row.cells) for row in table.rows] == [4, 4, 4]
    assert table.rows[2].cells[3] == "321.913"


def test_the_caption_carries_what_the_cells_leave_out() -> None:
    """Where a filer states the units and the scale."""

    assert "operating segments" in read_tables(MARKUP)[0].caption


def test_a_wide_cell_occupies_the_columns_it_says_it_does() -> None:
    """
    Honouring colspan is what makes a filing's table a grid at all.

    Filers pad with one wide empty cell on some rows and several narrow
    ones on others. Counting cells without expanding them puts the same
    column at a different index on every row, which is exactly the
    assumption a share of a total rests on.
    """

    spanned = """
    <table>
      <tr><td>($ in millions)</td><td colspan="2">2025</td><td>2024</td></tr>
      <tr><td>Entertainment</td><td>42,466</td><td>x</td><td>41,186</td></tr>
      <tr><td>Revenues</td><td>94,425</td><td>y</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(spanned)[0]

    assert table.rows[0].cells == ("($ in millions)", "2025", "", "2024")
    assert table.column_header(1) == "2025"
    assert table.cell(1, 1) == "42,466"


def test_a_currency_symbol_belongs_to_the_figure_beside_it() -> None:
    """
    Filers typeset "$ 42,466" and "17,672" on alternating rows of one table.

    Visually the numbers line up; structurally they sit in different
    columns, so a column index means the 2025 figure on one row and
    nothing at all on the next. A symbol on its own is not a value.
    """

    mixed = """
    <table>
      <tr><td>($ in millions)</td><td colspan="2">2025</td></tr>
      <tr><td>Entertainment</td><td>$</td><td>42,466</td></tr>
      <tr><td>Sports</td><td colspan="2">17,672</td></tr>
    </table>
    """

    table = read_tables(mixed)[0]

    assert table.rows[1].cells == ("Entertainment", "$ 42,466")
    assert table.rows[2].cells == ("Sports", "17,672")
    assert table.column_header(1) == "2025"


def test_a_table_used_for_layout_is_not_evidence_of_anything() -> None:
    """Filers typeset with tables constantly, and none of it reports a figure."""

    layout = """
    <table><tr><td>Table of Contents</td></tr>
    <tr><td>Item 1. Business</td><td>4</td></tr></table>
    """

    assert read_tables(layout) == ()


def test_a_nested_table_is_part_of_the_cell_that_contains_it() -> None:
    """
    One number must have one address.

    A filer nests tables for layout, and a nested table addressed as a
    peer of its parent would give the same cell two different addresses.
    """

    nested = """
    <table>
      <tr><td>Revenues</td><td>2025</td></tr>
      <tr><td>Entertainment</td><td><table><tr><td>42,466</td></tr></table></td></tr>
      <tr><td>Total</td><td>94,425</td></tr>
    </table>
    """

    tables = read_tables(nested)

    assert len(tables) == 1
    assert tables[0].rows[1].cells == ("Entertainment", "42,466")


def test_a_stylesheet_inside_a_table_is_not_a_cell_s_contents() -> None:
    """A cell is quoted verbatim in evidence, so a rule set must not land in one."""

    styled = """
    <table>
      <tr><td>Revenues</td><td>2025</td></tr>
      <tr><td>Entertainment</td><td><style>.x{color:red}</style>42,466</td></tr>
      <tr><td>Total</td><td>94,425</td></tr>
    </table>
    """

    assert read_tables(styled)[0].rows[1].cells == ("Entertainment", "42,466")
