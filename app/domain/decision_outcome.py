"""What the security did after the Artificial CIO decided about it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.cio.decision_state import DecisionState
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    """
    One recorded decision, and the price move since it was made.

    This is a measurement of an observed window, not a verdict on the
    thesis. The investor's horizon is years; a month of price action is
    the beginning of the story, and calling it "the outcome" would let
    noise read as a track record.

    What it can honestly say is whether the security has so far moved the
    way the decision implied — for the decisions that implied anything.
    """

    symbol: str
    state: DecisionState

    #: The conviction the decision was taken at, where it carried one.
    #: A record whose conviction was withheld is still an outcome — the
    #: state was decided and the price did what it did — so the window is
    #: measured and the number is simply absent.
    conviction: int | None
    decided_at: datetime

    #: The close the decision is measured from, and the day it is the
    #: close of. Not necessarily the decision date: markets shut, and the
    #: last close before a Sunday decision is Friday's.
    priced_on: date
    price_at_decision: float

    price_now: float
    days_elapsed: int

    #: Who priced this, and when the current price was read.
    reading: Provenance

    #: A move smaller than this is not a direction, over any window this
    #: measures. Policy, stated here because a security that has barely
    #: moved is evidence for nobody: without a floor, a stock sitting
    #: exactly where it was counted as proof the call was wrong, which is
    #: how a flat month becomes a black mark.
    FLAT_MOVE = 0.005

    @property
    def change(self) -> float:
        """The move since the decision, as a ratio."""

        return (self.price_now - self.price_at_decision) / self.price_at_decision

    @property
    def moved_as_the_decision_implied(self) -> bool | None:
        """
        Whether the move so far agrees with what the decision said to do.

        None where the decision said to do nothing. MONITOR and
        INVESTIGATE are not calls — they are the platform saying it does
        not know yet — and scoring them against a price move would build
        a track record out of decisions that never claimed anything.

        None too where the security has barely moved. A holding that sits
        where it was neither confirms nor refutes the call, and the first
        live run priced one at exactly its decision price and marked it
        against the decision.

        REJECT is a call: it says this is not worth owning, and a fall
        agrees with it. Counting a rise after a REJECT as a loss would be
        the opposite error, so this reports agreement, not profit.
        """

        if abs(self.change) < self.FLAT_MOVE:
            return None

        if self.state is DecisionState.REJECT:
            return self.change < 0

        if self.state.asks_for_action:
            return self.change > 0

        return None


@dataclass(frozen=True, slots=True)
class UnscoredDecision:
    """A recorded decision that could not be measured, and why not."""

    symbol: str
    state: DecisionState
    decided_at: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class TrackRecord:
    """
    Every recorded decision old enough to measure, and everything not.

    The unscored are carried rather than dropped. A track record built
    only from the decisions that happened to be measurable would describe
    a different platform from the one that made them.
    """

    outcomes: tuple[DecisionOutcome, ...]
    unscored: tuple[UnscoredDecision, ...]

    #: Calls needed before a hit rate is reported at all. Below this the
    #: figure moves several points per decision, which reads as a skill
    #: measurement and is arithmetic on a handful of days.
    MINIMUM_CALLS = 10

    @property
    def calls(self) -> tuple[DecisionOutcome, ...]:
        """The outcomes whose decision actually implied something."""

        return tuple(
            outcome
            for outcome in self.outcomes
            if outcome.moved_as_the_decision_implied is not None
        )

    @property
    def agreed(self) -> int:
        """Calls the market has so far agreed with."""

        return sum(1 for outcome in self.calls if outcome.moved_as_the_decision_implied)

    @property
    def hit_rate(self) -> float | None:
        """
        The share of calls the market has agreed with, or nothing.

        Nothing below `MINIMUM_CALLS`, because a rate over three
        decisions is not a rate.
        """

        if len(self.calls) < self.MINIMUM_CALLS:
            return None

        return self.agreed / len(self.calls)
