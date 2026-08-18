"""A foreign private issuer's annual report, read at its own item numbers.

A 20-F is not a 10-K with different pagination. The SEC prescribes both
sequences and they do not correspond: a domestic filer describes its
business under **Item 1** and reviews it under **Item 7**; a foreign
private issuer describes the same business under **Item 4** —
*Information on the Company* — and reviews it under **Item 5** —
*Operating and Financial Review and Prospects*.

Item 1 of a 20-F is *Identity of Directors, Senior Management and
Advisers*. So asking a 20-F for Item 1 does not merely read the wrong
section: it reads a section about **people** as though it answered *what
does this company do*. Measured before this slice, over the four held
20-F filings, that produced a 156,874-character business description as
**81 characters** of a contents entry, and three others as nothing at
all — none of which the platform could say a word about.

Every case below either pins which items a form is read at, or pins that
reading them cost nothing else.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from app.domain.section_refusal import SectionRefusal
from app.providers.edgar_filings import (
    ANNUAL_SECTION_ITEMS,
    EdgarFilings,
    FilingReference,
)
from app.providers.section_locator import Item

REFERENCE = FilingReference(
    company="Example PLC",
    form="20-F",
    filed_on=date(2026, 3, 13),
    accession="0000000000-26-000002",
    url="https://example.invalid/20f.htm",
)


def filing(document: str, form: str = "20-F"):
    return EdgarFilings()._read(replace(REFERENCE, form=form), document)  # noqa: SLF001


def paragraphs(*blocks: str) -> str:
    typeset = "".join(f"<p>{block}</p>" for block in blocks)

    return f"<html><body>{typeset}</body></html>"


#: Long enough that no anchor inside it is mistaken for a contents entry.
BUSINESS = "The group provides retail banking across its home market. " * 300
REVIEW = "Operating income rose on higher net interest income. " * 300
RISK = "Credit risk could reduce the group's earnings. " * 300


#: A 20-F's item sequence, as the regulator prescribes it and as a filer
#: prints it — first as a contents listing, then as the body.
#:
#: **Both, and in full.** `section_locator` resolves a section through
#: the document's own coherent sequence, so a fixture that lists twenty
#: items and prints four does not merely look unrealistic: the listing
#: becomes the longest coherent chain and wins, which is the defect the
#: locator exists to prevent and not the one this file is about.
ITEMS = (
    (1, "Identity of Directors, Senior Management and Advisers"),
    (2, "Offer Statistics and Expected Timetable"),
    (3, "Key Information"),
    (4, "Information on the Company"),
    (5, "Operating and Financial Review and Prospects"),
    (6, "Directors, Senior Management and Employees"),
    (7, "Major Shareholders and Related Party Transactions"),
    (8, "Financial Information"),
    (9, "The Offer and Listing"),
    (10, "Additional Information"),
    (11, "Quantitative and Qualitative Disclosures About Market Risk"),
    (12, "Description of Securities Other Than Equity Securities"),
)

CONTENTS = tuple(f"Item {number}. {title} {number * 9}" for number, title in ITEMS)


def body(
    *,
    printing: dict[int, str],
    omitting: tuple[int, ...] = (),
) -> tuple[str, ...]:
    """The document's body: every item's heading, with named contents.

    An item in `omitting` is not printed at all, which is how a filing
    that prints one of the two requested sections and not the other is
    built.
    """

    blocks: list[str] = []

    for number, title in ITEMS:
        if number in omitting:
            continue

        blocks.append(f"Item {number}.\xa0{title.upper()}")
        blocks.append(printing.get(number, "Not applicable."))

    return tuple(blocks)


def statement_rows(label: str, count: int = 14) -> str:
    return "".join(
        f"<tr><td>{label} line {i}</td><td>{1000 + i * 37:,}</td>"
        f"<td>{900 + i * 31:,}</td></tr>"
        for i in range(count)
    )


#: The audited run, as a filer typesets it: a title, a table of figures
#: and the notes that follow it, three times over.
STATEMENTS = (
    "<p>CONSOLIDATED STATEMENT OF INCOME</p>"
    f"<table>{statement_rows('Income')}</table>"
    "<p>" + "Notes to the income statement follow. " * 60 + "</p>"
    "<p>CONSOLIDATED BALANCE SHEET</p>"
    f"<table>{statement_rows('Assets')}</table>"
    "<p>" + "Notes to the balance sheet follow. " * 60 + "</p>"
    "<p>CONSOLIDATED STATEMENT OF CASH FLOWS</p>"
    f"<table>{statement_rows('Cash')}</table>"
    "<p>" + "Notes to the cash flow statement follow. " * 60 + "</p>"
)


def printed_20f() -> str:
    """A 20-F that prints its items where the regulator prescribes them."""

    return paragraphs(
        *CONTENTS,
        *body(printing={4: BUSINESS, 5: REVIEW, 6: RISK}),
    )


# ── the mapping ─────────────────────────────────────────────────────


def test_each_form_is_read_at_the_items_its_regulator_prescribes() -> None:
    assert ANNUAL_SECTION_ITEMS["10-K"] == (Item(1), Item(7))
    assert ANNUAL_SECTION_ITEMS["20-F"] == (Item(4), Item(5))


def test_the_mapping_has_no_default_and_no_prefix_match() -> None:
    """A form this platform has not mapped borrows no other form's items.

    The amendments are the case that matters: measured, Barclays' `20-F/A`
    prints only Items 17-18, so reading it at Item 4 would ask a document
    for a section it does not contain and call the answer the company's.
    """

    for unmapped in ("20-F/A", "10-K/A", "20-F ", "20f", "6-K", "8-K", "", "F-1"):
        assert ANNUAL_SECTION_ITEMS.get(unmapped) is None, unmapped

    assert set(ANNUAL_SECTION_ITEMS) == {"10-K", "20-F"}


# ── the reading ─────────────────────────────────────────────────────


def test_a_20_f_is_read_at_item_4_and_item_5() -> None:
    read = filing(printed_20f())

    assert read.business_text.startswith("Item 4.\xa0INFORMATION ON THE COMPANY")
    assert "retail banking across its home market" in read.business_text

    assert read.discussion_text.startswith("Item 5.\xa0OPERATING AND FINANCIAL REVIEW")
    assert "higher net interest income" in read.discussion_text

    assert read.business_refusal is None
    assert read.discussion_refusal is None


def test_a_20_f_business_section_is_not_the_directors_it_lists_first() -> None:
    """The defect this slice removes, stated as what it produced.

    Item 1 of a 20-F is *Identity of Directors, Senior Management and
    Advisers*, and this filing answers it "Not applicable." Read as a
    10-K, that two-word non-answer **is** the business description.
    """

    read = filing(printed_20f())

    assert "Identity of Directors" not in read.business_text
    assert "Not applicable" not in read.business_text


def test_the_whole_item_is_taken_and_not_the_part_before_its_subheadings() -> None:
    """Whole Item 4, closed by the next item — never by a subheading.

    A 20-F's Item 4 is printed in lettered parts (*4.A History and
    Development*, *4.B Business Overview*), and closing on the first of
    them would take the history and leave out what the company does.
    """

    document = paragraphs(
        *CONTENTS,
        *body(
            printing={
                4: "A. History and Development of the Company "
                + "The company was incorporated in 1896. " * 200
                + "B. Business Overview "
                + BUSINESS,
                5: REVIEW,
                6: RISK,
            }
        ),
    )

    read = filing(document)

    assert "incorporated in 1896" in read.business_text
    assert "retail banking across its home market" in read.business_text
    assert "B. Business Overview" in read.business_text

    # And it stops where the next item begins, not later.
    assert "Credit risk" not in read.business_text
    assert "higher net interest income" not in read.business_text


# ── no legacy fallback ──────────────────────────────────────────────


def test_a_20_f_printing_a_10_k_numbering_is_refused_and_never_read_legacily() -> None:
    """The rule that makes the dispatch worth having.

    Falling back to the legacy anchors when Item 4 is absent would read
    this document's Item 1 — its directors — as the business, which is
    exactly the reading the mapping exists to stop. A form is not a hint,
    and an absent section is reported absent.
    """

    document = paragraphs(
        "Item 1.\xa0BUSINESS",
        BUSINESS,
        "Item 1A.\xa0RISK FACTORS",
        RISK,
        "Item 7.\xa0MANAGEMENT'S DISCUSSION AND ANALYSIS",
        REVIEW,
        "Item 7A.\xa0QUANTITATIVE AND QUALITATIVE DISCLOSURES",
        RISK,
    )

    read = filing(document, form="20-F")

    assert read.business_text == ""
    assert read.discussion_text == ""
    assert read.business_refusal is not None
    assert read.discussion_refusal is not None

    # Read as what it actually is, the same bytes yield the sections.
    domestic = filing(document, form="10-K")

    assert "retail banking across its home market" in domestic.business_text
    assert "higher net interest income" in domestic.discussion_text


def test_an_amended_20_f_still_takes_the_legacy_path() -> None:
    """`20-F/A` is a different document and is not dispatched."""

    read = filing(printed_20f(), form="20-F/A")

    assert read.business_refusal is None
    assert read.discussion_refusal is None


# ── the two sections refuse independently ───────────────────────────


def test_one_absent_section_never_refuses_the_other() -> None:
    """A filing may print one and not the other.

    Refusing both because one is missing would report this reader's
    coupling as the filer's silence.
    """

    document = paragraphs(
        *CONTENTS,
        *body(printing={4: BUSINESS, 6: RISK}, omitting=(5,)),
    )

    read = filing(document)

    assert "retail banking across its home market" in read.business_text
    assert read.business_refusal is None

    assert read.discussion_text == ""
    assert read.discussion_refusal is not None
    assert "Item 5" in read.discussion_refusal.observed
    assert read.discussion_refusal.expected == "performance discussion"


def test_a_cross_referenced_20_f_refuses_both_sections_separately() -> None:
    """Barclays' and NatWest's shape, and two refusals rather than one.

    Each names the item it was asked for, so a reader is told which
    section could not be supplied rather than that the document failed.
    """

    document = paragraphs(
        "FORM 20-F CROSS-REFERENCE INDEX Item Number Page",
        "4 Information on the Company 12-104",
        "5 Operating and Financial Review and Prospects 105-240",
        BUSINESS,
    )

    read = filing(document)

    for refused, item, expected in (
        (read.business_refusal, "Item 4", "business description"),
        (read.discussion_refusal, "Item 5", "performance discussion"),
    ):
        assert refused is not None
        assert refused.reason is SectionRefusal.CROSS_REFERENCE_INDEX
        assert refused.expected == expected
        assert refused.form == "20-F"
        assert item in refused.observed
        assert "is available" in refused.stated()

    assert read.business_refusal != read.discussion_refusal
    assert read.business_refusal.stated() != read.discussion_refusal.stated()


# ── the statements are not collateral ───────────────────────────────


def test_a_refused_20_f_section_takes_no_statement_with_it() -> None:
    """The load-bearing result, on the form that now reaches it.

    A 20-F whose sections are represented as page ranges still prints
    audited statements this platform reads perfectly well. The refusal is
    carried on the section; an exception would have taken all three away
    in order to report the first.

    Measured live on the same shape: Barclays and NatWest refuse both
    sections and still yield their income statement and balance sheet.
    """

    document = (
        "<html><body>"
        "<p>FORM 20-F CROSS-REFERENCE INDEX Item Number Page</p>"
        "<p>4 Information on the Company 12-104</p>"
        "<p>5 Operating and Financial Review and Prospects 105-240</p>"
        f"<p>{BUSINESS}</p>" + STATEMENTS + "</body></html>"
    )

    read = filing(document)

    assert read.business_refusal is not None
    assert read.discussion_refusal is not None

    # All three statements survive the refusal, in full.
    assert "CONSOLIDATED STATEMENT OF INCOME" in read.income_statement_text
    assert "CONSOLIDATED BALANCE SHEET" in read.balance_sheet_text
    assert "CONSOLIDATED STATEMENT OF CASH FLOWS" in read.cash_flow_text

    assert read.income_statement_tables
    assert read.balance_sheet_tables
    assert read.cash_flow_tables

    # And they are exactly what the same bytes yield with no refusal at
    # all, so the refusal is not merely survivable but inert here.
    legacy = filing(document, form="8-K")

    assert legacy.business_refusal is None
    assert read.income_statement_text == legacy.income_statement_text
    assert read.balance_sheet_text == legacy.balance_sheet_text
    assert read.cash_flow_text == legacy.cash_flow_text
