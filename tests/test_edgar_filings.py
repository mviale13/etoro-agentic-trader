"""Locating the sections of a 10-K, in the structure the filer typeset."""

from datetime import date

from app.providers.edgar_filings import EdgarFilings, Filing, FilingReference

REFERENCE = FilingReference(
    company="Example Corp",
    form="10-K",
    filed_on=date(2026, 2, 13),
    accession="0000000000-26-000001",
    url="https://example.invalid/10k.htm",
)


def read(document: str) -> Filing:
    """The sections this platform reads out of one filing's markup."""

    return EdgarFilings()._read(REFERENCE, document)


#: The shape that cost Caterpillar its segment sizes. A sentence in the
#: forward-looking-statements note mentions Item 7, and the span from
#: that sentence to the next closing heading is *wider* than Item 7
#: itself — so width alone chose the wrong section, and the wrong
#: section prints none of the tables the sizes are measured from.
CROSS_REFERENCED = """\
<html><body>
<p>ITEM 1. Business</p>
<p>The Company makes machines.</p>
<p>ITEM 1A. Risk Factors</p>
<p>The statements under Item 7 &#8220;Management&#8217;s Discussion and
Analysis of Financial Condition and Results of Operations&#8221; include
forward-looking statements.</p>
<p>{padding}</p>
<p>ITEM 7. Management&#8217;s Discussion and Analysis of Financial
Condition and Results of Operations</p>
<p>The following table presents revenues from our operating segments:</p>
<table>
  <tr><td>($ in millions)</td><td>2025</td></tr>
  <tr><td>Construction Industries</td><td>25,808</td></tr>
  <tr><td>Resource Industries</td><td>11,235</td></tr>
  <tr><td>Total sales and revenues</td><td>64,809</td></tr>
</table>
<p>ITEM 8. Financial Statements</p>
</body></html>
""".format(padding="filler " * 400)


def test_a_section_is_located_where_the_filer_typeset_its_title() -> None:
    """
    And not at the widest span, which is not a property of a section.

    Caterpillar's 10-K mentions Item 7 in a sentence, and the span from
    that sentence to Item 8 is wider than Item 7 is. Width chose it, and
    the platform read forty-five thousand characters of the wrong
    section — reporting the sizes printed in the right one as absent
    from the filing.
    """

    filing = read(CROSS_REFERENCED)

    assert filing.discussion_text.startswith("ITEM 7.")
    assert "forward-looking statements" not in filing.discussion_text


def test_locating_the_section_is_what_puts_its_tables_within_reach() -> None:
    """The whole reason this matters: a size is read out of a cell."""

    assert len(read(CROSS_REFERENCED).discussion_tables) == 1


def test_a_contents_entry_begins_a_block_and_still_loses_to_the_section() -> None:
    """
    Structure alone does not settle it — a table of contents is typeset
    as headings too. What separates the entry from the section it points
    at is that it runs a few characters to its neighbour.
    """

    contents = """\
<html><body>
<p>ITEM 1. Business 4</p>
<p>ITEM 1A. Risk Factors 12</p>
<p>ITEM 1. Business</p>
<p>The Company makes machines and sells them worldwide.</p>
<p>ITEM 1A. Risk Factors</p>
</body></html>
"""

    assert "makes machines" in read(contents).business_text


def test_a_document_with_no_structure_is_read_by_width_as_before() -> None:
    """
    The same order of preference the narrative evidence uses: structure
    first, position behind it. A filing whose markup offers nothing to
    read is read the old way rather than left unread.
    """

    unstructured = (
        "ITEM 1. Business 4 ITEM 1A. Risk Factors 12 "
        "ITEM 1. Business The Company makes machines. "
        "ITEM 1A. Risk Factors Machines can break."
    )

    assert "makes machines" in read(unstructured).business_text


def test_a_section_the_filing_only_points_at_is_read_as_what_it_says() -> None:
    """
    JPMorgan's Item 7 is 395 characters naming the pages of a document
    filed separately. That is the section, correctly located, and it
    prints no tables — which is a fact about where the figures live
    rather than about whether the company reports them.
    """

    pointer = """\
<html><body>
<p>Item 7. Management&#8217;s Discussion and Analysis of Financial
Condition and Results of Operations.</p>
<p>Management&#8217;s discussion and analysis appears on pages 46-160.</p>
<p>Item 8. Financial Statements</p>
</body></html>
"""

    filing = read(pointer)

    assert "pages 46-160" in filing.discussion_text
    assert filing.discussion_tables == ()


# ── a section that says its content is printed elsewhere ────────────
#
# JPMorgan's shape. Item 1 names the segments and then states, in the
# filer's own words, that what they do is provided in the MD&A under a
# heading it quotes. Reading Item 1 alone saw the names and no
# descriptions, and every reading honestly reported that the filing
# described nothing — eighty pages from where it described them.

REFERRING = """\
<html><body>
<p>ITEM 1. Business</p>
<p>The Firm has two reportable business segments &#8212; Consumer Banking
(&#8220;CB&#8221;) and Investment Bank (&#8220;IB&#8221;). A description of
the Firm&#8217;s reportable business segments is provided in the
Management&#8217;s discussion and analysis section of this Form 10-K under
the heading &#8220;Business Segment Results,&#8221; which begins on page
46.</p>
<p>ITEM 1A. Risk Factors</p>
<p>{padding}</p>
<p>BUSINESS SEGMENT RESULTS</p>
<p>Consumer Banking offers deposit and lending products to consumers
through bank branches.</p>
<p>Investment Bank offers advisory, capital-raising and market-making
services to institutional clients.</p>
<table>
  <tr><td>($ in millions)</td><td>2025</td></tr>
  <tr><td>Consumer Banking</td><td>25,808</td></tr>
  <tr><td>Investment Bank</td><td>11,235</td></tr>
  <tr><td>Total net revenue</td><td>64,809</td></tr>
</table>
</body></html>
""".format(padding="filler " * 200)


def test_a_referenced_chapter_is_read_where_the_filer_says_it_is() -> None:
    """
    The address is the filer's own. This platform does not guess what a
    section might be called: it reads the heading the document quotes.
    """

    filing = read(REFERRING)

    # Both, never one instead of the other: the section that referred is
    # where the segments are named, and the referenced chapter is where
    # the filing says what they do.
    assert "two reportable business segments" in filing.business_text
    assert "offers deposit and lending products" in filing.business_text
    assert "advisory, capital-raising and market-making" in filing.business_text


def test_a_pointer_discussion_is_served_the_referenced_chapters_tables() -> None:
    """
    The pointer shape, closed. JPMorgan's Item 7 is 395 characters
    naming the pages its discussion appears on and prints no table; the
    figures are in the chapter Item 1's reference already located. An
    earlier pass declined these tables because the size reading could
    not survive their shape — the parse now reads a spanned group
    header as covering its columns and a page-split table as one table,
    so the decline is over on evidence rather than on hope.

    REFERRING's Item 7 is absent entirely, which is the same shape:
    the discussion contributes no tables of its own.
    """

    (table,) = read(REFERRING).discussion_tables

    assert any("Total net revenue" in row.label for row in table.rows)


def test_a_discussion_with_its_own_tables_keeps_exactly_those() -> None:
    """Mixing another chapter's tables in beside a discussion's own
    would put two tables' totals in one reading's reach."""

    referring_with_own = REFERRING.replace(
        "</body></html>",
        """<p>ITEM 7. Management&#8217;s Discussion and Analysis</p>
<table>
  <tr><td>(in millions)</td><td>2025</td></tr>
  <tr><td>Own Section Revenue</td><td>1,234</td></tr>
  <tr><td>Own Total</td><td>5,678</td></tr>
</table>
<p>ITEM 8. Financial Statements</p>
</body></html>""",
    )

    tables = read(referring_with_own).discussion_tables

    assert len(tables) == 1
    assert any("Own Total" in row.label for row in tables[0].rows)


def test_the_referenced_chapter_keeps_its_regions_in_the_joined_text() -> None:
    """
    Structural ownership is checked against the text the reader is
    given. Regions carried across unshifted would place every heading at
    the wrong end of the document and quietly hand each segment
    another's words.
    """

    filing = read(REFERRING)

    for region in filing.business_regions:
        assert filing.business_text[region.at : region.ends].strip()
        assert region.at <= len(filing.business_text)


def test_an_ambiguous_reference_is_refused_rather_than_chosen_between() -> None:
    """
    The same rule `owning` applies, refused for the same reason: where
    two regions could answer, none does. Measured on the filing that
    earned this — Item 7's reference to "Management's discussion and
    analysis" resolves to forty-two blocks, and is declined.
    """

    ambiguous = """\
<html><body>
<p>ITEM 1. Business</p>
<p>The Company makes machines. A description is provided under the
heading &#8220;Segment Results.&#8221;</p>
<p>ITEM 1A. Risk Factors</p>
<p>SEGMENT RESULTS</p>
<p>The first chapter of that name.</p>
<p>SEGMENT RESULTS</p>
<p>The second chapter of that name.</p>
</body></html>
"""

    filing = read(ambiguous)

    assert "makes machines" in filing.business_text
    assert "first chapter" not in filing.business_text
    assert "second chapter" not in filing.business_text


def test_a_filing_that_refers_to_nothing_is_read_exactly_as_before() -> None:
    """The mechanism costs nothing where a filer describes its segments
    in the section the reader was already given."""

    filing = read(CROSS_REFERENCED)

    assert "The Company makes machines." in filing.business_text
    assert "operating segments" not in filing.business_text


#: The shape of an annual report's financial section: the statements
#: listed in an index, mentioned in the auditor's report, and printed
#: under their own titles — with the income statement closed by the
#: statement that follows it.
STATEMENTS = """\
<html><body>
<p>Consolidated statements of income 152</p>
<p>Consolidated statements of comprehensive income 153</p>
<p>Report of Independent Registered Public Accounting Firm</p>
<p>We have audited the consolidated statements of income of Example
Corp and the related notes.</p>
<p>Consolidated statements of income</p>
<table>
  <tr><td>(in millions)</td><td>2025</td><td>2024</td></tr>
  <tr><td>Investment banking fees</td><td>8,415</td><td>7,124</td></tr>
  <tr><td>Principal transactions</td><td>27,411</td><td>24,268</td></tr>
  <tr><td>Lending- and deposit-related fees</td><td>7,608</td><td>7,340</td></tr>
  <tr><td>Asset management fees</td><td>19,353</td><td>17,201</td></tr>
  <tr><td>Total noninterest revenue</td><td>85,201</td><td>78,143</td></tr>
  <tr><td>Net interest income</td><td>92,218</td><td>84,735</td></tr>
  <tr><td>Total net revenue</td><td>177,419</td><td>162,878</td></tr>
  <tr><td>Compensation expense</td><td>46,678</td><td>42,213</td></tr>
  <tr><td>Total noninterest expense</td><td>91,313</td><td>87,172</td></tr>
  <tr><td>Income before income tax expense</td><td>72,106</td><td>61,610</td></tr>
  <tr><td>Net income</td><td>58,471</td><td>49,552</td></tr>
</table>
<p>Consolidated statements of comprehensive income</p>
<p>Other comprehensive income was as follows.</p>
</body></html>
"""


def test_the_income_statement_is_located_where_its_title_is_typeset() -> None:
    """
    The structural-section rule's third application. The index entry
    and the auditor's mention both carry the title; only the section's
    own heading begins a block wide enough to be the statement.
    """

    filing = read(STATEMENTS)

    assert filing.income_statement_text.startswith("Consolidated statements of income")
    assert "Total net revenue" in filing.income_statement_text
    assert "Other comprehensive income" not in filing.income_statement_text


def test_locating_the_statement_puts_its_table_within_reach() -> None:
    """The whole reason this matters: a figure is read out of a cell."""

    tables = read(STATEMENTS).income_statement_tables

    assert len(tables) == 1

    labels = [row.label for row in tables[0].rows]

    assert "Total net revenue" in labels
    assert "Net income" in labels


def test_a_filing_without_statements_leaves_them_unstated() -> None:
    filing = read(CROSS_REFERENCED)

    assert filing.income_statement_text == ""
    assert filing.income_statement_tables == ()
