"""How far the grounded selector reaches today, measured over the book.

A measurement of this platform, not of any company. Every security the
investor holds or watches is asked the same questions — how wide is the
stored knowledge, does it reach quorum, what does the selector serve —
and every company the grounded route cannot serve authoritatively is
charged with **exactly one blocker**: the next cheapest established
claim that would unlock it. Not a diagnosis, not a paragraph — one
claim, so the distribution of blockers is a roadmap the numbers wrote.

Read-only by construction: the service that fills this consults the
knowledge store as it stands and never resolves, fetches or reads a
document. A report that could acquire would measure what the platform
could know, which is a different quantity from what it knows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from app.domain.knowledge_consensus import QUORUM
from app.domain.playbook import PlaybookKind


class CoverageOrigin(StrEnum):
    """Where a security entered the measured population from."""

    PORTFOLIO = "portfolio"
    WATCHLIST = "watchlist"
    BOTH = "portfolio and watchlist"


class CoverageOutcome(StrEnum):
    """What the selector serves for this security today.

    Three different claims, never blended: an authoritative grounded
    selection, the reported-industry route serving as recorded
    fallback, and the honest double absence where neither route decided
    anything on evidence.
    """

    GROUNDED = "grounded"
    FALLBACK = "industry fallback"
    UNCLASSIFIED = "unclassified"


class Blocker(StrEnum):
    """The one established claim standing between a company and an
    authoritative grounded playbook.

    A closed vocabulary on purpose: a distribution over free text is a
    pile of paragraphs, and the point of this measurement is arithmetic
    over comparable absences. Each member names what is missing;
    `unlocked_by` words the cheapest way to establish it.
    """

    NOT_READ = "no filing read"
    BELOW_QUORUM = "below quorum"
    SEGMENTS_UNSETTLED = "segments unsettled"
    NO_REVENUE_MECHANISMS = "no revenue mechanisms established"
    NO_SEGMENT_SIZES = "no measured segment sizes"
    TOO_LITTLE_EXPLAINED = "under half of revenue explained"
    NO_MAPPING = "no deterministic mapping"
    NO_PRIMARY_SOURCE = "no primary source"

    @property
    def unlocked_by(self) -> str:
        """The next cheapest established claim, worded."""

        return _UNLOCKED_BY[self]


_UNLOCKED_BY: dict[Blocker, str] = {
    Blocker.NOT_READ: (
        "one reading of its current filing — the first stored observation"
    ),
    Blocker.BELOW_QUORUM: (
        f"observations of the current filing up to the quorum of {QUORUM} "
        "(movrvest observe — a counted spend, no new engineering)"
    ),
    Blocker.SEGMENTS_UNSETTLED: (
        "observations that agree which segments the filing names"
    ),
    Blocker.NO_REVENUE_MECHANISMS: (
        "one segment's way of earning established — a description read "
        "under the section the filer printed it in"
    ),
    Blocker.NO_SEGMENT_SIZES: ("one segment size proven against a table in the filing"),
    Blocker.TOO_LITTLE_EXPLAINED: (
        "ways of earning established for segments worth half of measured revenue"
    ),
    Blocker.NO_MAPPING: (
        "a playbook rule earned for its concluded archetype — case by "
        "case, per PLAYBOOK_SELECTION.md, never ahead of one"
    ),
    Blocker.NO_PRIMARY_SOURCE: (
        "nothing — this security files no report, and grounded selection "
        "does not apply to it"
    ),
}


@dataclass(frozen=True, slots=True)
class SecurityCoverage:
    """One security's answer to the measurement's questions."""

    symbol: str
    origin: CoverageOrigin

    #: How many stored observations the newest filing has. Zero where
    #: nothing was ever read.
    width: int
    quorate: bool

    #: Whether any consensus exists to derive an understanding from.
    understanding: bool

    outcome: CoverageOutcome

    #: The playbook actually served today, by whichever route.
    playbook: PlaybookKind

    #: The one thing in the way of an authoritative grounded selection.
    #: None exactly when the outcome is grounded.
    blocker: Blocker | None

    #: The blocker made specific to this company — which claim, for
    #: which segment or conclusion — in one line.
    blocking_claim: str | None

    #: An absence in the measurement itself (a provider that errored
    #: while the industry route was consulted), carried with its reason
    #: rather than silently folded into an outcome.
    note: str | None = None


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """The measured population, and the arithmetic over it."""

    securities: tuple[SecurityCoverage, ...]

    @property
    def total(self) -> int:
        return len(self.securities)

    @property
    def grounded(self) -> tuple[SecurityCoverage, ...]:
        return self._with(CoverageOutcome.GROUNDED)

    @property
    def fallbacks(self) -> tuple[SecurityCoverage, ...]:
        return self._with(CoverageOutcome.FALLBACK)

    @property
    def unclassified(self) -> tuple[SecurityCoverage, ...]:
        return self._with(CoverageOutcome.UNCLASSIFIED)

    @property
    def quorate(self) -> int:
        return sum(1 for security in self.securities if security.quorate)

    @property
    def below_quorum(self) -> int:
        return sum(1 for security in self.securities if 0 < security.width < QUORUM)

    @property
    def unread(self) -> int:
        return sum(1 for security in self.securities if security.width == 0)

    @property
    def grounded_kinds(self) -> tuple[tuple[PlaybookKind, int], ...]:
        """Which grounded playbooks serve, widest first."""

        counted = Counter(security.playbook for security in self.grounded)

        return tuple(
            sorted(counted.items(), key=lambda pair: (-pair[1], pair[0].value))
        )

    @property
    def blocker_distribution(self) -> tuple[tuple[Blocker, int], ...]:
        """Every blocker over the population, most common first."""

        counted = Counter(
            security.blocker
            for security in self.securities
            if security.blocker is not None
        )

        return tuple(
            sorted(counted.items(), key=lambda pair: (-pair[1], pair[0].value))
        )

    @property
    def blocked(self) -> tuple[SecurityCoverage, ...]:
        """Every security charged with a blocker, for the table."""

        return tuple(
            security for security in self.securities if security.blocker is not None
        )

    def _with(self, outcome: CoverageOutcome) -> tuple[SecurityCoverage, ...]:
        return tuple(
            security for security in self.securities if security.outcome is outcome
        )
