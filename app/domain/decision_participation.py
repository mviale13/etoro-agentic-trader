"""What the evidence says, and whether there is enough of it to act.

`DECISION_KERNEL_ALGEBRA.md` (#138) measured that the vote was carrying
two questions in one number. UNKNOWN scored `0`, so absence sat on the
same axis as `+1` and `−1`, and forgetting an adverse reading was
scored better than keeping it.

The separation this module makes:

- **Direction** — what the readings the platform actually holds say.
  Computed over *participating* signals at their **original weights**,
  with no renormalisation, so a survivor never gains authority by a
  neighbour's absence. Arithmetically this is what the vote always
  computed; what changes is that abstention is now visible rather than
  disguised as a zero vote.
- **Authority** — whether the platform holds enough of the evidence it
  expected to act on that direction at all. A separate question with a
  separate answer, and the reason the two were conflated is that a
  scalar cannot carry both.

Three participation states, and the distinction between the last two
is the one #138 found missing:

- **PARTICIPATING** — the signal expressed an analytical reading. A
  genuine NEUTRAL participates: *the evidence says middling* is a
  reading, and it contributes zero to the direction while counting
  fully towards coverage.
- **EXPECTED_ABSENT** — the question applies to this security and the
  platform has no answer: unread, inadmissible, or unknown. It stays
  in the expected set, so its absence lowers coverage. That is the
  whole mechanism by which ignorance withdraws authority instead of
  voting.
- **NOT_APPLICABLE** — the question does not apply. A fund has no
  earnings to be priced against. It leaves the expected set entirely
  rather than counting as a gap, because counting it would make the
  platform permanently unauthorised about instruments it understands
  perfectly well.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

#: Relative coverage an actionable call requires: every applicable
#: signal must have spoken. `market-cap-input-eligibility@1`'s
#: measurement showed why nothing lower is clean — at any floor below
#: 1.00 a deletion can still leave enough coverage to act, and the
#: deletion is precisely the case this gate exists to catch.
REQUIRED_RELATIVE_COVERAGE = 1.0

#: Participating signals an actionable call requires, regardless of
#: coverage. **Deliberately not expressible as relative coverage**: a
#: security with one applicable signal has 100% coverage by
#: construction, and #138 measured that this makes a fund a BUY on
#: momentum alone. Relative coverage protects against deletion;
#: this protects against a degenerate expected set. They are different
#: failures and neither implies the other.
REQUIRED_PARTICIPATING_SIGNALS = 2


class SignalParticipation(StrEnum):
    """Whether a signal takes part in the directional vote, and why not."""

    #: Expressed an analytical reading — including a genuine NEUTRAL.
    PARTICIPATING = "participating"

    #: Applicable, and the platform has no reading. Unread,
    #: inadmissible or unknown; the three are one state *here* because
    #: the vote's question is only "did it speak", and why it did not
    #: is carried on the signal itself.
    EXPECTED_ABSENT = "expected_absent"

    #: The question does not apply to this security at all.
    NOT_APPLICABLE = "not_applicable"

    @property
    def votes(self) -> bool:
        return self is SignalParticipation.PARTICIPATING

    @property
    def expected(self) -> bool:
        """Whether this signal counts towards the coverage denominator."""

        return self is not SignalParticipation.NOT_APPLICABLE

    @property
    def stated(self) -> str:
        return _PARTICIPATION_LABELS[self]


_PARTICIPATION_LABELS = {
    SignalParticipation.PARTICIPATING: "expressed a reading",
    SignalParticipation.EXPECTED_ABSENT: "expected, and not established",
    SignalParticipation.NOT_APPLICABLE: "not a question for this security",
}


class AuthorityGap(StrEnum):
    """Why a direction may not be acted on."""

    #: Some applicable signal did not speak.
    RELATIVE_COVERAGE = "relative_coverage"

    #: Too few signals spoke, however complete the expected set was.
    ABSOLUTE_BREADTH = "absolute_breadth"

    @property
    def stated(self) -> str:
        return _GAP_LABELS[self]


_GAP_LABELS = {
    AuthorityGap.RELATIVE_COVERAGE: (
        "not every applicable signal has been established"
    ),
    AuthorityGap.ABSOLUTE_BREADTH: (
        "too few signals expressed a reading to act on their agreement"
    ),
}


@dataclass(frozen=True, slots=True)
class SignalStanding:
    """One signal's part in the decision."""

    name: str
    weight: float
    participation: SignalParticipation

    #: The reading's direction: `+1`, `0`, `−1`. `None` where the
    #: signal did not participate — never zero, which is a reading.
    direction: int | None = None

    @property
    def contribution(self) -> float:
        """What this adds to the directional score."""

        if self.direction is None:
            return 0.0

        return self.weight * self.direction


@dataclass(frozen=True, slots=True)
class DecisionAuthority:
    """Whether the platform may act on the direction it computed.

    Two independent gates. A caller cannot collapse them: both are
    reported, and `gaps` names each one that failed, so a surface can
    say *the evidence leans bullish and we do not hold enough of it*
    rather than reporting equivocation the platform never measured.
    """

    standings: tuple[SignalStanding, ...]

    @property
    def applicable(self) -> tuple[SignalStanding, ...]:
        return tuple(s for s in self.standings if s.participation.expected)

    @property
    def participating(self) -> tuple[SignalStanding, ...]:
        return tuple(s for s in self.standings if s.participation.votes)

    @property
    def applicable_weight(self) -> float:
        return sum(s.weight for s in self.applicable)

    @property
    def participating_weight(self) -> float:
        return sum(s.weight for s in self.participating)

    @property
    def relative_coverage(self) -> float:
        """Share of the applicable expected set that spoke.

        Zero where nothing applies — a security the platform has no
        questions for is not thereby fully covered.
        """

        if self.applicable_weight <= 0:
            return 0.0

        return self.participating_weight / self.applicable_weight

    @property
    def participating_count(self) -> int:
        return len(self.participating)

    @property
    def gaps(self) -> tuple[AuthorityGap, ...]:
        """Every gate that failed, so a reader learns which and not just that."""

        failed: list[AuthorityGap] = []

        if self.relative_coverage < REQUIRED_RELATIVE_COVERAGE:
            failed.append(AuthorityGap.RELATIVE_COVERAGE)

        if self.participating_count < REQUIRED_PARTICIPATING_SIGNALS:
            failed.append(AuthorityGap.ABSOLUTE_BREADTH)

        return tuple(failed)

    @property
    def may_act(self) -> bool:
        return not self.gaps

    @property
    def stated(self) -> str:
        """What the platform may do with the direction, worded once."""

        if self.may_act:
            return (
                f"{self.participating_count} of "
                f"{len(self.applicable)} applicable signals established."
            )

        reasons = " and ".join(gap.stated for gap in self.gaps)

        return (
            f"The direction is not actionable: {reasons} "
            f"({self.participating_count} of {len(self.applicable)} "
            "applicable signals established)."
        )
