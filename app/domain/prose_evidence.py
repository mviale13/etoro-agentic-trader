"""A description a document printed, and proof of what it describes.

The narrative half of the same defect the tabular module closes. A span
can be exactly present in a filing and describe nothing it was attached
to — measured live, reading Volkswagen's segment note, all three segments
were cited with the identical sentence:

    "Die Vorjahreswerte entsprechen der geänderten Berichtsstruktur."

The prior-year figures correspond to the changed reporting structure. It
is genuinely in the document, it is genuinely about accounting, and it
describes no segment whatsoever. Grounding passes on all three.

What a table gives a number, prose gives a description: **position**. A
figure belongs to the row whose label leads it; a description belongs to
the segment whose name most recently precedes it. The document's own
naming of its segments partitions the prose the way row labels partition
a table, and that partition is something this platform can compute for
itself rather than take from a reading.

Two rules, and the measurements that set them. Across Disney's 10-K and
Volkswagen's annual report:

- **Ownership.** The span must sit under this segment's name and no
  other's. On Volkswagen this refuses two of the three citations
  outright, because the footnote sits in a third segment's region.
- **Proximity.** It must sit close enough to that naming to be part of
  what the document says about it. This is what refuses Volkswagen's
  third citation, which passes ownership *by accident* — the footnote
  happens to follow the last segment named, so that segment would
  otherwise claim it.

What is deliberately **not** a rule: that the span contain the segment's
name. Two of Disney's three good citations do not — the name is the
sentence's subject and the span is its predicate — so requiring it would
reject sound evidence and push a reading toward quoting headings instead
of descriptions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.evidence import EvidenceNotApplicable, normalised

#: How far a description may sit from the naming it belongs to, in
#: characters of normalised text.
#:
#: Measured rather than chosen. Disney's three sound citations sit 0, 23
#: and 51 characters after their segment is named — the same sentence, or
#: the next one. Volkswagen's boilerplate sits 814 and 1474 characters
#: after the nearest naming, which is somewhere else in the document
#: entirely. The gap between the two populations is more than an order of
#: magnitude, and this sits inside it with room on both sides.
#:
#: Widen it only with a document that shows the bound is wrong. Narrowing
#: it costs sound descriptions; widening it admits the boilerplate this
#: exists to refuse.
NEARBY = 300


@dataclass(frozen=True, slots=True)
class Naming:
    """One place a document names one of its own segments."""

    #: The segment, as this platform holds it.
    segment: str

    #: Where the naming begins and ends, in normalised coordinates.
    at: int
    ends: int

    def covers(self, other: Naming) -> bool:
        """Whether this naming contains another one whole.

        Segment names nest, and the shorter one is not a second naming.
        Volkswagen reports "Nutzfahrzeuge" and "Pkw und leichte
        Nutzfahrzeuge", so every mention of the second is also a mention
        of the first — and taking it as one would hand the shorter
        segment every region the longer segment introduced.
        """

        return self.at <= other.at and other.ends <= self.ends and self is not other


@dataclass(frozen=True, slots=True)
class DescribedSegment:
    """
    What a segment does, and proof the document says it of *this* segment.

    `quoted` establishes existence: the words are in the filing. The rest
    establishes applicability: the words sit inside the stretch of the
    document that this segment's own name introduced, close enough to it
    to be part of what is being said about it.

    An unevidenced description is unrepresentable rather than
    discouraged. There is no way to build one of these without a naming
    and a distance, and both are computed here from the document rather
    than accepted from whatever read it.
    """

    #: The verbatim span, as the document prints it.
    quoted: str

    #: The segment naming this span sits under, read off the document.
    under: str

    #: How far the span sits from that naming. Carried so a reader can
    #: see how directly the document connected the two, rather than only
    #: that something passed a threshold.
    distance: int

    def stated(self) -> str:
        """The description as an investor would check it."""

        where = (
            "in the same breath as"
            if self.distance == 0
            else f"{self.distance} characters after"
        )

        return f'"{self.quoted}" — {where} the document\'s own "{self.under}"'


def namings(text: str, segments: tuple[str, ...]) -> tuple[Naming, ...]:
    """
    Every place this document names one of these segments, in order.

    The partition. A document that never names a segment contributes
    nothing here for it, which is not a failure — it is why that
    segment's description will be absent rather than attached to whatever
    sentence happened to be nearby.
    """

    flat, origins = _indexed(text)

    found: list[Naming] = []

    for segment in segments:
        needle = normalised(segment)

        if not needle:
            continue

        at = flat.find(needle)

        while at != -1:
            if _is_a_word(text, origins, at, at + len(needle)):
                found.append(Naming(segment=segment, at=at, ends=at + len(needle)))

            at = flat.find(needle, at + 1)

    # A naming swallowed whole by a longer one is that longer one, said
    # once. Keeping both would let "Nutzfahrzeuge" claim every stretch of
    # the document that "Pkw und leichte Nutzfahrzeuge" opened.
    standing = [
        naming for naming in found if not any(other.covers(naming) for other in found)
    ]

    return tuple(sorted(standing, key=lambda naming: naming.at))


def describes(
    text: str,
    partition: tuple[Naming, ...],
    segment: str,
    quoted: str,
) -> DescribedSegment:
    """
    This span as a description of this segment, or a worded refusal.

    Every occurrence of the span is considered, because a sentence can
    appear twice and only one of them need sit where it is claimed to.
    The best placement wins — the one under this segment and closest to
    its naming — and where no occurrence qualifies, the refusal says
    which segment the document actually put those words under. That is
    usually the more useful fact: it names what went wrong rather than
    reporting that something did.
    """

    if not quoted.strip():
        raise EvidenceNotApplicable(
            f"The description of {segment!r} arrived with no words at all."
        )

    flat = normalised(text)
    needle = normalised(quoted)

    if not needle or needle not in flat:
        raise EvidenceNotApplicable(
            f"The description of {segment!r} quotes words that are not in the document."
        )

    best: DescribedSegment | None = None
    elsewhere: set[str] = set()

    at = flat.find(needle)

    while at != -1:
        ends = at + len(needle)

        # The document's last word on the subject before this span
        # finishes — which may be inside the span itself, because "The
        # Entertainment segment produces and distributes film" is the
        # best citation there is and names the segment in its first
        # three words.
        opened = [naming for naming in partition if naming.at < ends]
        owner = opened[-1] if opened else None

        if owner is None:
            elsewhere.add("nothing the document had named yet")
        elif owner.segment != segment:
            elsewhere.add(owner.segment)
        else:
            distance = 0 if owner.at >= at else at - owner.at

            if best is None or distance < best.distance:
                best = DescribedSegment(
                    quoted=quoted.strip(),
                    under=owner.segment,
                    distance=distance,
                )

        at = flat.find(needle, at + 1)

    if best is None:
        raise EvidenceNotApplicable(
            f"The description of {segment!r} quotes words the document prints "
            f"under {_worded(elsewhere)}, so they are not what it says about "
            f"{segment!r}."
        )

    if best.distance > NEARBY:
        raise EvidenceNotApplicable(
            f"The description of {segment!r} quotes words that sit "
            f"{best.distance} characters from where the document last named "
            f"it — far enough to be about something else. A description is "
            "what a document says of a segment, not what it happens to say "
            "after one."
        )

    return best


def _indexed(text: str) -> tuple[str, tuple[int, ...]]:
    """The comparison text, and where each of its characters came from.

    `normalised` throws away everything but letters and digits, which is
    what makes a filing's typography harmless — and it also throws away
    the word boundaries. Keeping the origins allows a match to be asked
    the one question the normalised form cannot answer: was that a word,
    or the tail of a longer one?
    """

    kept: list[str] = []
    origins: list[int] = []

    # Folded one character at a time, because folding the whole string
    # first would change its length and silently shift every index after
    # the change. German "ß" folds to "ss", so on Volkswagen's report
    # every origin past the first one pointed a character to the left —
    # and the boundary check then read the wrong character and refused
    # the segment's own name, discarding the entire reading.
    for index, character in enumerate(text):
        for folded in character.casefold():
            if folded.isalnum():
                kept.append(folded)
                origins.append(index)

    return "".join(kept), tuple(origins)


def _is_a_word(text: str, origins: tuple[int, ...], at: int, ends: int) -> bool:
    """
    Whether this match is the segment's name rather than part of a word.

    Disney's Entertainment section contains the phrase "non-sports
    focused global film", and normalised to letters that phrase contains
    "sports". Read as a naming, it opens the Sports segment's region in
    the middle of the Entertainment segment's — and Entertainment's own
    description is then refused as belonging to Sports. The refusal is
    silent, because a description that does not apply is absent rather
    than an error.

    So a naming has to be a word. What precedes it must not be a letter
    or a hyphen joining it to one, and what follows must not be a letter.
    """

    if at >= len(origins) or ends > len(origins):
        return False

    before = origins[at] - 1
    after = origins[ends - 1] + 1

    if before >= 0:
        preceding = text[before]

        if preceding.isalnum() or preceding in "-'’":
            return False

    if after < len(text) and text[after].isalnum():
        return False

    return True


def _worded(names: set[str]) -> str:
    """A set of segment names as a reader would say them."""

    if not names:
        return "no segment at all"

    listed = sorted(names)

    if len(listed) == 1:
        return repr(listed[0])

    return f"{', '.join(repr(name) for name in listed[:-1])} and {listed[-1]!r}"
