"""A section title is not an item suffix.

`_CANDIDATE`'s optional `a`-`c` group is matched case-insensitively, so
without a lexical boundary it takes the first letter of the section's
own title. `Item 1 Business` was discovered as **Item 1B** — and
*Business* is the commonest word to follow *Item 1* in a 10-K.

Honeywell prints `ITEM 1 About Honeywell`, read as Item 1A, so its
Item 1 was never a candidate at all and the resolved sequence began at
1A. Measured over the 24 held annual reports in
`docs/architecture/ANNUAL_SECTION_LOCATION_CORPUS.md`.

Offline. Every case here is a string, because the defect is in one
pattern and the corpus movement it causes is recorded in the report.
"""

from __future__ import annotations

import dataclasses
import pathlib

from app.providers.document_text import flatten
from app.providers.section_locator import Item, candidates, discover, locate, sequence


def only(text: str) -> Item:
    """The single item this text discovers."""

    found = discover(text)

    assert len(found) == 1, (text, [i.stated() for i, _, _ in found])

    return found[0][0]


# ── a title is not a suffix ─────────────────────────────────────────────


def test_a_section_title_is_not_an_item_suffix() -> None:
    """The measured defect, case by case."""

    for text in (
        "Item 1 Business",
        "ITEM 1 BUSINESS",
        "Item 1 Company overview",
        "ITEM 1 About Honeywell",
        "Item 1 Business.",
    ):
        assert only(text) == Item(1), text
        assert only(text).suffix == "", text


def test_the_defect_is_not_specific_to_item_one() -> None:
    """`a`, `b` and `c` begin ordinary words after any item number."""

    assert only("Item 7 Balance sheet discussion") == Item(7)
    assert only("Item 2 Ceased operations") == Item(2)
    assert only("Item 3 Adverse proceedings") == Item(3)


# ── a genuine suffix is still a suffix ──────────────────────────────────


def test_a_bounded_suffix_survives() -> None:
    """Every form the corpus prints, with each terminator it uses."""

    assert only("Item 1A. Risk Factors") == Item(1, "A")
    assert only("ITEM 1A RISK FACTORS") == Item(1, "A")
    assert only("Item 1B. Unresolved Staff Comments") == Item(1, "B")
    assert only("Item 1C. Cybersecurity") == Item(1, "C")
    assert only("Item 7A. Quantitative and Qualitative Disclosures") == Item(7, "A")
    assert only("Item 1A—Risk Factors") == Item(1, "A")
    assert only("Item 1A: Risk Factors") == Item(1, "A")


def test_a_suffix_at_the_very_end_of_the_text_survives() -> None:
    """The lookahead must not require a character to be there at all."""

    assert only("Item 1A") == Item(1, "A")
    assert only("Item 7A") == Item(7, "A")


# ── punctuation never becomes a suffix ──────────────────────────────────


def test_punctuation_does_not_become_a_suffix() -> None:
    for text in ("Item 1. Business", "Item 1: Business", "Item 1 — Business"):
        assert only(text) == Item(1), text


# ── #191's dotted numbering is untouched ────────────────────────────────


def test_the_dotted_fraction_is_unchanged() -> None:
    """Current-report numbering, with the typography #191 measured."""

    for separator in (" ", " ", " ", "\t", "  "):
        text = f"Item{separator}5.02 Departure of Directors or Certain Officers"

        found = discover(text)

        assert found, repr(separator)
        assert found[0][0] == Item(5, fraction="02"), repr(separator)

    assert only("Item 9.01") == Item(9, fraction="01")
    assert only("Item 9.01 Financial Statements and Exhibits") == Item(9, fraction="01")


def test_a_fraction_immediately_followed_by_a_letter_keeps_its_fraction() -> None:
    """Why the guard is bound to the suffix rather than trailed after it.

    Written `([a-c])?(?![A-Za-z])` the lookahead also fires where **no**
    suffix matched, so this backtracks past its own fraction and reads
    as a bare Item 5 — silently undoing #191. Bound to the suffix, the
    constraint applies only to a suffix that actually matched.
    """

    assert only("Item 5.02Departure") == Item(5, fraction="02")


def test_the_annual_report_guards_from_191_still_hold() -> None:
    assert only("Item 1. 10 years ago the company was founded") == Item(1)
    assert only("Item 5. 02 is not a fraction") == Item(5)
    assert only("Item 5.021") == Item(5)
    assert only("Item 16") == Item(16)


def test_the_residual_failures_from_191_remain_residual() -> None:
    """A word split by markup was never handled and still is not.

    `_CANDIDATE` opens on `\\bitem`, so `I tem 5.02` — the three filings
    of 244 that #191 reported as still unlocated — is not discovered.
    This repair neither fixes nor worsens that residual.
    """

    assert discover("I tem 5.02 Departure of Directors") == ()
    assert discover("I tem 1 Business") == ()


# ── offsets, ordering and the dataclass contract ────────────────────────


def test_every_offset_is_where_it_was() -> None:
    """`match.start()` is the item's position, and that is what is used."""

    text = "Preamble. Item 1 Business follows here."

    found = discover(text)

    assert [item for item, _, _ in found] == [Item(1)]
    assert found[0][1] == text.index("Item 1")


def test_the_positional_dataclass_contract_is_unchanged() -> None:
    assert Item(1, "A").suffix == "A"
    assert Item(1, "A").fraction == ""

    fields = [field.name for field in dataclasses.fields(Item)]

    assert fields == ["number", "suffix", "fraction"], fields


def test_item_ordering_is_unchanged() -> None:
    assert Item(1).order < Item(1, "A").order < Item(1, "B").order < Item(2).order
    assert Item(5, fraction="02").order < Item(5, fraction="03").order
    assert Item(5).order < Item(5, fraction="02").order


# ── the sequence resolves through the repair ────────────────────────────


ANNUAL = """
<html><body>
<p><b>ITEM 1 Business</b></p>
<p>{filler}</p>
<p><b>ITEM 1A. Risk Factors</b></p>
<p>{filler}</p>
<p><b>ITEM 1B. Unresolved Staff Comments</b></p>
<p>{filler}</p>
<p><b>ITEM 7 Management's Discussion and Analysis</b></p>
<p>{filler}</p>
<p><b>ITEM 7A. Quantitative and Qualitative Disclosures</b></p>
<p>{filler}</p>
</body></html>
"""


def _annual() -> str:
    return ANNUAL.format(filler="Narrative text. " * 400)


def test_an_unpunctuated_item_one_now_resolves_in_the_sequence() -> None:
    """Honeywell's shape: `ITEM 1 <Title>` with no punctuation.

    Before the guard the sequence began at Item 1A, and Item 1 could not
    be asked for at all.
    """

    markup = _annual()
    flat = flatten(markup)

    run = sequence(tuple(c for c in candidates(markup, flat) if c.is_heading))

    assert [c.item for c in run][:3] == [Item(1), Item(1, "A"), Item(1, "B")]

    section = locate(markup, flat, Item(1))

    assert section is not None
    assert section.closed_by is not None
    assert section.closed_by.item == Item(1, "A")


def test_an_unpunctuated_item_seven_resolves_too() -> None:
    markup = _annual()
    flat = flatten(markup)

    section = locate(markup, flat, Item(7))

    assert section is not None
    assert section.closed_by is not None
    assert section.closed_by.item == Item(7, "A")


# ── the live consumer, and the rewire that remains refused ──────────────


def test_the_statement_locator_still_imports_only_what_it_did() -> None:
    """`statement_locator` is the one live consumer of this module.

    It takes the structural scoring and none of the names this repair
    touches, which is why no statement, consensus or band can move.
    """

    source = pathlib.Path("app/providers/statement_locator.py").read_text()

    assert "from app.providers.section_locator import Evidence, observe" in source

    for name in ("discover", "candidates", "sequence", "locate(", "_CANDIDATE"):
        assert f"section_locator.{name}" not in source, name


def test_the_annual_report_reader_uses_this_module_for_the_mapped_forms() -> None:
    """Superseded: the rewire was refused when this was written, then ruled.

    The suffix guard this file tests is now load-bearing on the annual
    path rather than merely adjacent to it — `Item 1 Business` being
    discovered as `Item 1B` would break the very readings the cutover
    corrects. The assertion is inverted to say so, and the 20-F dispatch
    widens what depends on it: `Item 4` must not be discovered as
    `Item 4B`, which a 20-F prints (*4.B Business Overview*).
    """

    from app.providers.edgar_filings import ANNUAL_SECTION_ITEMS

    source = pathlib.Path("app/providers/edgar_filings.py").read_text()

    assert "section_locator" in source
    assert set(ANNUAL_SECTION_ITEMS) == {"10-K", "20-F"}
