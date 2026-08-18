"""The other numbering a regulator uses, and the path it may not disturb.

An annual report numbers its items `1`, `1A`, `7A`. A current report
numbers them `1.01`, `5.02`, `9.01`. Both are "Item N" to a reader, and
only the first was expressible — so `Item 5.02` was discovered as
`Item 5` with the fraction thrown away, and a section keyed on it could
not be asked for at all.

Everything here is offline. The corpus measurement that earned the change
is in `docs/architecture/ITEM_HEADING_LOCATION.md`; this pins the
contract and the inertness.
"""

from __future__ import annotations

import pathlib

from app.providers.document_text import flatten
from app.providers.section_locator import Item, candidates, discover, locate, sequence

# ── the existing contract, unmoved ──────────────────────────────────────


def test_a_positional_second_argument_is_still_the_suffix() -> None:
    """`Item(1, "A")` meant a suffix before the fraction existed.

    The field is last for exactly this reason. A new field inserted
    ahead of an existing one silently changes what every positional call
    means, and no type checker sees it — both are `str`.
    """

    assert Item(1, "A").suffix == "A"
    assert Item(1, "A").fraction == ""
    assert Item(1, "A").stated() == "Item 1A"


def test_an_annual_report_item_has_no_fraction_rather_than_a_zero_one() -> None:
    assert Item(7).fraction == ""
    assert Item(7).stated() == "Item 7"
    assert Item(5, fraction="02").stated() == "Item 5.02"


def test_the_order_that_makes_1_then_1a_then_2_a_fact_is_unchanged() -> None:
    assert Item(1).order < Item(1, "A").order < Item(1, "B").order < Item(2).order


def test_a_current_report_orders_by_its_fraction() -> None:
    """5.02 < 5.03 < 7.01, and a bare Item 5 precedes its own sub-items."""

    assert Item(5, fraction="02").order < Item(5, fraction="03").order
    assert Item(5, fraction="03").order < Item(7, fraction="01").order
    assert Item(5).order < Item(5, fraction="02").order

    # Compared as the two printed digits, which is the same ordering
    # without inventing a value: "01" < "02" < "10".
    assert Item(9, fraction="01").order < Item(9, fraction="10").order


# ── discovery ───────────────────────────────────────────────────────────


def test_the_fraction_is_read_where_the_filer_prints_one() -> None:
    found = discover("Item 5.02 Departure of Directors or Certain Officers")

    assert [item for item, _, _ in found] == [Item(5, fraction="02")]


def test_it_is_read_through_the_typography_a_filer_actually_uses() -> None:
    """Non-breaking and thin spaces are what made 18% unreadable.

    Measured on 231 filings: 28 use `U+00A0`, 11 use `U+2009`. Both are
    presentation, and `\\s` has always covered them — the fraction is
    what was missing.
    """

    for separator in (" ", " ", " ", "\t", "  "):
        found = discover(f"Item{separator}5.02 Departure of Directors")

        assert [item for item, _, _ in found] == [Item(5, fraction="02")], separator


def test_an_annual_report_heading_gains_no_fraction() -> None:
    """The dot must touch the number and exactly two digits must follow.

    This pattern governs the annual-report path too, so a full stop
    followed by prose — or by a number that is part of a sentence — must
    read exactly as it did.
    """

    unchanged = {
        "Item 1. Business": Item(1),
        "Item 1.": Item(1),
        "Item 1A. Risk Factors": Item(1, "A"),
        "Item 7A. Quantitative Disclosures": Item(7, "A"),
        "Item 1. 10 years ago the company was founded": Item(1),
        "Item 5. 02 is not a fraction": Item(5),
        "Item 16": Item(16),
    }

    for text, expected in unchanged.items():
        found = discover(text)

        assert found[0][0] == expected, text
        assert found[0][0].fraction == "", text


def test_a_third_digit_is_not_a_fraction() -> None:
    found = discover("Item 5.021")

    assert found[0][0] == Item(5)


# ── it resolves a real current report ───────────────────────────────────


EIGHT_K = """
<html><body>
<p>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</p>
<p>FORM 8-K</p>
<p><b>Item&#160;2.02 Results of Operations and Financial Condition.</b></p>
<p>{filler}</p>
<p><b>Item&#160;5.02 Departure of Directors or Certain Officers.</b></p>
<p>On March 9, 2026, the registrant announced a leadership change.</p>
<p>{filler}</p>
<p><b>Item&#160;9.01 Financial Statements and Exhibits.</b></p>
<p>{filler}</p>
</body></html>
"""


def _document() -> str:
    return EIGHT_K.format(filler="Narrative text. " * 60)


def test_the_section_can_now_be_asked_for_at_all() -> None:
    markup = _document()
    flat = flatten(markup)

    section = locate(markup, flat, Item(5, fraction="02"))

    assert section is not None
    assert "leadership change" in flat.text[section.at : section.ends]

    # It closes at the next peer the document prints, not at the end.
    assert section.closed_by is not None
    assert section.closed_by.item == Item(9, fraction="01")


def test_the_sequence_runs_in_the_current_report_s_own_order() -> None:
    markup = _document()
    flat = flatten(markup)

    run = sequence(tuple(one for one in candidates(markup, flat) if one.is_heading))

    assert [one.item for one in run] == [
        Item(2, fraction="02"),
        Item(5, fraction="02"),
        Item(9, fraction="01"),
    ]


def test_asking_for_an_item_the_document_does_not_carry_returns_nothing() -> None:
    markup = _document()

    assert locate(markup, flatten(markup), Item(5, fraction="07")) is None


# ── inertness ───────────────────────────────────────────────────────────


def test_the_annual_report_path_cannot_reach_this_module() -> None:
    """`edgar_filings` locates its sections with its own literal rule.

    Which is why this change cannot move `business_text` or
    `discussion_text` for any company. Rewiring that path is a separate
    question with a separately measured blast radius — 26 of 48 section
    reads move and one is lost — and is recorded in the report rather
    than taken here.
    """

    source = pathlib.Path("app/providers/edgar_filings.py").read_text()

    assert "section_locator" not in source


def test_statement_location_cannot_reach_the_changed_names() -> None:
    """The one live consumer imports the two things this did not touch.

    `statement_locator` takes `Evidence` and `observe` — the structural
    scoring — and none of `discover`, `Item`, `candidates`, `sequence`
    or `locate`. So no statement, no consensus and no band can move.
    """

    source = pathlib.Path("app/providers/statement_locator.py").read_text()

    assert "from app.providers.section_locator import Evidence, observe" in source

    for name in ("discover", "candidates", "sequence", "locate(", "Item("):
        assert f"section_locator.{name}" not in source, name


def test_nothing_consumes_the_new_numbering_yet() -> None:
    """Named and acquirable, and wired to no reader.

    The consumer is the transition-extraction measurement that comes
    next, and it is not built. Until it is, a fraction is a thing this
    locator can express and nothing asks it for.
    """

    consumers = [
        path
        for path in pathlib.Path("app").rglob("*.py")
        if "fraction=" in path.read_text() and path.name != "section_locator.py"
    ]

    assert consumers == [], [str(path) for path in consumers]
