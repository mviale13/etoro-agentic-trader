"""Whether Quality has seen enough to band a business at all.

`QUALITY_BAND_RULER.md` (#140) measured the defect this answers: a
company that passed **every factor the platform could read** banded
LOW and voted `−1`, because the ruler compared absolute points against
a fixed three-factor maximum. Apple scored its one readable factor and
was called poor quality; a company that *failed* its one readable
factor was called exactly the same thing.

The separation, mirroring `decision-authority@1` one layer up:

- **performance** — how many applicable factors passed, over how many
  were read. A fact about the business, as far as it goes.
- **coverage** — how much of the applicable factor set was readable at
  all. Its own docstring on `QualitySignal.available` has always said
  this is "a statement about the reading rather than about the
  business".
- **authority** — whether coverage is complete enough for the band to
  be a claim about the business rather than about the reading.

Only after authority is established does the existing LOW/MEDIUM/HIGH
ruler run, unchanged. Short of it Quality **abstains**: not LOW, not
neutral, not a zero score and not a synthetic band — the honest state
the signal already had for "nothing readable", now reached for
"not enough readable".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.decision_participation import SignalParticipation


class QualityFactor(StrEnum):
    """The factors business quality is judged on.

    Named rather than counted, because #140 found the platform could
    not say *which* factor it was missing — only how many.
    """

    MARKET_SIGNIFICANCE = "market_significance"
    EARNINGS = "earnings"
    DIVIDEND = "dividend"

    @property
    def stated(self) -> str:
        return _FACTOR_LABELS[self]


_FACTOR_LABELS = {
    QualityFactor.MARKET_SIGNIFICANCE: "company size",
    QualityFactor.EARNINGS: "earnings",
    QualityFactor.DIVIDEND: "dividend",
}


@dataclass(frozen=True, slots=True)
class FactorStanding:
    """One quality factor's part in the assessment."""

    factor: QualityFactor
    participation: SignalParticipation

    #: The point this factor earned, where it was read at all. `None`
    #: for a factor that did not participate — never zero, which is a
    #: measured failure and a different statement.
    points: int | None = None

    @property
    def read(self) -> bool:
        return self.participation is SignalParticipation.PARTICIPATING

    @property
    def expected(self) -> bool:
        """Whether this factor counts towards the coverage denominator."""

        return self.participation.expected


@dataclass(frozen=True, slots=True)
class QualityCoverage:
    """How much of the applicable factor set Quality actually read.

    The object that decides whether a band may be issued. It computes
    no band itself and holds no threshold: the ruler is unchanged and
    lives where it always did.
    """

    standings: tuple[FactorStanding, ...]

    @property
    def applicable(self) -> tuple[FactorStanding, ...]:
        """Factors that apply to this company, read or not."""

        return tuple(item for item in self.standings if item.expected)

    @property
    def read(self) -> tuple[FactorStanding, ...]:
        return tuple(item for item in self.standings if item.read)

    @property
    def earned(self) -> int:
        return sum(item.points or 0 for item in self.read)

    @property
    def available(self) -> int:
        return len(self.read)

    @property
    def expected(self) -> int:
        return len(self.applicable)

    @property
    def complete(self) -> bool:
        """Whether every applicable factor was read.

        The authority test, and it is deliberately *completeness*
        rather than a ratio floor: #140 measured that every partial
        rule — relative performance, relative plus a coverage floor,
        relative plus a breadth floor — lets deleting a factor move the
        band's direction. Requiring the whole applicable set is the
        only rule under which a deletion has no direction left to move.
        """

        return self.expected > 0 and self.available == self.expected

    @property
    def missing(self) -> tuple[QualityFactor, ...]:
        """Applicable factors that could not be read, named."""

        return tuple(
            item.factor
            for item in self.applicable
            if item.participation is SignalParticipation.EXPECTED_ABSENT
        )

    @property
    def may_band(self) -> bool:
        """Whether the existing ruler may run at all."""

        return self.complete

    @property
    def performance(self) -> str:
        """What was actually measured, sayable even without authority.

        The sentence the platform could not previously form: *passed
        the one factor we could read* is true, and is not a judgement
        of the business.
        """

        return f"{self.earned} of {self.available} readable factors passed"

    @property
    def because(self) -> str:
        """Why Quality withheld a band, worded here once."""

        if self.may_band:
            return ""

        if self.available == 0:
            return (
                "Business quality is not assessed: none of the factors it "
                "is judged on could be read."
            )

        missing = ", ".join(factor.stated for factor in self.missing)

        return (
            "Business quality is not assessed: "
            f"{self.performance}, but {missing} could not be read, and a "
            "band earned over part of the question set would describe the "
            "reading rather than the business."
        )
