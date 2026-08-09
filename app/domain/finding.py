"""A single thing a signal observed, and what it says."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from hashlib import blake2b


class Sense(StrEnum):
    """Whether a finding argues for the security, against it, or neither."""

    FAVOURABLE = "favourable"
    ADVERSE = "adverse"

    #: Measured, and it argues neither way. A price that moved 0.4% and a
    #: P/E in the middle of its range are observations, not arguments.
    #: So is an absence: "Forward P/E unavailable." reports that nothing
    #: could be read, which is never a point for or against.
    NEUTRAL = "neutral"


class Dimension(StrEnum):
    """Which reading produced a finding — the signal that observed it.

    Preserved, never inferred. Every finding on this platform is
    composed at a point where the producing signal is known by name:
    `signals.value.evidence`, `signals.quality.evidence`, the risk
    signal's own list, the fundamental analysts' verdicts. That
    knowledge used to be dropped at composition, exactly as `Sense` was
    dropped before it, so a later layer wanting to ask *what did the
    valuation reading find?* had to guess from the wording.

    A committee's remit is a set of these. Reading a remit off preserved
    provenance is the difference between a committee that reports what a
    reading found and one that pattern-matches sentences.
    """

    QUALITY = "quality"
    VALUATION = "valuation"
    MOMENTUM = "momentum"
    RISK = "risk"
    RESEARCH = "research"

    #: The company's own calendar. Dated, and never an argument: a
    #: company reporting soon is neither a reason to buy nor to sell.
    SCHEDULE = "schedule"

    #: Composed before this vocabulary existed, or by a caller that
    #: states no signal. Never guessed at from the statement's words.
    UNATTRIBUTED = "unattributed"


@dataclass(frozen=True, slots=True)
class Finding:
    """
    One observation, carrying the sense the signal read it with.

    Findings used to be bare strings, so nothing downstream could tell
    "Large-cap company." from "Negative earnings." — and an investment
    case could not state a security's strengths without also stating its
    weaknesses as if they were strengths. The signal knows the difference
    at the moment it scores; this is where that knowledge stopped being
    thrown away.

    The same argument added `dimension`, one layer later and for the
    same reason: the signal also knows which reading it is, and a
    committee cannot state its own remit's findings from a list that
    forgot which reading produced each one.
    """

    statement: str
    sense: Sense
    dimension: Dimension = Dimension.UNATTRIBUTED

    @classmethod
    def favourable(cls, statement: str, dimension: Dimension | None = None) -> Finding:
        return cls(
            statement=statement,
            sense=Sense.FAVOURABLE,
            dimension=dimension or Dimension.UNATTRIBUTED,
        )

    @classmethod
    def adverse(cls, statement: str, dimension: Dimension | None = None) -> Finding:
        return cls(
            statement=statement,
            sense=Sense.ADVERSE,
            dimension=dimension or Dimension.UNATTRIBUTED,
        )

    @classmethod
    def neutral(cls, statement: str, dimension: Dimension | None = None) -> Finding:
        return cls(
            statement=statement,
            sense=Sense.NEUTRAL,
            dimension=dimension or Dimension.UNATTRIBUTED,
        )

    def about(self, dimension: Dimension) -> Finding:
        """The same finding, attributed to the reading that produced it.

        For composition sites that know the signal but receive findings
        already built. Attribution is only ever applied where the caller
        holds the producing signal — never derived from the statement.
        """

        return Finding(
            statement=self.statement,
            sense=self.sense,
            dimension=dimension,
        )

    @property
    def ref(self) -> str:
        """A stable address for this finding, derived from its content.

        Content-addressed rather than positional, so a reference means
        the same thing across two cycles and cannot silently come to
        point at a different finding when the order a signal reports in
        changes. All three fields are hashed because all three are what
        makes a finding distinct — the identical sentence read by the
        quality signal and by an analyst is two observations, and the
        deduplication this platform already performs treats them so.
        """

        content = " ".join((self.dimension.value, self.sense.value, self.statement))

        digest = blake2b(content.encode("utf-8"), digest_size=5)

        return f"finding:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class FindingLedger:
    """Every finding read about one security, each one addressable.

    The canonical list a committee opinion points into. It exists so
    that an opinion can carry *references* rather than restated prose:
    a committee that quoted its own wording could say something the
    platform never read, and nothing downstream could tell the two
    apart.

    Order is the order the signals reported, and it is not a ranking.
    This platform does not measure how strong a finding is, so anything
    that presented the first entry as the strongest would be publishing
    an ordering nobody measured.
    """

    findings: tuple[Finding, ...] = ()

    @classmethod
    def of(cls, findings: Iterable[Finding]) -> FindingLedger:
        """The ledger of these findings, each kept once."""

        return cls(findings=tuple(dict.fromkeys(findings)))

    def __iter__(self) -> Iterator[Finding]:
        return iter(self.findings)

    def __len__(self) -> int:
        return len(self.findings)

    @property
    def refs(self) -> tuple[str, ...]:
        return tuple(finding.ref for finding in self.findings)

    def resolve(self, ref: str) -> Finding | None:
        """The finding at this address, or nothing where it is not here.

        Nothing rather than a raised error: a reference that does not
        resolve is a defect in whoever composed it, and a surface that
        crashed on one would take an entire dossier down over a single
        stale address.
        """

        return next(
            (finding for finding in self.findings if finding.ref == ref),
            None,
        )

    def statements_for(self, refs: Iterable[str]) -> tuple[str, ...]:
        """The wording of these references, skipping any that do not resolve."""

        resolved = (self.resolve(ref) for ref in refs)

        return tuple(finding.statement for finding in resolved if finding is not None)

    def where(
        self,
        *,
        sense: Sense | None = None,
        dimensions: frozenset[Dimension] | None = None,
    ) -> tuple[Finding, ...]:
        """The findings matching a sense, a set of readings, or both."""

        return tuple(
            finding
            for finding in self.findings
            if (sense is None or finding.sense is sense)
            and (dimensions is None or finding.dimension in dimensions)
        )


def statements(findings: tuple[Finding, ...]) -> tuple[str, ...]:
    """Every finding, as text, in the order it was observed."""

    return tuple(finding.statement for finding in findings)


def statements_where(
    findings: tuple[Finding, ...],
    sense: Sense,
) -> tuple[str, ...]:
    """The findings that argue one particular way, as text."""

    return tuple(finding.statement for finding in findings if finding.sense is sense)
