"""A section boundary is an interpretation, not a string match.

Every case below is a shape a real filing in the acceptance corpus
prints, reduced to the smallest markup that reproduces it. The
companies are named because the slice was earned by measuring them.
"""

from app.providers.document_text import flatten
from app.providers.section_locator import (
    Item,
    candidates,
    discover,
    locate,
    sequence,
)


def located(markup: str, number: int, suffix: str = ""):
    flat = flatten(markup)

    return locate(markup, flat, Item(number=number, suffix=suffix))


def body(text: str) -> str:
    """Filler wide enough that a section reads as a section."""

    return f"<p>{text * 400}</p>"


# ── discovery: typography may be normalised away ────────────────────


def test_discovery_ignores_how_the_heading_was_typeset() -> None:
    """Amazon prints a non-breaking space, Boeing two, Danaher capitals.

    Every one of these was invisible to a literal match, and every one
    of them cost the company its entire business section.
    """

    typeset = (
        "Item 1. Business",
        "Item\xa01. Business",
        "Item\xa0\xa01. Business",
        "ITEM 1. BUSINESS",
        "Item  1.  Business",
        "item 1: business",
    )

    for printed in typeset:
        found = discover(printed)

        assert found, f"{printed!r} was not discovered"
        assert found[0][0] == Item(1), printed


def test_discovery_orders_items_the_way_a_filing_does() -> None:
    assert Item(1).order < Item(1, "A").order < Item(1, "B").order < Item(2).order
    assert Item(7).order < Item(7, "A").order < Item(8).order


# ── the first invariant: typography alone establishes nothing ───────


def test_a_typographic_difference_alone_does_not_make_a_boundary() -> None:
    """
    The invariant, held directly. The same characters appear twice —
    once as a heading the filer typeset, once inside a sentence — and
    only one of them may close a section, however it is spaced.
    """

    markup = (
        "<p>ITEM\xa01. BUSINESS</p>"
        + body("The company makes machines. ")
        + "<p>The relevant risks are set forth in Item\xa01A. Risk Factors "
        "of this report.</p>"
        + body("More business description follows the reference. ")
        + "<p>ITEM\xa01A. RISK FACTORS</p>"
        + body("Machines can break. ")
    )

    section = located(markup, 1)

    assert section is not None
    assert section.closed_by is not None
    # Closed by the heading, not by the sentence that mentioned it.
    assert section.closed_by.at > markup.find("More business description")
    assert (
        "More business description" in flatten(markup).text[section.at : section.ends]
    )


def test_a_prose_cross_reference_is_observed_as_one() -> None:
    """Disney's case: '...are set forth in Item 1A' must not close Item 1."""

    markup = (
        "<p>Item 1. Business</p>"
        + body("What the company does. ")
        + "<p>Risks are set forth in Item 1A of this report.</p>"
        + "<p>Item 1A. Risk Factors</p>"
        + body("The risks. ")
    )

    flat = flatten(markup)
    mentions = [
        candidate
        for candidate in candidates(markup, flat)
        if candidate.item == Item(1, "A")
    ]

    assert len(mentions) == 2

    reference, heading = sorted(mentions, key=lambda candidate: candidate.at)

    assert not reference.is_heading
    assert heading.is_heading
    assert any(
        "reference, not a title" in seen.observation for seen in reference.evidence
    )


# ── the second invariant: a closing needs structure and coherence ───


def test_the_contents_listing_loses_to_the_body_it_points_at() -> None:
    """
    Danaher's case. The table of contents is a perfectly ordered run of
    items — it cannot be rejected by ordering, and it is not rejected
    by typography either. What separates it from the body is that its
    steps are a few characters wide where the body's are thousands.
    """

    markup = (
        "<p>Item 1. Business 3</p>"
        "<p>Item 1A. Risk Factors 15</p>"
        "<p>Item 2. Properties 30</p>"
        "<p>ITEM\xa01. BUSINESS</p>"
        + body("What the company actually does. ")
        + "<p>ITEM\xa01A. RISK FACTORS</p>"
        + body("The risks. ")
        + "<p>ITEM\xa02. PROPERTIES</p>"
        + body("The properties. ")
    )

    section = located(markup, 1)

    assert section is not None
    assert (
        "What the company actually does"
        in flatten(markup).text[section.at : section.ends]
    )
    # The contents entry is reported as considered and not selected.
    assert section.rejected


def test_a_section_closes_at_the_next_peer_not_the_next_mention() -> None:
    """
    Caterpillar's case, which the over-read exposed: Item 7 is mentioned
    inside the forward-looking-statements note long before Item 7A is
    typeset, and the section ends at the heading.
    """

    markup = (
        "<p>Item 7. Management's Discussion and Analysis</p>"
        + body("Revenues by segment are discussed here. ")
        + "<p>The statements in Part II, Item 7 include forward-looking "
        "statements about Item 8 as well.</p>"
        + body("More discussion, with the segment tables in it. ")
        + "<p>Item 7A. Quantitative and Qualitative Disclosures</p>"
        + body("Market risk. ")
        + "<p>Item 8. Financial Statements</p>"
        + body("The statements. ")
    )

    section = located(markup, 7)

    assert section is not None
    assert section.closed_by is not None
    assert section.closed_by.item == Item(7, "A")
    assert "More discussion" in flatten(markup).text[section.at : section.ends]


def test_the_resolved_sequence_runs_in_item_order() -> None:
    """The coherence that decides, stated as a property of the run."""

    markup = (
        "<p>Item 1. Business</p>"
        + body("A. ")
        + "<p>Item 1A. Risk Factors</p>"
        + body("B. ")
        + "<p>Item 1B. Unresolved Staff Comments</p>"
        + body("C. ")
        + "<p>Item 2. Properties</p>"
        + body("D. ")
    )

    flat = flatten(markup)
    run = sequence(tuple(c for c in candidates(markup, flat) if c.is_heading))

    assert [candidate.item for candidate in run] == [
        Item(1),
        Item(1, "A"),
        Item(1, "B"),
        Item(2),
    ]

    positions = [candidate.at for candidate in run]

    assert positions == sorted(positions)


def test_an_item_the_sequence_does_not_contain_is_absent() -> None:
    """A section that cannot be located is absent, never substituted."""

    markup = "<p>Item 1. Business</p>" + body("Only this. ")

    assert located(markup, 7) is None


# ── the trace, because location is now evidence infrastructure ──────


def test_the_selection_explains_itself_and_what_it_rejected() -> None:
    markup = (
        "<p>Item 1. Business 3</p>"
        "<p>ITEM 1. BUSINESS</p>"
        + body("The real section. ")
        + "<p>ITEM 1A. RISK FACTORS</p>"
        + body("Risks. ")
    )

    section = located(markup, 1)

    assert section is not None

    trace = section.stated()

    assert "Selected Item 1 candidate at offset" in trace
    assert "Evidence:" in trace
    assert "Rejected candidate at offset" in trace
    assert "+" in trace


def test_every_observation_is_named_and_directional() -> None:
    """No score without an account of it."""

    markup = "<p>ITEM 1. BUSINESS</p>" + body("Text. ")
    flat = flatten(markup)

    for candidate in candidates(markup, flat):
        for observed in candidate.evidence:
            assert observed.observation
            assert isinstance(observed.supports, bool)
            assert observed.stated().startswith(("+ ", "- "))


def test_a_cross_reference_phrase_is_matched_on_whole_words() -> None:
    """
    'margin' ends with 'in', and an occurrence after it is not a
    reference. Substring matching here would quietly reject real
    headings — the kind of plausible wrongness this module removes.
    """

    markup = (
        "<p>Operating margin</p><p>ITEM 1. BUSINESS</p>"
        + body("Real section. ")
        + "<p>ITEM 1A. RISK FACTORS</p>"
        + body("Risks. ")
    )

    section = located(markup, 1)

    assert section is not None
    assert not any(
        "reference, not a title" in seen.observation
        for seen in section.opened_by.evidence
    )
