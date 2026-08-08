"""Where a filing's audited financial statements are, and why there.

The second application of the boundary architecture in
`section_locator`, and it exists for the same reason the first one
does: a title match is not a location. Measured on JPMorgan, the string
"consolidated balance sheets" begins a block in five different places —
a contents entry, the MD&A's *Consolidated balance sheets and cash
flows analysis*, the audited statement, and two more — and the widest
of them is not the audited statement. The figures read out of the wrong
one were genuine, checked, internally consistent and the filer's own.
They were simply not the audited balance sheet, and nothing downstream
could see that. **A figure that is right whose provenance claim is
wrong** is the failure this module removes.

The generalisation is the point. `section_locator` resolves the most
coherent progression of *numbered items*; this resolves the most
coherent progression of *statements*. What changed is the vocabulary,
not the idea:

```text
normalize for discovery   → every plausible occurrence, typography ignored
score each occurrence     → named structural evidence, for and against
resolve the run           → the most coherent progression of statements
close at the next peer    → the boundary is the statement that follows
```

**A statement is selected because it belongs to the highest-quality
structural run, never because its title matched first.** Which makes
the three failing shapes fall out of one rule rather than three
special cases:

- **A contents page** — its members are listings, a few characters to
  the next. A progression, but of nothing.
- **An MD&A discussion** — isolated: one statement's title, with no
  sibling statements around it.
- **A pointer item** — Item 8 saying "appear on pages 162–314" holds
  no statement title at all, so it is a candidate for nothing.
- **The audited statements** — several *different* statements, each
  running thousands of characters. The only shape with both.

Two things this module refuses to do, and both were named before it was
written. It does not prefer a candidate for sitting under Item 8, for
being capitalised, or for not being called "Selected" — those are
localised heuristics, and the Reference Corpus has already refused two
of that kind. And it does not fall back: a statement absent from the
selected run is **absent**, even where its title appears elsewhere in
the document. Interpretation never outruns evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.financial_statements import StatementKind
from app.providers.document_text import Flattened, typesets_blocks
from app.providers.section_locator import Evidence, observe

#: The titles filers typeset over each primary statement. Singular and
#: plural are listed apart because discovery matches whole words: a
#: pattern for "sheet" does not match "sheets", which is what keeps the
#: two from being one fuzzy rule.
TITLES: dict[StatementKind, tuple[str, ...]] = {
    StatementKind.INCOME_STATEMENT: (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
    ),
    StatementKind.BALANCE_SHEET: (
        "consolidated balance sheets",
        "consolidated balance sheet",
        "consolidated statements of financial position",
        "consolidated statement of financial position",
    ),
    StatementKind.CASH_FLOW_STATEMENT: (
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
    ),
}

#: The statements a filer prints between and after the ones this
#: platform reads, and the notes heading that follows them all.
#:
#: They close a section without opening one, and they have to exist
#: here for a reason the fixtures make plain: a run's last member would
#: otherwise swallow every statement printed after it. Comprehensive
#: income sits immediately behind the income statement in most US
#: filings, and this platform reads no concept from it — but the filer
#: printed it, so it is where the income statement ends.
#:
#: The asymmetry is deliberate. Opening a section requires structural
#: evidence and membership of a run; closing one requires only that the
#: filer named the next statement. Requiring closings to begin a block
#: is the repair that ran Caterpillar's discussion from 28,000
#: characters to 105,000, and it is not made here.
_PEERS = (
    "consolidated statements of comprehensive income",
    "consolidated statement of comprehensive income",
    "consolidated statements of changes in",
    "consolidated statement of changes in",
    "consolidated statements of stockholders",
    "consolidated statement of stockholders",
    "consolidated statements of shareholders",
    "consolidated statements of equity",
    "consolidated statement of equity",
    "notes to consolidated financial statements",
    "notes to the consolidated financial statements",
    "notes to the financial statements",
    "report of independent registered public accounting firm",
)

#: How far apart two statements may sit and still be one run.
#:
#: Reasoned from a measured shape, and **deliberately erring small**,
#: which is the half of this constant that matters. On JPMorgan the
#: three statements sit 2,675 and 5,911 characters apart; a filer that
#: prints comprehensive income and changes in equity between them —
#: this vocabulary reads neither — pushes that into the tens of
#: thousands.
#:
#: The two failure directions are not symmetric, so the constant is not
#: chosen to sit in the middle of them:
#:
#: - **Too small** splits a real audited block into two runs. The
#:   higher-substance part still wins, and the statements that fell out
#:   of it are reported *absent*. An honest gap.
#: - **Too large** lets a discussion of a statement, printed near the
#:   audited block, join the run — and where it supplies a statement the
#:   audited block lacks, it is located and served as that statement.
#:   A wrong provenance claim, which is the failure this whole module
#:   exists to remove.
#:
#: So it is set to hold a genuine block together across one intervening
#: statement, and no wider. It decides grouping only; nothing is ever
#: selected by proximity.
RUN_GAP = 30_000

#: Below this width a located statement is a listing rather than a
#: statement: a contents entry runs a few characters to its neighbour
#: where the statement itself runs thousands. The same measured
#: constant `section_locator` uses on items, for the same reason.
LISTING_WIDEST = 300

#: How far past the last statement of a run to read where the filing
#: prints no notes heading after it.
_LAST_WIDEST = 80_000


@dataclass(frozen=True, slots=True)
class StatementCandidate:
    """One occurrence of a statement title, with what was observed of it."""

    statement: StatementKind

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
        """Whether the observations make this a title rather than a mention.

        The identical rule `section_locator.Candidate` holds, and it is
        identical deliberately: nothing contradicts it and something
        structural supports it. One feature is never authoritative.
        """

        return self.contradicting == 0 and self.supporting > 0

    def stated(self) -> str:
        lines = [
            f"{self.statement.value} at offset {self.at:,} — {self.printed!r}",
        ]
        lines.extend(f"    {observed.stated()}" for observed in self.evidence)

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class Run:
    """A progression of statements, and how much of one it is.

    Quality is `substance`: how many *different* statements the run
    carries at more than a listing's width. That one number separates
    every shape this module has to tell apart, without knowing anything
    about any of them — a contents page has three statements and no
    substance, a discussion has substance and one statement, and the
    audited block has both.
    """

    members: tuple[StatementCandidate, ...]

    #: Each member's width: to the next member, and for the last one to
    #: whatever closes the run.
    widths: tuple[int, ...]

    @property
    def substance(self) -> int:
        """How many different statements this run carries, listings aside."""

        return len(
            {
                member.statement
                for member, width in zip(self.members, self.widths, strict=True)
                if width >= LISTING_WIDEST
            }
        )

    @property
    def supporting(self) -> int:
        """The structural evidence behind the whole run."""

        return sum(member.supporting for member in self.members)

    @property
    def quality(self) -> tuple[int, int]:
        """What makes one run better than another, in order.

        Substance first, and it is almost always decisive. Supporting
        evidence breaks a tie between two runs carrying the same
        statements — and where even that ties, `resolve` returns
        nothing rather than choosing, because two runs that are
        structurally indistinguishable are a question this module
        cannot answer and must not pretend to.
        """

        return (self.substance, self.supporting)

    def of(self, statement: StatementKind) -> tuple[StatementCandidate, ...]:
        """This run's members for one statement, widest first."""

        found = [
            (width, member)
            for member, width in zip(self.members, self.widths, strict=True)
            if member.statement is statement
        ]

        return tuple(member for _, member in sorted(found, key=lambda m: -m[0]))

    def width_of(self, candidate: StatementCandidate) -> int:
        for member, width in zip(self.members, self.widths, strict=True):
            if member.at == candidate.at:
                return width

        return 0


@dataclass(frozen=True, slots=True)
class LocatedStatements:
    """Where each audited statement begins and ends, and the reasoning."""

    #: The run that was selected, or None where none could be.
    run: Run | None

    #: Per statement: where it begins and ends in the flattened text.
    #: A statement absent from the selected run is absent here, even
    #: where its title appears elsewhere in the document.
    spans: dict[StatementKind, tuple[int, int]]

    #: How many candidates the selected run held for each statement.
    #: One is the resolved case. More means the run itself was
    #: ambiguous, and the figures carry that.
    contenders: dict[StatementKind, int]

    #: The runs that lost, and every candidate outside the winner.
    rejected: tuple[Run, ...]

    #: Why nothing was selected, where nothing was.
    unresolved_because: str | None = None

    def span(self, statement: StatementKind) -> tuple[int, int] | None:
        return self.spans.get(statement)

    def stated(self) -> str:
        """The full trace: what was selected, what was not, and why."""

        if self.run is None:
            return self.unresolved_because or "No statement run was resolved."

        lines = [
            f"Selected a run of {self.run.substance} statements "
            f"at offset {self.run.members[0].at:,}",
            "",
        ]

        for member, width in zip(self.run.members, self.run.widths, strict=True):
            lines.append(f"  {member.statement.value}: {width:,} characters")
            lines.extend(f"    {observed.stated()}" for observed in member.evidence)

        for losing in self.rejected:
            lines.extend(
                [
                    "",
                    f"Rejected a run of {losing.substance} statements at offset "
                    f"{losing.members[0].at:,} "
                    f"({len(losing.members)} title occurrences)",
                ]
            )

        return "\n".join(lines)


def _pattern(title: str) -> re.Pattern[str]:
    """One title, matched however the filer spaced it.

    Whitespace tolerance belongs to discovery and only to discovery.
    `\\s` covers the non-breaking space a filer typesets inside a
    heading, and matching this way preserves every offset — so the span
    found is the span cut. Deciding whether an occurrence is a title is
    a separate job, done by `observe`, and keeping the two apart is the
    lesson the item locator paid for.
    """

    return re.compile(r"(?i)\b" + r"\s+".join(map(re.escape, title.split())) + r"\b")


def discover(text: str) -> tuple[tuple[StatementKind, int, str], ...]:
    """Every plausible statement title, typography ignored, offsets kept.

    Where two titles match at one offset the longer wins — "consolidated
    statements of financial position" is not two findings because
    something shorter also matched inside it.
    """

    found: dict[int, tuple[StatementKind, str]] = {}

    for statement, titles in TITLES.items():
        for title in titles:
            for match in _pattern(title).finditer(text):
                at = match.start()
                printed = match.group(0)

                held = found.get(at)

                if held is None or len(printed) > len(held[1]):
                    found[at] = (statement, printed)

    return tuple(
        (statement, at, printed) for at, (statement, printed) in sorted(found.items())
    )


def candidates(markup: str, flat: Flattened) -> tuple[StatementCandidate, ...]:
    """Every discovered occurrence, with its structural evidence attached."""

    structured = typesets_blocks(markup)

    return tuple(
        StatementCandidate(
            statement=statement,
            at=at,
            printed=printed,
            evidence=observe(markup, flat, at, printed, structured),
        )
        for statement, at, printed in discover(flat.text)
    )


def _closes(text: str, after: int) -> int:
    """Where a run's last statement ends: the next statement, or a reach.

    The next thing the filer printed, whether or not this platform
    reads it. Nothing is read past a peer's title, so the last member of
    a run cannot absorb the statements that follow it.
    """

    lowered = text.casefold()

    ends = [at for peer in _PEERS if (at := lowered.find(peer, after)) != -1]

    return min(ends) if ends else min(after + _LAST_WIDEST, len(text))


def runs(
    accepted: tuple[StatementCandidate, ...],
    text: str,
) -> tuple[Run, ...]:
    """Group titles into progressions, and measure each member's width.

    A run breaks where the next title is further away than any audited
    block is wide. Grouping is all this does — nothing is selected here,
    and the gap decides only what sits beside what.
    """

    if not accepted:
        return ()

    ordered = sorted(accepted, key=lambda candidate: candidate.at)

    grouped: list[list[StatementCandidate]] = [[ordered[0]]]

    for candidate in ordered[1:]:
        if candidate.at - grouped[-1][-1].at > RUN_GAP:
            grouped.append([candidate])
        else:
            grouped[-1].append(candidate)

    built = []

    for group in grouped:
        widths = []

        for index, member in enumerate(group):
            # A member ends at whichever comes first: the next statement
            # of the run, or a statement the filer printed between them
            # that this platform does not read. Comprehensive income
            # sits between the income statement and the balance sheet in
            # most US filings, and a member closed only at the next run
            # member would carry it.
            following = group[index + 1].at if index + 1 < len(group) else len(text)

            widths.append(min(_closes(text, member.at + 1), following) - member.at)

        built.append(Run(members=tuple(group), widths=tuple(widths)))

    return tuple(built)


def resolve(built: tuple[Run, ...]) -> tuple[Run | None, str | None]:
    """The highest-quality run, or nothing with the reason worded.

    Strictly best or nothing. Two runs of equal quality are a question
    the document did not answer, and choosing between them by position,
    capitalisation or the item they sit under is exactly the localised
    repair this architecture exists to avoid making.
    """

    substantial = tuple(run for run in built if run.substance > 0)

    if not substantial:
        return (
            None,
            "No run of statement titles in this document carries a statement "
            "wider than a contents listing, so this platform located no "
            "audited financial statements. This is a fact about the reading, "
            "not about the company.",
        )

    best = max(substantial, key=lambda run: run.quality)
    tied = [run for run in substantial if run.quality == best.quality]

    if len(tied) > 1:
        return (
            None,
            f"{len(tied)} runs of statement titles in this document are "
            "structurally indistinguishable — the same statements, at the "
            "same width, with the same evidence — so which holds the audited "
            "statements was not established, and none was chosen.",
        )

    return best, None


def locate(markup: str, flat: Flattened) -> LocatedStatements:
    """The audited statements, resolved as the run they are.

    Nothing where the document offers no coherent run. A statement this
    module cannot place is absent and stays absent: returning a
    discussion of a statement and reading it as the statement is the
    failure the whole module exists to stop.
    """

    found = candidates(markup, flat)
    accepted = tuple(candidate for candidate in found if candidate.is_heading)

    built = runs(accepted, flat.text)
    selected, because = resolve(built)

    if selected is None:
        return LocatedStatements(
            run=None,
            spans={},
            contenders={},
            rejected=built,
            unresolved_because=because,
        )

    spans: dict[StatementKind, tuple[int, int]] = {}
    contenders: dict[StatementKind, int] = {}

    for statement in StatementKind:
        held = selected.of(statement)

        substantial = tuple(
            candidate
            for candidate in held
            if selected.width_of(candidate) >= LISTING_WIDEST
        )

        contenders[statement] = len(substantial)

        if not substantial:
            continue

        # Widest first, so this is the substantive occurrence. Where the
        # run holds more than one, `contenders` says so and the figures
        # carry the caveat rather than the choice being hidden.
        chosen = substantial[0]

        spans[statement] = (chosen.at, chosen.at + selected.width_of(chosen))

    return LocatedStatements(
        run=selected,
        spans=spans,
        contenders=contenders,
        rejected=tuple(run for run in built if run is not selected),
    )
