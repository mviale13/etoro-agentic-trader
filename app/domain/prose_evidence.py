"""A description a document printed, and proof of what it describes.

The narrative half of the same defect the tabular module closes. A span
can be exactly present in a filing and describe nothing it was attached
to — measured live, reading Volkswagen's segment note, all three segments
were cited with the identical sentence:

    "Die Vorjahreswerte entsprechen der geänderten Berichtsstruktur."

The prior-year figures correspond to the changed reporting structure. It
is genuinely in the document, it is genuinely about accounting, and it
describes no segment whatsoever. Grounding passes on all three.

The invariant this module serves is **unambiguous ownership**: a
narrative citation must establish that the cited text belongs to the
claim it supports. What follows are the mechanisms, not the invariant.

**What an owner is, stated apart from how one is found.** A structural
owner is *the smallest region of the document that can be shown to
correspond uniquely to the claim* — smallest, because a region covering
the whole filing owns nothing in particular; shown, because this
platform computes it from the document rather than accepting it from
whatever read it; uniquely, because if two regions could own a claim,
none does.

Two mechanisms serve that concept, and the stronger one is preferred
where the document supports it.

**Structure, where the document has any.** A heading introduces a region
and the region runs to the next heading, so the span that describes a
segment is the one printed inside that segment's own section. This is
the mechanism `owning` and the structural branch of `describes`
implement.

**Position, where it does not.** What a table gives a number, prose
gives a description: a figure belongs to the row whose label leads it,
so a description belongs to the segment whose name most recently
precedes it. Two positional rules, and the measurements that set them,
across Disney's 10-K and Volkswagen's annual report:

- **Ownership by naming.** The span must sit under this segment's name
  and no other's. On Volkswagen this refuses two of the three citations
  outright, because the footnote sits in a third segment's region.
- **Proximity.** It must sit close enough to that naming to be part of
  what the document says about it. This is what refuses Volkswagen's
  third citation, which passes the naming rule *by accident* — the
  footnote happens to follow the last segment named, so that segment
  would otherwise claim it.

**Why position alone was not enough, measured rather than argued.**
Meta's 10-K is not an ambiguous document; ownership by naming was. The
only exact occurrences of the stored names `Family of Apps (FoA)` and
`Reality Labs (RL)` sit twenty-five characters apart, in one summary
sentence at prose offsets 7021 and 7046 — *after* all the descriptive
prose, which lives at 2323–6400 under the headings `Family of Apps
Products` and `Reality Labs Products`. So "the segment whose name most
recently precedes it" hands nearly the whole section to whichever
segment that late sentence names last. The partition was not imprecise;
it was inverted, which is why asking again for a better citation
recovered nothing.

What is deliberately **not** a rule: that the span contain the segment's
name. Two of Disney's three good citations do not — the name is the
sentence's subject and the span is its predicate — so requiring it would
reject sound evidence and push a reading toward quoting headings instead
of descriptions.
"""

from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import dataclass
from enum import StrEnum

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

#: An abbreviation the filer defined for its own segment, which belongs
#: to the name this platform stores and not to the heading the document
#: prints over the section. Meta stores `Family of Apps (FoA)` and heads
#: the section `Family of Apps Products`; neither string contains the
#: other, and the parenthetical is the whole of the difference.
_DEFINED_ABBREVIATION = re.compile(r"\s*\([^()]*\)\s*$")


class Ownership(StrEnum):
    """How a span was shown to belong to the segment it describes.

    Carried because the two are not equally strong and a reader is owed
    the difference. A span inside the section the document heads with a
    segment's name is owned by the document's own structure; a span that
    merely follows a mention of the segment is owned by where it sits.
    """

    #: The span is printed inside the region a heading introduced, and
    #: that heading corresponds uniquely to this segment.
    STRUCTURE = "structure"

    #: The document offered no usable structure, so the span was placed
    #: by the naming it sits under and its distance from it.
    PROXIMITY = "proximity"


@dataclass(frozen=True, slots=True)
class Region:
    """A stretch of a document that one heading introduced.

    The region runs from its heading to the next one, which is what
    makes it the *smallest* region the document offers — a region that
    ran to the end of the section would swallow everything the filer
    wrote afterwards about competition, regulation and its workforce.

    Coordinates are into the prose as the platform reads it, before
    normalisation, because that is what the provider that parsed the
    markup can honestly report.
    """

    #: The words the document printed as the heading, verbatim.
    heading: str

    at: int
    ends: int


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

    #: What the span was shown to sit under, read off the document: the
    #: segment's own naming under proximity, the section's heading under
    #: structure.
    under: str

    #: How far the span sits from that naming or heading. Carried so a
    #: reader can see how directly the document connected the two, rather
    #: than only that something passed a threshold.
    distance: int

    #: Which of the two mechanisms established the ownership. Defaulted
    #: to proximity so that every citation written before structure
    #: existed keeps saying exactly what it always said.
    ownership: Ownership = Ownership.PROXIMITY

    def stated(self) -> str:
        """The description as an investor would check it."""

        if self.ownership is Ownership.STRUCTURE:
            where = (
                "at the head of"
                if self.distance == 0
                else f"{self.distance} characters into"
            )

            return (
                f'"{self.quoted}" — {where} the section the document '
                f'heads "{self.under}"'
            )

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


def owning(
    regions: tuple[Region, ...],
    segments: tuple[str, ...],
) -> dict[str, Region]:
    """
    Which region of the document corresponds uniquely to each segment.

    The structural half of the partition, and the whole of it is
    uniqueness. A heading owns a segment when it contains that segment's
    name — less the abbreviation the filer defined for its own use — and
    when it is the only heading that does, and when it names no other
    segment. A segment that fails any of those has no structural owner
    here, and the caller falls back to the weaker mechanism rather than
    picking between candidates.

    Ambiguity is deliberately not resolved by preference or by order. Two
    regions that could each own a claim mean the document did not say
    which, and guessing would be exactly the kind of unproven
    relationship this module exists to refuse.
    """

    wanted = {
        segment: normalised(_DEFINED_ABBREVIATION.sub("", segment))
        for segment in segments
    }

    matched: dict[str, list[Region]] = {segment: [] for segment in segments}

    for region in regions:
        heading = normalised(region.heading)

        named = [
            segment for segment, name in wanted.items() if name and name in heading
        ]

        # A heading that names two segments introduces a region that
        # corresponds uniquely to neither of them.
        if len(named) != 1:
            continue

        matched[named[0]].append(region)

    return {segment: found[0] for segment, found in matched.items() if len(found) == 1}


def describes(
    text: str,
    partition: tuple[Naming, ...],
    segment: str,
    quoted: str,
    owner: Region | None = None,
) -> DescribedSegment:
    """
    This span as a description of this segment, or a worded refusal.

    Every occurrence of the span is considered, because a sentence can
    appear twice and only one of them need sit where it is claimed to.
    The best placement wins, and where no occurrence qualifies, the
    refusal says what the document actually put those words under. That
    is usually the more useful fact: it names what went wrong rather than
    reporting that something did.

    Where the document offered a structural owner, that region decides —
    both ways. A span inside it is a description however far into the
    section it sits, and a span outside it is refused however close it
    happens to sit to a mention of the segment. Preferring the stronger
    mechanism does not mean accepting more: existence is established
    first and identically, and a structurally selected span is held to
    the same requirement that the document actually prints it.
    """

    if not quoted.strip():
        raise EvidenceNotApplicable(
            f"The description of {segment!r} arrived with no words at all."
        )

    flat, origins = _indexed(text)
    needle = normalised(quoted)

    if not needle or needle not in flat:
        raise EvidenceNotApplicable(
            f"The description of {segment!r} quotes words that are not in the document."
        )

    if owner is not None:
        return _inside(flat, origins, owner, segment, quoted)

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
        last_named = opened[-1] if opened else None

        if last_named is None:
            elsewhere.add("nothing the document had named yet")
        elif last_named.segment != segment:
            elsewhere.add(last_named.segment)
        else:
            distance = 0 if last_named.at >= at else at - last_named.at

            if best is None or distance < best.distance:
                best = DescribedSegment(
                    quoted=quoted.strip(),
                    under=last_named.segment,
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


def _inside(
    flat: str,
    origins: tuple[int, ...],
    owner: Region,
    segment: str,
    quoted: str,
) -> DescribedSegment:
    """
    This span as something printed inside the region that owns the segment.

    The region's bounds are in the prose as it was read; the span is
    located in the normalised text. So each occurrence is mapped back
    through its origins and asked whether the document printed it inside
    the section, which is a question about the document rather than
    about the reduction this platform compares through.

    The earliest qualifying occurrence wins. Under proximity the best
    placement is the closest one to a naming; here every occurrence
    inside the region is owned by it equally, and the first is the one a
    reader turning to that section would find.
    """

    needle = normalised(quoted)

    at = flat.find(needle)

    while at != -1:
        ends = at + len(needle)

        # Where the document printed this occurrence, rather than where
        # it landed in the reduction.
        opens = origins[at]
        closes = origins[ends - 1]

        if owner.at <= opens and closes < owner.ends:
            return DescribedSegment(
                quoted=quoted.strip(),
                under=owner.heading,
                distance=at - _normalised_index(origins, owner.at),
                ownership=Ownership.STRUCTURE,
            )

        at = flat.find(needle, at + 1)

    raise EvidenceNotApplicable(
        f"The description of {segment!r} quotes words the document prints "
        f"outside the section it heads {owner.heading!r}, so they are not "
        f"what it says there about {segment!r}."
    )


def _normalised_index(origins: tuple[int, ...], at: int) -> int:
    """Where a position in the prose lands in the normalised text.

    The origins rise, so the first character kept from `at` onwards is
    the first origin that reaches it. A region beginning on a character
    normalisation discarded — the space after a heading, most often —
    therefore begins at the next character it kept, which is what makes
    a distance of zero mean "at the head of the section".
    """

    return bisect_left(origins, at)


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
