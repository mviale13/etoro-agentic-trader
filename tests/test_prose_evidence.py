"""A span that exists is not a span that describes."""

import pytest

from app.domain.evidence import EvidenceNotApplicable
from app.domain.prose_evidence import NEARBY, describes, namings

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
