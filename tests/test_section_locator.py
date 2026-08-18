"""A section boundary is an interpretation, not a string match.

Every case below is a shape a real filing in the acceptance corpus
prints, reduced to the smallest markup that reproduces it. The
companies are named because the slice was earned by measuring them.
"""

from app.providers.document_text import flatten
from app.providers.section_locator import (
    _LISTING_SHORTEST,
    _LISTING_STEP_WIDEST,
    Candidate,
    Evidence,
    Item,
    candidates,
    discover,
    listing_runs,
    locate,
    openings,
    sequence,
)


def located(markup: str, number: int, suffix: str = ""):
    flat = flatten(markup)

    return locate(markup, flat, Item(number=number, suffix=suffix))


def body(text: str) -> str:
    """Filler wide enough that a section reads as a section."""

    return f"<p>{text * 400}</p>"


def occurrence(item: Item, at: int, supported: bool = True) -> Candidate:
    """One discovered occurrence, at a chosen offset.

    The listing run is arithmetic over offsets and item order, so it can
    be asked its boundary questions directly rather than through a
    filing contrived to produce them.
    """

    return Candidate(
        item=item,
        at=at,
        printed=item.stated(),
        evidence=(Evidence("begins a block the filer typeset", supported),),
    )


def listing(*items: Item, start: int = 0, step: int = 20) -> tuple[Candidate, ...]:
    """A run of item entries, evenly spaced, the way a listing prints."""

    return tuple(
        occurrence(item, start + index * step) for index, item in enumerate(items)
    )


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
    by typography either.

    Three entries is a listing too short to be set aside by `openings`,
    so this case still turns on width, and it is kept as the record of
    what width alone can and cannot do: it settles a three-entry listing
    and, measured over the corpus, gets a twenty-entry one wrong. The
    cases below are the ones it gets wrong.
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


# ── the third invariant: a heading in a listing may not open it ─────


def test_the_run_counts_only_an_unbroken_advancing_chain() -> None:
    """What the chain is, and the two ways it stops."""

    chain = listing(Item(1), Item(1, "A"), Item(1, "B"), Item(2), Item(3))

    assert listing_runs(chain) == (4, 3, 2, 1, 0)


def test_a_chain_stops_where_the_sequence_stops_advancing() -> None:
    """A repeated or falling item is a different listing, not more of one."""

    repeated = listing(Item(1), Item(1, "A"), Item(1, "A"), Item(2))
    assert listing_runs(repeated)[0] == 1

    falling = listing(Item(1), Item(1, "A"), Item(1), Item(2))
    assert listing_runs(falling)[0] == 1

    scattered = listing(Item(7), Item(3), Item(9))
    assert listing_runs(scattered) == (0, 1, 0)


def test_a_chain_stops_at_a_step_wider_than_the_listing_allows() -> None:
    """1,999 and 2,000 continue the listing; 2,001 is somewhere else."""

    assert _LISTING_STEP_WIDEST == 2_000

    for step, expected in ((1_999, 1), (2_000, 1), (2_001, 0)):
        pair = (occurrence(Item(1), 0), occurrence(Item(1, "A"), step))

        assert listing_runs(pair)[0] == expected, step


def test_five_entries_are_not_a_listing_and_six_are() -> None:
    """The boundary the corpus put in the middle of an empty band.

    Nothing measured over the 24 held annual reports has a chain of 5 to
    11: the longest chain following anything that is not a listing entry
    is 4, and the shortest following a genuine contents entry is 12.
    """

    ladder = (
        Item(1),
        Item(1, "A"),
        Item(1, "B"),
        Item(1, "C"),
        Item(2),
        Item(3),
        Item(4),
    )

    five = listing(*ladder[:6])
    six = listing(*ladder)

    assert listing_runs(five)[0] == _LISTING_SHORTEST - 1
    assert listing_runs(six)[0] == _LISTING_SHORTEST

    # Five entries do not make a listing, so a body heading does not
    # displace the first of them; six do.
    five_with_body = five + (occurrence(Item(1), 50_000),)
    six_with_body = six + (occurrence(Item(1), 50_000),)

    assert five[0] in openings(five_with_body, five_with_body)
    assert six[0] not in openings(six_with_body, six_with_body)


def test_the_run_reads_item_order_and_not_printed_digits() -> None:
    """1 < 1A < 1B < 2, and 5.02 < 5.03 < 7.01 — #201's own semantics.

    Sorted as strings, '10' precedes '2' and a dotted item has no place
    at all, so a listing would appear to stop advancing and a contents
    entry would open the section it lists.
    """

    suffixed = listing(Item(1), Item(1, "A"), Item(1, "B"), Item(1, "C"), Item(2))
    assert listing_runs(suffixed)[0] == 4

    two_digit = listing(Item(2), Item(9), Item(10), Item(11))
    assert listing_runs(two_digit)[0] == 3

    dotted = listing(
        Item(5, fraction="02"),
        Item(5, fraction="03"),
        Item(7, fraction="01"),
        Item(9, fraction="01"),
    )
    assert listing_runs(dotted)[0] == 3

    # A bare Item 5 sorts before Item 5.02, as a filer's own sequence does.
    bare_then_dotted = listing(Item(5), Item(5, fraction="02"))
    assert listing_runs(bare_then_dotted)[0] == 1


def test_one_listing_entry_and_one_body_heading_leave_the_body() -> None:
    """Regions Financial's case, reduced: both begin blocks, one lists."""

    contents = listing(
        Item(1),
        Item(1, "A"),
        Item(1, "B"),
        Item(1, "C"),
        Item(2),
        Item(3),
        Item(4),
    )
    bodies = (occurrence(Item(1), 50_000), occurrence(Item(1, "A"), 120_000))
    every = contents + bodies

    eligible = openings(every, every)

    assert contents[0] not in eligible
    assert bodies[0] in eligible


def test_several_listing_entries_and_one_body_leave_only_the_body() -> None:
    """A filing may print its contents twice; neither copy opens a section."""

    first = listing(
        Item(1), Item(1, "A"), Item(1, "B"), Item(1, "C"), Item(2), Item(3), Item(4)
    )
    second = listing(
        Item(1),
        Item(1, "A"),
        Item(1, "B"),
        Item(1, "C"),
        Item(2),
        Item(3),
        Item(4),
        start=10_000,
    )
    real = occurrence(Item(1), 50_000)
    every = first + second + (real,)

    eligible = openings(every, every)

    assert [found for found in eligible if found.item == Item(1)] == [real]


def test_where_every_candidate_lists_they_are_all_retained() -> None:
    """Honeywell's case: its sections carry no item number at all.

    Its only occurrences of Item 1 and Item 7 are inside its own
    "FORM 10-K CROSS-REFERENCE INDEX". Struck outright, the filing goes
    silent about sections it does print; retained, it says exactly what
    it said before. The rule is a preference, never a veto.
    """

    index = listing(
        Item(1), Item(1, "A"), Item(1, "B"), Item(1, "C"), Item(2), Item(3), Item(4)
    )

    assert openings(index, index) == index


def test_one_listing_chain_does_not_unseat_another_item() -> None:
    """One chain runs through every item, so eligibility is per item.

    Item 1 has a body to open it and its entry is set aside. Item 3 is
    printed nowhere but the listing, and keeps it.
    """

    contents = listing(
        Item(1), Item(1, "A"), Item(1, "B"), Item(1, "C"), Item(2), Item(3), Item(4)
    )
    real = occurrence(Item(1), 50_000)
    every = contents + (real,)

    eligible = openings(every, every)
    kept = {found.item for found in eligible}

    assert Item(3) in kept
    assert Item(2) in kept
    assert contents[0] not in eligible
    assert real in eligible


def test_the_listing_run_is_read_before_anything_is_set_aside() -> None:
    """A set-aside entry still counts toward the chain that removed it.

    The run is measured over every discovered occurrence — including the
    prose cross-references the evidence layer rejects — so the reading
    does not change with which candidates survived it.
    """

    contents = listing(
        Item(1), Item(1, "A"), Item(1, "B"), Item(1, "C"), Item(2), Item(3), Item(4)
    )
    real = occurrence(Item(1), 50_000)
    every = contents + (real,)

    # Only the two Item 1 occurrences ever reach the evidence layer here;
    # the chain that condemns the first is made of the others.
    accepted = (contents[0], real)

    assert openings(every, accepted) == (real,)


def test_a_listing_entry_is_set_aside_and_still_explains_itself() -> None:
    """Discovery is untouched, and the rejected entry is still reported.

    Which is what places the rule between discovery and resolution: the
    contents entry is discovered, is observed to begin a block, is not
    allowed to open the section, and is still handed to the reader as a
    candidate that was considered.
    """

    printed = ("1.", "1A.", "1B.", "1C.", "2.", "3.", "4.")

    contents = "".join(
        f"<p>Item {number} Heading {page}</p>"
        for page, number in enumerate(printed, start=3)
    )
    sections = "".join(
        f"<p>ITEM\xa0{number} HEADING</p>" + body(f"Section {number} prose. ")
        for number in printed
    )

    markup = f"<p>FORM 10-K INDEX</p>{contents}{sections}"

    flat = flatten(markup)
    every = candidates(markup, flat)
    accepted = tuple(found for found in every if found.is_heading)

    listed = next(found for found in every if found.item == Item(1))

    assert listed.is_heading, "discovery and evidence are untouched"
    assert listed not in openings(every, accepted), "but it may not open the section"

    section = locate(markup, flat, Item(1))

    assert section is not None
    assert "Section 1. prose" in flat.text[section.at : section.ends]
    assert listed.at in {other.at for other in section.rejected}


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
