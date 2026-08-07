"""Reading a filing as words, and as the tables it prints."""

import html
import re

from app.providers.document_text import (
    begins_a_block,
    flatten,
    read_regions,
    read_tables,
)

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


# ── the structure a filer typesets ──────────────────────────────────

#: An SEC filer's own idiom, copied from Meta's 10-K: no `<h1>`
#: anywhere, and a heading is a block whose entire content is one short
#: span typeset bold.
_BOLD = "color:#000000;font-family:'Times New Roman',serif;font-weight:700"

SECTIONED = f"""\
<html><body>
<div><span>ITEM 1. Business</span></div>
<div><span style="{_BOLD}">Overview</span></div>
<div><span>We build technology that helps people connect.</span></div>
<div><span style="{_BOLD}">Family of Apps Products</span></div>
<div><span>Facebook helps people <b>share</b> moments and build community.</span></div>
<div><span style="{_BOLD}">Reality Labs Products</span></div>
<div><span>We build augmented and virtual reality hardware.</span></div>
<div><span>ITEM 1A. Risk Factors</span></div>
</body></html>
"""


def sectioned_regions():
    """The regions of the business section, as the provider reads them."""

    flat = flatten(SECTIONED)

    start = flat.text.index("ITEM 1. Business")
    end = flat.text.index("ITEM 1A.")

    return flat.text[start:end].strip(), read_regions(SECTIONED, flat, start, end)


def test_a_filers_bold_block_is_the_heading_it_is_typeset_as() -> None:
    """SEC filers do not use `<h1>`, so the idiom is what gets detected."""

    _, regions = sectioned_regions()

    assert [region.heading for region in regions] == [
        "Overview",
        "Family of Apps Products",
        "Reality Labs Products",
    ]


def test_a_region_runs_to_the_next_heading_and_not_to_the_end() -> None:
    """
    What makes it the *smallest* region the document offers.

    A region bounded at the end of the section instead would hand the
    last segment every word the filer wrote afterwards about competition,
    regulation and its workforce.
    """

    text, regions = sectioned_regions()

    apps = next(r for r in regions if r.heading == "Family of Apps Products")

    inside = text[apps.at : apps.ends]

    assert "Facebook helps people share moments" in inside
    assert "augmented and virtual reality" not in inside


def test_a_regions_coordinates_address_the_section_as_a_caller_receives_it() -> None:
    """
    The prose is handed over stripped, so the regions must describe that
    string. Off by the document's leading whitespace is off silently.
    """

    text, regions = sectioned_regions()

    for region in regions:
        assert text[region.at :].startswith(region.heading)


def test_emphasis_inside_a_sentence_is_not_a_heading() -> None:
    """A heading is alone in its block; bold mid-sentence is not."""

    _, regions = sectioned_regions()

    assert "share" not in [region.heading for region in regions]


def test_a_bold_paragraph_is_not_a_heading_over_a_section() -> None:
    """
    Length is what separates a heading from a paragraph the filer
    emphasised. Measured: every heading in Meta's Item 1 is between 8 and
    50 characters, and nothing longer is bold and alone in its block.
    """

    emphasised = (
        f'<div><span style="{_BOLD}">Heading</span></div>'
        f'<div><span style="{_BOLD}">{"word " * 40}</span></div>'
    )

    flat = flatten(emphasised)

    regions = read_regions(emphasised, flat, 0, len(flat.text))

    assert [region.heading for region in regions] == ["Heading"]


def test_a_document_that_typesets_no_headings_yields_no_regions() -> None:
    """
    Which is not a failure. Ownership falls back to position, and a
    provider that invented structure the document did not supply would be
    manufacturing the evidence this platform exists to check.
    """

    plain = "<div><span>We build technology that helps people connect.</span></div>"

    flat = flatten(plain)

    assert read_regions(plain, flat, 0, len(flat.text)) == ()


def test_a_section_title_begins_the_block_the_filer_typeset_it_in() -> None:
    """What tells a heading from a sentence that mentions it.

    Flattened to prose the two are the same string, so the markup is the
    only place the difference survives.
    """

    markup = "<p>ITEM 7. Management&#8217;s Discussion</p>"

    flat = flatten(markup)

    assert begins_a_block(markup, flat, flat.text.index("ITEM 7."))


def test_a_cross_reference_to_a_section_does_not_begin_a_block() -> None:
    """
    Caterpillar's 10-K names Item 7 inside its forward-looking-statements
    note, with the rest of that sentence typeset ahead of it.
    """

    markup = (
        "<p>The statements under Item 7 "
        "&#8220;Management&#8217;s Discussion&#8221; include "
        "forward-looking statements.</p>"
    )

    flat = flatten(markup)

    assert not begins_a_block(markup, flat, flat.text.index("Item 7"))


def test_a_title_the_filer_typeset_into_a_cell_still_begins_its_block() -> None:
    """A section title in a table cell is a section title.

    Which is why this asks a wider question than `_headings` does: the
    row and the cell open a block as surely as a paragraph.
    """

    markup = "<table><tr><td>ITEM 1. Business</td></tr></table>"

    flat = flatten(markup)

    assert begins_a_block(markup, flat, flat.text.index("ITEM 1."))


# ── spanned words, split tables ─────────────────────────────────────


def test_a_spanned_groups_words_cover_every_column_it_claims() -> None:
    """
    What the colspan the filer wrote asserts. JPMorgan heads six columns
    of figures "Consumer & Community Banking" with one spanned cell, and
    a figure in the sixth is exactly as much that segment's as a figure
    in the first — so the words go into every column the span covers,
    and each column's header is the group it belongs to.
    """

    grouped = """
    <table>
      <tr><td>Year ended December 31,</td>
          <td colspan="3">Consumer Banking</td><td colspan="3">Total</td></tr>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td><td>2023</td>
          <td>2025</td><td>2024</td><td>2023</td></tr>
      <tr><td>Total net revenue</td><td>76,029</td><td>71,507</td><td>70,148</td>
          <td>185,581</td><td>180,593</td><td>162,366</td></tr>
    </table>
    """

    table = read_tables(grouped)[0]

    assert table.header_row == 0
    assert table.column_header(1) == "Consumer Banking"
    assert table.column_header(3) == "Consumer Banking"
    assert table.column_header(4) == "Total"
    assert table.column_header(6) == "Total"


def test_a_spanned_number_is_never_repeated_into_its_columns() -> None:
    """
    A value spanned for centering must not become several addressable
    copies of one printed figure — two segments could then cite the same
    number at two addresses without the duplicate-cell check seeing it.
    """

    centered = """
    <table>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Entertainment</td><td colspan="2">42,466</td></tr>
      <tr><td>Revenues</td><td>94,425</td><td>91,361</td></tr>
    </table>
    """

    table = read_tables(centered)[0]

    assert table.cell(1, 1) == "42,466"
    assert table.cell(1, 2) == ""


def test_a_spanned_title_still_names_the_table_and_no_column() -> None:
    """Caterpillar's shape, preserved through the repetition rule: a
    title is one distinct stretch of words however many columns the
    filer spanned it across."""

    titled = """
    <table>
      <tr><td colspan="3">Sales and Revenues by Segment</td></tr>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Construction Industries</td><td>25,808</td><td>26,414</td></tr>
      <tr><td>Total sales and revenues</td><td>64,809</td><td>67,060</td></tr>
    </table>
    """

    table = read_tables(titled)[0]

    assert table.header_row == 1
    assert table.column_header(1) == "2025"


def test_a_table_split_by_the_page_is_read_as_the_one_table_it_is() -> None:
    """
    JPMorgan's segment results: the table outgrew the page, so the filer
    split it and repeated the label column. The labels are the proof —
    same rows, every label equal pairwise — and the merged table is what
    lets a segment's figure and the firmwide total share a row again,
    which is the relationship the mix contract requires.
    """

    split = """
    <table>
      <tr><td>Year ended December 31,</td><td colspan="2">Consumer Banking</td></tr>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Total net revenue</td><td>76,029</td><td>71,507</td></tr>
      <tr><td>Net income</td><td>4,520</td><td>10,601</td></tr>
    </table>
    <table>
      <tr><td>Year ended December 31,</td><td colspan="2">Total</td></tr>
      <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
      <tr><td>Total net revenue</td><td>185,581</td><td>180,593</td></tr>
      <tr><td>Net income</td><td>57,048</td><td>58,471</td></tr>
    </table>
    """

    tables = read_tables(split)

    assert len(tables) == 1

    table = tables[0]

    assert table.column_header(1) == "Consumer Banking"
    assert table.cell(2, 1) == "76,029"

    # The continuation's columns, to the right of the first table's,
    # with its repeated label column dropped.
    assert table.column_header(3) == "Total"
    assert table.cell(2, 3) == "185,581"


def test_a_repeated_prior_year_table_is_not_a_continuation() -> None:
    """
    Volkswagen's shape, and the case the header gate exists for: the
    2025 segment table and the 2024 segment table print identical row
    labels, and merging them would put two columns called "Pkw und
    leichte Nutzfahrzeuge" in one table. A continuation carries the
    columns the first table had no room for; a repetition carries the
    same columns again, and a header cell the first table already
    prints refuses the merge.
    """

    repeated = """
    <table>
      <tr><td>Mio. EUR</td><td>Pkw</td><td>Nutzfahrzeuge</td></tr>
      <tr><td>Umsatzerloese</td><td>244,484</td><td>42,540</td></tr>
      <tr><td>Segmentergebnis</td><td>4,966</td><td>2,417</td></tr>
    </table>
    <table>
      <tr><td>Mio. EUR</td><td>Pkw</td><td>Nutzfahrzeuge</td></tr>
      <tr><td>Umsatzerloese</td><td>241,526</td><td>46,183</td></tr>
      <tr><td>Segmentergebnis</td><td>13,656</td><td>4,218</td></tr>
    </table>
    """

    assert len(read_tables(repeated)) == 2
