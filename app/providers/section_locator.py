"""Where a filing's numbered sections begin and end, and why there.

A section boundary is not a text match. It is an interpretation of a
document, supported by several independent structural observations and
resolved against the sequence the filing as a whole describes.

The failure that earned this module is worth stating exactly, because
it is the argument for the whole design. The locator used to ask one
pattern to do two different jobs: recognise a heading despite the way
it was typeset, *and* decide whether that occurrence was structurally a
heading rather than a mention of one in prose. Those pull in opposite
directions. Matching literally missed `Item\xa01.` — Amazon and Boeing
typeset a non-breaking space there, and the platform handed its reader
an empty section, which the reader honestly reported as a filing that
described no business. Matching tolerantly found those, and promptly
took Disney's sentence "…are set forth in Item 1A" as the end of its
business description, truncating it ten thousand characters early.
Making closings require a block in turn ran Caterpillar's discussion
from twenty-eight thousand characters to a hundred and five. Every one
of those passed the unit tests; the Reference Corpus refused them.

So the two jobs are separated here:

```text
normalize for discovery      → every plausible occurrence, typography ignored
score each occurrence        → named structural evidence, for and against
set the listing aside        → a contents entry may not open what it lists
resolve the sequence         → the most coherent progression of items
close at the next peer       → the boundary is a heading, never a mention
```

Three invariants govern it, and all three are checked by tests:

1. **A typographic difference may change candidate discovery, but may
   not alone establish a section boundary.** Whitespace and case are
   presentation; a boundary needs structure.
2. **A closing boundary must be supported by structural evidence and by
   coherence with the surrounding item sequence.** The next section
   begins because the document says a peer began, not because a string
   appeared.
3. **A heading in a listing is still a heading.** It is barred from
   *opening* the item it lists and nothing more — never struck from the
   evidence, never denied to an item that has no other candidate. The
   third step exists because typography ran out: measured over 119
   block-beginning occurrences, every one of them begins a block and
   capitals are a filer's habit rather than a role, so the structure
   that separates a contents entry from the section it points at is not
   in the candidate at all. It is in what follows the candidate.

Nothing here compensates for a locator failure downstream. A section
this module cannot find is returned absent, and the reader is left to
report the absence honestly — which is what it did all along.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.providers.document_text import Flattened, begins_a_block, typesets_blocks

#: Every plausible item heading, typography ignored. Deliberately
#: permissive: discovery is not allowed to decide anything, so its only
#: failure mode that matters is missing an occurrence. `\s` covers the
#: non-breaking space a filer typesets between the word and its number,
#: which is exactly what a literal match could not see — and matching
#: this way preserves every offset, so the span cut out of the markup is
#: the span that was found.
#:
#: The dotted group reads the *other* numbering the regulator uses. An
#: annual report numbers its items `1`, `1A`, `7A`; a current report
#: numbers them `5.02`, `9.01`. Both are "Item N" to a reader and only
#: one of them was expressible here.
#:
#: It is bound as tightly as it can be, because this pattern governs the
#: annual-report path too: the dot must touch the number, exactly two
#: digits must follow it, and no third digit may. So `Item 1. 10 years
#: ago` still reads as Item 1 with its full stop, and `Item 5.02` no
#: longer reads as Item 5 with the fraction thrown away.
#: The suffix is part of the item number only where it is lexically
#: bounded. Without `(?![A-Za-z])` the optional `a`-`c` group, matched
#: case-insensitively, takes the **first letter of the section's own
#: title**: `Item 1 Business` was discovered as Item 1B, `Item 1 Company
#: overview` as Item 1C, and Honeywell's `ITEM 1 About Honeywell` as
#: Item 1A — so Honeywell's Item 1 was never a candidate at all and the
#: resolved sequence began at 1A. Measured over the 24 held annual
#: reports in `ANNUAL_SECTION_LOCATION_CORPUS.md`.
#:
#: The boundary is bound to the **suffix** rather than trailed after the
#: whole optional chain, and the difference is not cosmetic. Written as
#: `([a-c])?(?![A-Za-z])` the lookahead also fires where no suffix
#: matched, so `Item 5.02Departure` — a fraction immediately followed by
#: a title — backtracks past its own fraction and reads as a bare
#: Item 5, silently undoing #191. Written as `(?:([a-c])(?![A-Za-z]))?`
#: the constraint applies only to a suffix that actually matched, which
#: is what the defect is about.
#:
#: A genuine suffix followed by punctuation, a space or the end of the
#: text still matches: `Item 1A.`, `ITEM 1A RISK FACTORS`,
#: `Item 1A—Risk Factors`, `Item 1A`. And `match.start()` — every offset
#: into the flattened text — is untouched either way.
_CANDIDATE = re.compile(
    r"(?i)\bitem\s+(\d{1,2})(?:\.(\d{2})(?!\d))?\s*(?:([a-c])(?![A-Za-z]))?\s*[.:—-]?"
)

#: How a filer refers to a section rather than beginning one. Read from
#: the words immediately before the occurrence, because a cross-reference
#: is the tail of a sentence and a heading is not. These are the phrases
#: the corpus actually prints; the list grows only when a filing shows a
#: new one, never by imagination.
_REFERRING = (
    "set forth in",
    "described in",
    "described under",
    "discussed in",
    "included in",
    "included under",
    "contained in",
    "refer to",
    "referred to in",
    "see",
    "under",
    "in part i",
    "in part ii",
    "of this report",
    "and",
    "in",
)

#: How much text before an occurrence is read when asking whether it sits
#: inside a sentence. Long enough to carry the phrases above and the
#: clause they belong to; short enough that a previous paragraph cannot
#: reach into the judgement.
_LOOKBEHIND = 120

#: A heading occupies its own short line. Measured across the corpus:
#: the section titles run to about a hundred and twenty characters at
#: the widest, and a cross-reference sits inside a sentence far longer.
_HEADING_LINE = 160

#: A located section that is shorter than this is a listing rather than
#: the section itself — a table-of-contents entry runs a few characters
#: to its neighbour where the section runs tens of thousands. Measured:
#: JPMorgan's Item 7 is a genuine 395-character pointer to a document
#: filed separately, so this sits well below it and that pointer is
#: still read as the section it is.
_LISTING_WIDEST = 300

#: How far one entry of a listing may sit from the next and still be
#: read as part of the same listing. A contents entry's neighbour is the
#: next line of the same table; a section's neighbour is whatever the
#: prose mentions next, which is usually far away and occasionally very
#: close.
#:
#: Measured over the 24 held annual reports
#: (`CONTENTS_BODY_HEADING_SELECTION.md`): at this distance the chain
#: below runs 12 to 22 for every contents entry in the corpus and 0 or 1
#: for every body heading, and the reading of all 48 sections is
#: identical across every setting from 1,000 to 4,000 paired with a
#: chain of 5 to 10 — 49 of 54 settings agree exactly. It is a plateau
#: rather than a fitted constant, and this sits inside it.
#:
#: Widening it is not free: at 5,000 Union Pacific's *body* heading
#: chains four steps, and at 3,000 JPMorgan's pointer chains six.
_LISTING_STEP_WIDEST = 2_000

#: How long that chain must run before the candidate is reading as an
#: entry in a listing rather than as a section that happens to be
#: followed by a mention of a later item.
#:
#: Measured on the same corpus: the longest chain following anything
#: that is not a listing entry is **4** — JPMorgan's Item 7, whose Part
#: II prints Item 7, 7A, 8 and 9 as consecutive pointer blocks, which is
#: a list of items with page numbers because that is what JPMorgan
#: filed. The shortest chain following a genuine contents entry is
#: **12**, and four separate filers print exactly that. Nothing in the
#: corpus sits between 5 and 11, so this is the middle of an empty band
#: rather than a line drawn against the nearest case.
_LISTING_SHORTEST = 6


@dataclass(frozen=True, slots=True)
class Item:
    """A filing item as an orderable thing: 1, then 1A, then 2.

    Two regulator numberings, one type. An annual report counts its items
    `1`, `1A`, `2`; a current report counts them `1.01`, `5.02`, `9.01`.
    The fraction is empty for the first and set for the second, so an
    annual report's items are exactly what they were.
    """

    number: int

    suffix: str = ""

    #: The two digits after the dot, as printed — `"02"` of `5.02`.
    #: Empty for an annual report's items, which have no fraction rather
    #: than a fraction of zero.
    #:
    #: Last, and deliberately: `Item(1, "A")` meant a suffix before this
    #: field existed and still does. A new field that silently changed
    #: what an existing call means is the kind of break a type checker
    #: cannot see.
    fraction: str = ""

    @property
    def order(self) -> tuple[int, str, str]:
        """What makes 1 < 1A < 1B < 2 a fact rather than a convention.

        And 5.02 < 5.03 < 7.01 by the same line. The fraction is compared
        as the two printed digits rather than as a number, which is the
        same ordering — `"01" < "02" < "10"` — without inventing a value
        for an item that has none: a bare `Item 5` sorts before `5.02`,
        which is what a filer's own sequence does.
        """

        return (self.number, self.fraction, self.suffix)

    def stated(self) -> str:
        dotted = f".{self.fraction}" if self.fraction else ""

        return f"Item {self.number}{dotted}{self.suffix}"


@dataclass(frozen=True, slots=True)
class Evidence:
    """One structural observation about a candidate, and its direction.

    Named and kept whether it supported the candidate or not. Section
    location is authoritative evidence infrastructure now: a reader is
    owed an explanation of why the filing was cut where it was, and a
    score with no account behind it is exactly the unexplainable number
    this platform removes everywhere else.
    """

    observation: str
    supports: bool

    def stated(self) -> str:
        return f"{'+' if self.supports else '-'} {self.observation}"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One occurrence of a plausible heading, with what was observed of it."""

    item: Item

    #: Where it begins in the flattened text.
    at: int

    #: The occurrence exactly as the document typeset it.
    printed: str

    evidence: tuple[Evidence, ...]

    @property
    def supporting(self) -> int:
        return sum(1 for observed in self.evidence if observed.supports)

    @property
    def contradicting(self) -> int:
        return sum(1 for observed in self.evidence if not observed.supports)

    @property
    def is_heading(self) -> bool:
        """Whether the observations make this a heading rather than a mention.

        A single feature is never authoritative — that is the whole
        lesson of the two refused repairs. What decides is that nothing
        contradicts the candidate and something structural supports it:
        a mention inside a sentence carries a contradiction whatever
        else it has going for it, and an occurrence nothing at all
        supports is not evidence of a boundary.
        """

        return self.contradicting == 0 and self.supporting > 0

    def stated(self) -> str:
        """The candidate as a reader checks it, evidence and all."""

        lines = [f"{self.item.stated()} at offset {self.at:,} — {self.printed!r}"]
        lines.extend(f"    {observed.stated()}" for observed in self.evidence)

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class LocatedSection:
    """One section, where it was cut, and the reasoning that cut it there."""

    item: Item

    #: The span in the flattened text: where the heading begins, and
    #: where the next accepted peer heading does.
    at: int
    ends: int

    #: The candidate that opened it, and the one that closed it. The
    #: closing is absent only where the section runs to the end of the
    #: document.
    opened_by: Candidate
    closed_by: Candidate | None

    #: Every candidate for this item that was not selected, with the
    #: evidence that lost it — the other half of the explanation.
    rejected: tuple[Candidate, ...]

    @property
    def width(self) -> int:
        return self.ends - self.at

    def stated(self) -> str:
        """The full trace: what was selected, what was not, and why."""

        closing = (
            f"closed at offset {self.ends:,} by {self.closed_by.item.stated()}"
            if self.closed_by is not None
            else f"closed at offset {self.ends:,} — the end of the document"
        )

        lines = [
            f"Selected {self.item.stated()} candidate at offset {self.at:,}",
            "",
            "Evidence:",
            *(f"  {observed.stated()}" for observed in self.opened_by.evidence),
            "",
            f"{closing}; {self.width:,} characters.",
        ]

        for candidate in self.rejected:
            lines.extend(
                [
                    "",
                    f"Rejected candidate at offset {candidate.at:,}",
                    "",
                    "Evidence:",
                    *(f"  {observed.stated()}" for observed in candidate.evidence),
                ]
            )

        return "\n".join(lines)


def discover(text: str) -> tuple[tuple[Item, int, str], ...]:
    """Every plausible item heading in the text, typography ignored.

    Discovery only. Nothing here decides that an occurrence is a
    heading — the first invariant of this module is that it may not.
    """

    found = []

    for match in _CANDIDATE.finditer(text):
        number = int(match.group(1))
        fraction = match.group(2) or ""
        suffix = (match.group(3) or "").upper()

        found.append(
            (
                Item(number=number, fraction=fraction, suffix=suffix),
                match.start(),
                match.group(0),
            )
        )

    return tuple(found)


def observe(
    markup: str,
    flat: Flattened,
    at: int,
    printed: str,
    structured: bool,
) -> tuple[Evidence, ...]:
    """What can be observed structurally about one occurrence.

    Independent observations, each named, none authoritative alone.
    They are the difference between

    ```text
    ITEM 1.
    BUSINESS
    ```

    and

    ```text
    The relevant risks are set forth in Item 1A.
    ```

    which are the same string once typography is normalised away.
    """

    text = flat.text
    observed: list[Evidence] = []

    before = text[max(0, at - _LOOKBEHIND) : at]

    referring = _referring(before)

    if referring is not None:
        observed.append(
            Evidence(f"preceded by {referring!r} — a reference, not a title", False)
        )

    # Whether the filer began a block here is the load-bearing
    # observation, and it is read from the markup rather than from the
    # prose. It has to be: flattening turns every tag into a space, so
    # the reduced text of a whole 10-K carries a handful of newlines and
    # "begins its line" is not a question that can be asked of it. That
    # was measured here — an earlier draft of this module asked it
    # anyway, found 119 characters ahead of every candidate on its
    # notional line, and rejected every heading in the corpus.
    if structured:
        if begins_a_block(markup, flat, at):
            observed.append(Evidence("begins a block the filer typeset", True))
        else:
            observed.append(
                Evidence("sits inside a block the filer had already begun", False)
            )
    else:
        # No block structure to read, so position is what is left —
        # the same order of preference the rest of this platform's
        # evidence uses: structure first, position behind it.
        line_began = before.rfind("\n") + 1
        preceding = before[line_began:].strip()

        if preceding:
            observed.append(
                Evidence(
                    f"{len(preceding)} characters of prose precede it on its line",
                    False,
                )
            )
        else:
            observed.append(Evidence("begins its line", True))

    if printed.strip() == printed.strip().upper():
        observed.append(Evidence("typeset in capitals, as headings here are", True))

    return tuple(observed)


def _referring(before: str) -> str | None:
    """The cross-reference phrase this occurrence follows, if it follows one.

    Matched on whole words at the end of the preceding text. A
    substring test would find "in" at the end of "margin" and call
    every heading after that word a reference — which is the kind of
    quiet, plausible wrongness this module exists to remove.
    """

    tail = before.casefold().rstrip().rstrip(",;:")

    for phrase in _REFERRING:
        if re.search(rf"(?:^|\W){re.escape(phrase)}$", tail):
            return phrase

    return None


def candidates(markup: str, flat: Flattened) -> tuple[Candidate, ...]:
    """Every discovered occurrence, with its structural evidence attached."""

    structured = typesets_blocks(markup)

    return tuple(
        Candidate(
            item=item,
            at=at,
            printed=printed,
            evidence=observe(markup, flat, at, printed, structured),
        )
        for item, at, printed in discover(flat.text)
    )


def listing_runs(occurrences: tuple[Candidate, ...]) -> tuple[int, ...]:
    """For each occurrence, how much more of the listing follows it.

    One number per occurrence, in the order they were discovered: the
    length of the unbroken chain that follows, where every step advances
    the item sequence and no step is longer than `_LISTING_STEP_WIDEST`.
    The chain stops at the first step that goes too far or fails to
    advance — it is a run, not a count of what happens to be nearby.

    Read over **every** discovered occurrence rather than over the
    accepted ones, and that is load-bearing rather than incidental. A
    contents entry's neighbours include lines that begin no block of
    their own, and a body heading's chain is broken by exactly the prose
    cross-references the evidence layer rejects. Both belong to the
    reading; asking this question of the survivors would ask it of a
    different document.

    Deliberately blind to width, position, capitalisation, page numbers
    and the words "table of contents" — the last of which points the
    wrong way, because a filing prints it as a running page header and
    it therefore lands nearer the body heading than the contents entry
    that lists it.
    """

    runs: list[int] = []

    for index in range(len(occurrences)):
        length = 0
        cursor = index

        while cursor + 1 < len(occurrences):
            here, following = occurrences[cursor], occurrences[cursor + 1]

            if following.at - here.at > _LISTING_STEP_WIDEST:
                break

            if following.item.order <= here.item.order:
                break

            length += 1
            cursor += 1

        runs.append(length)

    return tuple(runs)


def openings(
    occurrences: tuple[Candidate, ...],
    accepted: tuple[Candidate, ...],
) -> tuple[Candidate, ...]:
    """The accepted candidates that may open a section, listings aside.

    A candidate whose chain reaches `_LISTING_SHORTEST` is an entry in a
    listing of items, and an entry in a listing is not the thing it
    lists. So it is set aside — **for its own item only, and only where
    that item has somewhere else to open.**

    Both halves of that sentence were earned by a filing.

    *For its own item only*: a contents listing is one chain running
    through Item 1, 1A, 1B, 2 and onwards, so every item in the document
    has an entry in it. Deciding eligibility per item keeps one chain
    from reaching across and unseating an item it merely passed through.

    *Only where that item has somewhere else to open*: Honeywell prints
    its item numbers **nowhere but** its "FORM 10-K CROSS-REFERENCE
    INDEX" — its sections are titled "About Honeywell" and carry no
    number at all. Struck outright, its Item 1 and Item 7 become absent,
    which is this platform reporting nothing about a filing it can
    partly read. Retained, they stay exactly what they were. The rule is
    a preference between candidates, never a veto over one.

    Order is preserved, so the resolution downstream is as deterministic
    as it was.

    One consequence is recorded rather than guarded against, because no
    filing in the acceptance corpus produces it: a retained entry is a
    full candidate, so a *fragment* of a listing — the items that have
    no body heading anywhere in the document — stays in the sequence and
    could in principle out-score the body's own run, whose steps are
    wide but few. Every filing measured either prints a body heading for
    the items it lists, collapsing the fragment to nothing, or prints
    none at all, which is Honeywell and is the case this clause is for.
    """

    runs = dict(
        zip(
            (found.at for found in occurrences),
            listing_runs(occurrences),
            strict=True,
        )
    )

    listing = {
        candidate.at: runs.get(candidate.at, 0) >= _LISTING_SHORTEST
        for candidate in accepted
    }

    elsewhere = {
        candidate.item.order for candidate in accepted if not listing[candidate.at]
    }

    return tuple(
        candidate
        for candidate in accepted
        if not listing[candidate.at] or candidate.item.order not in elsewhere
    )


def sequence(accepted: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
    """The most coherent progression of items the document describes.

    The heart of the resolution, and the reason this is not a third
    closing regex. The strongest signal about a candidate is not how it
    looks locally; it is whether choosing it builds a filing that runs
    Item 1 → Item 1A → Item 1B → Item 2 in order, with sections of
    plausible width.

    So the accepted candidates are read as a sequence and the best
    increasing run through them is chosen — increasing in item order,
    advancing in position, and rewarded for the width each step spans.
    One thing falls out of that without being a special case:

    - A prose mention of a later item cannot close a section, because
      choosing it would leave the genuine heading for that same item
      stranded later in the sequence, which no coherent run does.

    A second thing was claimed here and is false, and the correction is
    why `openings` exists. A table of contents does *not* lose to the
    body it points at: its entry for Item 1 can step straight to the
    body's Item 1A, and that single step is wider than the body's own —
    so rewarding width prefers the listing. Measured over the 24 held
    annual reports, twelve of them opened Item 1 on a contents entry
    this way, and Goldman Sachs began doing so only when #199 made its
    contents entry a candidate for the first time. Width cannot tell a
    listing from a section, and nothing here pretends otherwise now.

    Ties are broken toward the earlier position, so the resolution is
    deterministic for a given document.
    """

    if not accepted:
        return ()

    ordered = sorted(accepted, key=lambda candidate: candidate.at)

    # The best run ending at each candidate, scored by the width its
    # steps span — plus the candidate's own structural support, so a
    # well-evidenced heading is preferred where widths are comparable.
    best: list[float] = []
    previous: list[int | None] = []

    for index, candidate in enumerate(ordered):
        score = float(candidate.supporting)
        came_from: int | None = None

        for earlier in range(index):
            prior = ordered[earlier]

            if prior.item.order >= candidate.item.order:
                continue

            spanned = _width_score(candidate.at - prior.at)
            through = best[earlier] + spanned + candidate.supporting

            if through > score:
                score, came_from = through, earlier

        best.append(score)
        previous.append(came_from)

    end = max(range(len(ordered)), key=lambda index: (best[index], -ordered[index].at))

    run: list[Candidate] = []
    cursor: int | None = end

    while cursor is not None:
        run.append(ordered[cursor])
        cursor = previous[cursor]

    return tuple(reversed(run))


def _width_score(width: int) -> float:
    """How much a step of this width looks like one section following another.

    A listing's steps are a few characters; a document's real sections
    are thousands. Deliberately flattening above that: this has to tell
    a contents entry from a section, and it must not become a preference
    for the *widest* reading — which is precisely the over-read the
    structural rule was introduced to remove.
    """

    if width <= _LISTING_WIDEST:
        return 0.0

    return min(width / 10_000.0, 3.0)


def locate(
    markup: str,
    flat: Flattened,
    wanted: Item,
) -> LocatedSection | None:
    """One item's section, resolved through the document's own sequence.

    Nothing where the document's coherent sequence does not contain the
    item. A section that cannot be located is absent, and stays absent:
    returning the wrong part of a filing and reading it as though it
    were the right one is the failure this whole module exists to stop.
    """

    found = candidates(markup, flat)
    accepted = tuple(candidate for candidate in found if candidate.is_heading)

    run = sequence(openings(found, accepted))

    for index, candidate in enumerate(run):
        if candidate.item.order != wanted.order:
            continue

        following = run[index + 1] if index + 1 < len(run) else None

        return LocatedSection(
            item=wanted,
            at=candidate.at,
            ends=following.at if following is not None else len(flat.text),
            opened_by=candidate,
            closed_by=following,
            rejected=tuple(
                other
                for other in found
                if other.item.order == wanted.order and other.at != candidate.at
            ),
        )

    return None
