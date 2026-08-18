"""Locating the sections of a 10-K, in the structure the filer typeset."""

import pathlib
from dataclasses import replace
from datetime import date

import pytest

from app.providers.edgar_filings import EdgarFilings, Filing, FilingReference

REFERENCE = FilingReference(
    company="Example Corp",
    form="10-K",
    filed_on=date(2026, 2, 13),
    accession="0000000000-26-000001",
    url="https://example.invalid/10k.htm",
)


def read(document: str, form: str = "10-K") -> Filing:
    """The sections this platform reads out of one filing's markup.

    The form is a parameter because the reader now has two paths: exactly
    `10-K` goes through `section_locator`, and everything else keeps the
    literal reader. A test that means one of them says which.
    """

    return EdgarFilings()._read(replace(REFERENCE, form=form), document)


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


#: Two contents entries over a body. Kept because it is the shape the
#: legacy reader was built against, and it is now read by two different
#: rules depending on the form.
TWO_ENTRY_CONTENTS = """\
<html><body>
<p>ITEM 1. Business 4</p>
<p>ITEM 1A. Risk Factors 12</p>
<p>ITEM 1. Business</p>
<p>The Company makes machines and sells them worldwide.</p>
<p>ITEM 1A. Risk Factors</p>
</body></html>
"""


def test_the_legacy_reader_still_prefers_the_section_over_its_entry() -> None:
    """
    Structure alone does not settle it — a table of contents is typeset
    as headings too. What separates the entry from the section it points
    at, *for the legacy reader*, is that it runs a few characters to its
    neighbour.

    Read under a form the cutover does not claim, because that reader is
    still what every non-`10-K` filing gets.
    """

    assert "makes machines" in read(TWO_ENTRY_CONTENTS, form="20-F").business_text


def test_a_two_entry_listing_is_below_the_measured_listing_threshold() -> None:
    """The locator's honest residual, pinned rather than hidden.

    `section_locator` sets a contents entry aside when at least six
    further items follow it in one chain — the band measured in
    `CONTENTS_BODY_HEADING_SELECTION.md`, where every real contents
    listing in the 24-filing corpus runs 12 to 22 entries. A listing of
    **two** is far below that, so the entry is not set aside and width
    decides, exactly as it did before the selector existed.

    A 10-K lists Items 1 through 16, so no filing in the corpus prints a
    two-entry listing and this shape has never been observed. It is
    recorded here so that the residual is a known property of the
    threshold rather than a surprise: **the cutover inherits it from a
    ruled selector rather than introducing it.**
    """

    filing = read(TWO_ENTRY_CONTENTS, form="10-K")

    # The entry is selected and closed at the entry beside it, so the
    # section is the listing line alone. At this scale every step is
    # under the width floor, so nothing separates the two readings and
    # the earlier one wins the tie.
    assert filing.business_text == "ITEM 1. Business 4"
    assert "makes machines" not in filing.business_text


def test_a_realistic_listing_sends_the_10_k_reader_to_the_body() -> None:
    """Six chained entries is a listing, and the body opens the section."""

    entries = "".join(
        f"<p>ITEM {number}. Heading {number}</p>"
        for number in ("1", "1A", "1B", "1C", "2", "3", "4")
    )
    sections = "".join(
        f"<p>ITEM\xa0{number}. HEADING</p><p>{'Section prose. ' * 300}</p>"
        for number in ("1", "1A", "1B", "1C", "2", "3", "4")
    )

    filing = read(f"<html><body>{entries}{sections}</body></html>", form="10-K")

    assert filing.business_text.startswith("ITEM\xa01. HEADING")
    assert "Heading 1A" not in filing.business_text, "a contents entry opened it"


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


# ── a reference is followed only where content was displaced ─────────

#: Capital One's shape, reduced. Every gate that existed passed: the
#: filer really writes `under the headings`, the quoted heading really
#: begins exactly one block, and it really does point out of Item 1 — so
#: 80,000 characters of risk factors were appended to a business
#: description. What was missing was any test of the *relationship*.
DIRECTING = """\
<html><body>
<p>ITEM 1. Business</p>
<p>The Company issues credit cards and takes deposits. For more
information about technology, data protection and data security, and
related risks for our business, see &#8220;Item 1A. Risk
Factors&#8221; under the headings &#8220;We face risks related to our
operational infrastructure&#8221; and &#8220;A cyber-attack could
disrupt us&#8221;.</p>
<p>ITEM 1A. Risk Factors</p>
<p>{padding}</p>
<p>We face risks related to our operational infrastructure</p>
<p>Our ability to retain and attract customers depends on technology we
must operate and adapt in a rapidly changing environment.</p>
</body></html>
""".format(padding="filler " * 200)


def test_a_clause_that_only_directs_the_reader_appends_nothing() -> None:
    """`see X under the heading Y` is a cross-reference, not displacement.

    The defect the 10-K locator cutover exposed: correcting Capital One's
    business span from 17,165 characters to its true 84,268 brought this
    sentence inside it, and every existing gate passed.
    """

    filing = read(DIRECTING, form="10-K")

    assert "issues credit cards" in filing.business_text
    assert "retain and attract customers" not in filing.business_text
    assert "rapidly changing environment" not in filing.business_text


def test_a_clause_that_states_the_content_is_elsewhere_still_appends() -> None:
    """JPMorgan's shape. `is provided in … under the heading` displaces."""

    filing = read(REFERRING, form="10-K")

    assert "two reportable business segments" in filing.business_text
    assert "offers deposit and lending products" in filing.business_text


def clause(sentence: str) -> str:
    """One filing whose Item 1 carries exactly the sentence given."""

    return f"""\
<html><body>
<p>ITEM 1. Business</p>
<p>The Firm has two segments. {sentence}</p>
<p>ITEM 1A. Risk Factors</p>
<p>{"filler " * 200}</p>
<p>SEGMENT RESULTS</p>
<p>Consumer Banking offers deposit products through branches.</p>
</body></html>
"""


def follows(sentence: str) -> bool:
    return (
        "offers deposit products" in read(clause(sentence), form="10-K").business_text
    )


def test_a_directing_cue_after_a_displacement_cue_refuses() -> None:
    """The nearest cue governs, not any cue in the sentence.

    A single sentence carries more than one clause, and the displacement
    verb here belongs to a different one. Asking whether a displacement
    verb appeared *somewhere* would follow this reference and append the
    risk factors — Capital One's defect, one clause further along.
    """

    assert not follows(
        "Results are presented in Note 2, and for risks see the disclosures "
        "under the heading &#8220;Segment Results&#8221;."
    )


def test_a_displacement_cue_after_a_directing_cue_still_follows() -> None:
    """The earlier clause directs; the one that governs displaces."""

    assert follows(
        "For additional background see Note 2; the segment descriptions are "
        "provided in MD&amp;A under the heading &#8220;Segment Results&#8221;."
    )


def test_a_reference_with_no_relationship_cue_at_all_refuses() -> None:
    """M&T's shape: a website navigation label, not a document reference."""

    assert not follows(
        "The Company also makes available on its website, under the heading "
        "&#8220;Segment Results&#8221;, certain governance documents."
    )


@pytest.mark.parametrize(
    "cue",
    ["refer to", "referred to", "please see", "see"],
)
def test_every_directing_cue_the_contract_names_refuses(cue) -> None:
    assert not follows(
        f"The segment descriptions are provided in Note 2, and {cue} the "
        "disclosures under the heading &#8220;Segment Results&#8221;."
    )


@pytest.mark.parametrize(
    "verb",
    ["is provided in", "are presented in", "is included in", "are set forth in"],
)
def test_every_displacement_verb_the_contract_names_is_accepted(verb) -> None:
    document = f"""\
<html><body>
<p>ITEM 1. Business</p>
<p>The Firm has two segments. A description of them {verb} the
Management&#8217;s discussion and analysis section under the heading
&#8220;Segment Results&#8221;.</p>
<p>ITEM 1A. Risk Factors</p>
<p>{"filler " * 200}</p>
<p>SEGMENT RESULTS</p>
<p>Consumer Banking offers deposit products through branches.</p>
</body></html>
"""

    assert "offers deposit products" in read(document, form="10-K").business_text


def test_a_verb_in_a_neighbouring_sentence_is_not_evidence() -> None:
    """The assertion is a sentence's, and a character window cannot tell.

    Measured over the four references the 20-company cohort prints: the
    nearest displacement verb is 171 characters back for JPMorgan, which
    should be followed, and 216 back for M&T, which should not — its verb
    belongs to a different sentence about its own website. Any window
    wide enough for the first admits the second.
    """

    document = f"""\
<html><body>
<p>ITEM 1. Business</p>
<p>The Firm has two segments. A description of our people is provided in
our sustainability report. The Company also makes available on its
website, under the heading &#8220;Segment Results&#8221;, certain
governance documents.</p>
<p>ITEM 1A. Risk Factors</p>
<p>{"filler " * 200}</p>
<p>SEGMENT RESULTS</p>
<p>Consumer Banking offers deposit products through branches.</p>
</body></html>
"""

    assert "offers deposit products" not in read(document, form="10-K").business_text


def test_a_sentence_wrapped_across_lines_is_still_one_sentence() -> None:
    """A single newline is a wrap, not a sentence end.

    `_REFERRED` is whitespace-tolerant for exactly this reason, and the
    flattened prose keeps the filer's line breaks. Treating a lone
    newline as a boundary refused the mechanism's own calibration
    fixture, whose clause wraps twice.
    """

    document = f"""\
<html><body>
<p>ITEM 1. Business</p>
<p>The Firm has two segments. A description of them is provided in the
Management&#8217;s discussion and analysis section of this Form 10-K
under
the heading &#8220;Segment Results&#8221;.</p>
<p>ITEM 1A. Risk Factors</p>
<p>{"filler " * 200}</p>
<p>SEGMENT RESULTS</p>
<p>Consumer Banking offers deposit products through branches.</p>
</body></html>
"""

    assert "offers deposit products" in read(document, form="10-K").business_text


def test_the_gate_reads_no_section_name_and_no_company() -> None:
    """No literal `Risk Factors`, no width rule, no allowlist.

    Three repairs the ruling forbade, asserted against what the module
    *executes* rather than against its text — the prose above the gate
    quotes Capital One's own sentence in order to explain the defect, and
    a substring search over the whole file would call that explanation a
    violation.
    """

    import ast

    tree = ast.parse(pathlib.Path("app/providers/edgar_filings.py").read_text())

    docstrings = set()

    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            doc = ast.get_docstring(node, clean=False)

            if doc is not None:
                docstrings.add(doc)

    executed = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    ]

    for forbidden in ("risk factor", "capital one", "jpmorgan", "cof", "jpm"):
        offenders = [text for text in executed if forbidden in text.casefold()]

        assert offenders == [], f"{forbidden!r} is executed: {offenders}"

    # And the cap the ruling protected has not been quietly lowered.
    from app.providers.edgar_filings import _FOLLOWED_WIDEST

    assert _FOLLOWED_WIDEST == 80_000
