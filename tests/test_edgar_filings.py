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
