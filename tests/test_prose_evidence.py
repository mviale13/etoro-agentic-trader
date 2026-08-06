"""A span that exists is not a span that describes."""

import pytest

from app.domain.evidence import EvidenceNotApplicable, normalised
from app.domain.prose_evidence import (
    NEARBY,
    Ownership,
    Region,
    describes,
    namings,
    owning,
)

SEGMENT_PROSE = (
    "The Company operates in three segments. "
    "The Entertainment segment produces and distributes film and television "
    "content and operates direct-to-consumer streaming services. "
    "The Sports segment operates ESPN and produces live sporting events. "
    "The Experiences segment operates theme parks and cruise ships."
)

FILING = (
    SEGMENT_PROSE
    + " Prior-year figures have been restated to reflect the changed structure."
)

SEGMENTS = ("Entertainment", "Sports", "Experiences")

PARTITION = namings(FILING, SEGMENTS)


def described(segment: str, quoted: str):
    return describes(FILING, PARTITION, segment, quoted)


# ── the partition ───────────────────────────────────────────────────


def test_a_document_names_its_own_segments_and_that_is_the_partition() -> None:
    """
    The prose equivalent of a table's row labels.

    A figure belongs to the row whose label leads it; a description
    belongs to the segment whose name most recently precedes it. Both are
    computed by this platform from the document, never taken from the
    reading — which is what makes them evidence rather than assertion.
    """

    assert [naming.segment for naming in PARTITION] == [
        "Entertainment",
        "Sports",
        "Experiences",
    ]

    # In document order, so a position can be attributed to one of them.
    assert [naming.at for naming in PARTITION] == sorted(
        naming.at for naming in PARTITION
    )


def test_a_segment_name_swallowed_by_a_longer_one_is_not_a_second_naming() -> None:
    """
    Volkswagen reports both "Nutzfahrzeuge" and "Pkw und leichte
    Nutzfahrzeuge", so every mention of the second is also a mention of
    the first. Counting both would hand the shorter segment every stretch
    of the document that the longer segment opened — and it did, until
    the real report was run through this.
    """

    text = (
        "Das Segment Pkw und leichte Nutzfahrzeuge umfasst die Marken. "
        "Das Segment Nutzfahrzeuge umfasst Trucks und Busse."
    )

    partition = namings(text, ("Nutzfahrzeuge", "Pkw und leichte Nutzfahrzeuge"))

    assert [naming.segment for naming in partition] == [
        "Pkw und leichte Nutzfahrzeuge",
        "Nutzfahrzeuge",
    ]


def test_a_segment_name_inside_another_word_is_not_a_naming() -> None:
    """
    Disney's Entertainment section says "non-sports focused global film".

    Normalised to letters, that phrase contains "sports". Read as a
    naming it opens the Sports region in the middle of Entertainment's,
    and Entertainment's own description is then refused as belonging to
    Sports — silently, because an inapplicable description is absent
    rather than an error. Caught on the live 10-K, not in a fixture.
    """

    text = (
        "The Entertainment segment encompasses non-sports focused global film "
        "and episodic content. The Sports segment operates ESPN."
    )

    partition = namings(text, ("Entertainment", "Sports"))

    assert [naming.segment for naming in partition] == ["Entertainment", "Sports"]

    evidence = describes(
        text, partition, "Entertainment", "non-sports focused global film"
    )

    assert evidence.under == "Entertainment"


def test_a_naming_survives_a_character_that_folds_into_two() -> None:
    """
    Case folding changes a string's length, and German is where it shows.

    "ß" folds to "ss", so folding the whole document before indexing it
    shifted every position after the first one by a character. The
    boundary check then read the wrong character, decided Volkswagen's
    report never names "Pkw und leichte Nutzfahrzeuge", and discarded the
    entire reading — identity, measured sizes and all.
    """

    text = (
        "Die Konzernzentrale liegt an der Berliner Straße. "
        "Das Segment Nutzfahrzeuge umfasst Trucks und Busse."
    )

    partition = namings(text, ("Nutzfahrzeuge",))

    assert [naming.segment for naming in partition] == ["Nutzfahrzeuge"]

    evidence = describes(text, partition, "Nutzfahrzeuge", "umfasst Trucks und Busse")

    assert evidence.under == "Nutzfahrzeuge"


def test_a_segment_name_that_is_the_stem_of_a_longer_word_is_not_a_naming() -> None:
    """ "Sportsman" is not the Sports segment being named."""

    text = "The Retail segment sells Sportsman equipment and outdoor gear."

    assert namings(text, ("Sports",)) == ()


# ── applicability ───────────────────────────────────────────────────


def test_a_span_the_document_prints_under_this_segment_describes_it() -> None:
    evidence = described(
        "Entertainment",
        "produces and distributes film and television content",
    )

    assert evidence.under == "Entertainment"
    assert evidence.distance > 0
    assert "characters after" in evidence.stated()


def test_a_span_that_opens_with_the_segments_own_name_is_the_strongest() -> None:
    """
    A naming inside the span is the best placement, not a missing one.

    An earlier rule looked only behind a span for the naming it belonged
    to, and so refused exactly the citations that need no looking.
    """

    evidence = described(
        "Entertainment",
        "The Entertainment segment produces and distributes film",
    )

    assert evidence.distance == 0
    assert "in the same breath as" in evidence.stated()


def test_a_span_the_document_prints_under_another_segment_is_refused() -> None:
    """The words are real, and the document says them of someone else."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        described("Experiences", "operates ESPN and produces live sporting events")

    assert "'Sports'" in str(refused.value)
    assert "not what it says about" in str(refused.value)


def test_boilerplate_after_the_last_segment_named_is_refused_on_distance() -> None:
    """
    Ownership alone lets it through; proximity is what closes it.

    Volkswagen's restatement footnote passes ownership by accident — it
    follows the last segment the document names, so that segment would
    otherwise claim it. Measured, sound citations sat 0 to 51 characters
    from their naming and this footnote sat 814.
    """

    filler = " ".join(["The Company faces competition and regulation."] * 12)

    text = SEGMENT_PROSE + " " + filler + " Prior-year figures have been restated."
    partition = namings(text, SEGMENTS)

    with pytest.raises(EvidenceNotApplicable) as refused:
        describes(
            text, partition, "Experiences", "Prior-year figures have been restated"
        )

    assert "characters from where the document last named it" in str(refused.value)


def test_boilerplate_immediately_after_a_segment_is_not_caught() -> None:
    """
    The residual gap, asserted rather than left to be discovered.

    Ownership and proximity are positional, so they cannot tell a
    description from a note that happens to sit right where a description
    would. Volkswagen's footnote was caught because it sat 814 characters
    away; the same sentence one line below a segment's description would
    pass.

    Recorded as a limit rather than papered over: closing it means
    judging what a sentence is *about*, which is a different kind of
    check from where it sits, and it would be a new slice rather than a
    wider bound here.
    """

    evidence = describes(
        FILING,
        PARTITION,
        "Experiences",
        "Prior-year figures have been restated",
    )

    assert evidence.under == "Experiences"
    assert evidence.distance < NEARBY


def test_a_span_before_any_segment_is_named_describes_none_of_them() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        described("Entertainment", "The Company operates in three segments")

    assert "nothing the document had named yet" in str(refused.value)


def test_a_span_that_is_not_in_the_document_is_refused() -> None:
    """Existence first. Applicability has nothing to work on without it."""

    with pytest.raises(EvidenceNotApplicable) as refused:
        described("Entertainment", "sells industrial lubricants to shipping fleets")

    assert "not in the document" in str(refused.value)


def test_an_empty_span_is_refused_rather_than_treated_as_a_description() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        described("Entertainment", "   ")

    assert "no words at all" in str(refused.value)


def test_the_best_placement_of_a_repeated_span_is_the_one_that_counts() -> None:
    """
    A sentence can appear twice and only one of them need sit where it is
    claimed to. Refusing on the worst occurrence would reject a citation
    the document does support.
    """

    text = (
        "operates theme parks and cruise ships. "
        "The Experiences segment operates theme parks and cruise ships."
    )

    partition = namings(text, SEGMENTS)

    evidence = describes(
        text, partition, "Experiences", "operates theme parks and cruise ships"
    )

    # The first occurrence sits before the document names anything at
    # all; the second sits just after "The Experiences segment". The
    # second is the one the citation rests on.
    assert evidence.under == "Experiences"
    assert evidence.distance == 18


def test_the_distance_is_counted_in_characters_that_carry_meaning() -> None:
    """
    A filing's own typography must not decide whether a citation applies.

    Markup leaves stray spacing everywhere, so distance is measured after
    normalisation — a page of whitespace between a naming and its
    description is not distance.
    """

    spaced = FILING.replace(" ", "      ")
    partition = namings(spaced, SEGMENTS)

    evidence = describes(
        spaced,
        partition,
        "Entertainment",
        "The Entertainment segment produces and distributes film",
    )

    assert evidence.distance == 0
    assert NEARBY == 300


# ── ownership by structure ──────────────────────────────────────────

#: A filing shaped the way Meta's 10-K is shaped, which is the shape
#: that inverts a positional partition. The segments are described in
#: sequence under their own headings, and the only place the document
#: uses the names this platform stores is a summary sentence *after* all
#: of it. So "the segment whose name most recently precedes it" attributes
#: every description to nothing at all, and the last sentence to both.
META_SHAPED = (
    "Overview "
    "We build technology that helps people connect. "
    "Family of Apps Products "
    "Facebook helps people share moments and build community. "
    "Reality Labs Products "
    "We build augmented and virtual reality hardware and software. "
    "Revenue and Investments "
    "We generate substantially all of our revenue from advertising. "
    "Our reportable segments are Family of Apps (FoA) and Reality Labs (RL)."
)

META_SEGMENTS = ("Family of Apps (FoA)", "Reality Labs (RL)")

META_HEADINGS = (
    "Overview",
    "Family of Apps Products",
    "Reality Labs Products",
    "Revenue and Investments",
)


def meta_regions() -> tuple[Region, ...]:
    """The regions those headings introduce, each running to the next."""

    at = [META_SHAPED.index(heading) for heading in META_HEADINGS]

    return tuple(
        Region(
            heading=heading,
            at=at[index],
            ends=at[index + 1] if index + 1 < len(at) else len(META_SHAPED),
        )
        for index, heading in enumerate(META_HEADINGS)
    )


META_REGIONS = meta_regions()
META_PARTITION = namings(META_SHAPED, META_SEGMENTS)
META_OWNERS = owning(META_REGIONS, META_SEGMENTS)


def test_a_heading_owns_the_segment_it_names_despite_the_filers_shorthand() -> None:
    """
    The matching problem, which is the hard part rather than the detection.

    The heading reads "Family of Apps Products" and the stored name is
    "Family of Apps (FoA)". Neither string contains the other, and the
    whole of the difference is an abbreviation the filer defined for its
    own later use.
    """

    assert META_OWNERS["Family of Apps (FoA)"].heading == "Family of Apps Products"
    assert META_OWNERS["Reality Labs (RL)"].heading == "Reality Labs Products"


def test_a_description_binds_to_its_own_section_though_it_precedes_the_naming() -> None:
    """
    Meta-shaped, and the reason this mechanism exists.

    Position alone refuses this description outright — the document has
    named no segment at all by the time it prints it. Structure accepts
    it, because the filer printed it under that segment's own heading.
    """

    quoted = "Facebook helps people share moments and build community"

    with pytest.raises(EvidenceNotApplicable):
        describes(META_SHAPED, META_PARTITION, "Family of Apps (FoA)", quoted)

    evidence = describes(
        META_SHAPED,
        META_PARTITION,
        "Family of Apps (FoA)",
        quoted,
        META_OWNERS["Family of Apps (FoA)"],
    )

    assert evidence.ownership is Ownership.STRUCTURE
    assert evidence.under == "Family of Apps Products"

    # Measured from the head of the section, so the first words after the
    # heading sit exactly the heading's own length into it.
    assert evidence.distance == len(normalised("Family of Apps Products"))
    assert "into the section the document heads" in evidence.stated()


def test_each_segment_binds_to_its_own_section_and_not_its_neighbours() -> None:
    """
    The inversion, stated as the thing that must not happen again.

    Both descriptions sit before either stored name appears, so a
    positional partition attributes them to whichever segment that late
    sentence names last. Structure keeps them apart.
    """

    for segment, quoted, heading in (
        (
            "Family of Apps (FoA)",
            "Facebook helps people share moments",
            "Family of Apps Products",
        ),
        (
            "Reality Labs (RL)",
            "augmented and virtual reality hardware",
            "Reality Labs Products",
        ),
    ):
        evidence = describes(
            META_SHAPED, META_PARTITION, segment, quoted, META_OWNERS[segment]
        )

        assert evidence.under == heading


def test_another_sections_words_are_refused_however_near_they_sit() -> None:
    """
    A neighbouring segment's sentence is outside the owning region.

    The refusal names the section the words were actually printed
    outside of, because "these words are elsewhere in the document" is a
    fact about the filing and the more useful half of the answer.
    """

    with pytest.raises(EvidenceNotApplicable) as refused:
        describes(
            META_SHAPED,
            META_PARTITION,
            "Family of Apps (FoA)",
            "augmented and virtual reality hardware",
            META_OWNERS["Family of Apps (FoA)"],
        )

    assert "outside the section it heads 'Family of Apps Products'" in str(
        refused.value
    )


def test_where_structure_and_position_disagree_structure_decides() -> None:
    """
    The same span, accepted by one mechanism and refused by the other.

    The filing's summary sentence names Family of Apps and then stops, so
    position reads it as that segment's own words at a distance of zero —
    the strongest citation proximity can recognise. It is still not a
    description: it is the sentence that lists the segments, printed
    under a heading about revenue. Structure refuses it, and structure is
    what the document actually says.
    """

    quoted = "Our reportable segments are Family of Apps (FoA)"

    by_position = describes(META_SHAPED, META_PARTITION, "Family of Apps (FoA)", quoted)

    assert by_position.ownership is Ownership.PROXIMITY
    assert by_position.distance == 0

    with pytest.raises(EvidenceNotApplicable):
        describes(
            META_SHAPED,
            META_PARTITION,
            "Family of Apps (FoA)",
            quoted,
            META_OWNERS["Family of Apps (FoA)"],
        )


def test_a_document_with_no_structure_keeps_the_positional_mechanism() -> None:
    """
    Volkswagen-shaped. A report assembled from tagged blocks has no
    headings to divide, so there is nothing to prefer and proximity
    remains — including its ability to return absence.
    """

    assert owning((), SEGMENTS) == {}

    evidence = describes(
        FILING, PARTITION, "Entertainment", "produces and distributes film"
    )

    assert evidence.ownership is Ownership.PROXIMITY


def test_a_segment_two_headings_could_own_has_no_structural_owner() -> None:
    """
    Uniqueness is the whole safeguard.

    A filer that heads two sections "Reality Labs Products" and "Reality
    Labs Financials" has not said which one describes the segment.
    Choosing by order or by length would be this platform deciding
    something the document did not, which is the unproven relationship
    the module exists to refuse.
    """

    regions = (
        Region(heading="Reality Labs Products", at=0, ends=50),
        Region(heading="Reality Labs Financials", at=50, ends=100),
    )

    assert owning(regions, ("Reality Labs (RL)",)) == {}


def test_a_heading_that_names_two_segments_owns_neither() -> None:
    """A region corresponding uniquely to two claims corresponds to none."""

    regions = (
        Region(heading="Family of Apps and Reality Labs", at=0, ends=50),
        Region(heading="Competition", at=50, ends=100),
    )

    assert owning(regions, META_SEGMENTS) == {}


def test_structure_never_admits_words_the_document_does_not_print() -> None:
    """
    Preferring the stronger mechanism does not mean accepting more.

    Existence is established first and identically: a span that is not in
    the filing is refused on that ground, structural owner or not.
    """

    with pytest.raises(EvidenceNotApplicable) as refused:
        describes(
            META_SHAPED,
            META_PARTITION,
            "Family of Apps (FoA)",
            "sells industrial lubricants to shipping fleets",
            META_OWNERS["Family of Apps (FoA)"],
        )

    assert "not in the document" in str(refused.value)


def test_an_empty_span_is_refused_before_structure_is_consulted() -> None:
    with pytest.raises(EvidenceNotApplicable) as refused:
        describes(
            META_SHAPED,
            META_PARTITION,
            "Family of Apps (FoA)",
            "  ",
            META_OWNERS["Family of Apps (FoA)"],
        )

    assert "no words at all" in str(refused.value)
