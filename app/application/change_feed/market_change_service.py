"""What the market did between two recorded observations."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class MarketChangeService:
    """
    Compare two recorded market observations and report what moved.

    Nothing here fetches, and nothing here decides. Both snapshots were
    read from the archive, and a change is the difference between two
    figures that were actually observed.

    **What is reported.** A classification that moved: the market mood, the
    volatility band, and the sentiment reading's own label. Each event
    states the figures behind it where they were read, because "volatility
    rose" without the VIX is an adjective, and the branch has already spent
    a commit on adjectives that could not be compared with yesterday's.

    **What is not reported, and why.** An individual instrument moving is
    not an event here. Every instrument moves between any two readings, so
    reporting one means deciding which moves matter, and this platform has
    no measure of that — a threshold picked to look sensible would be an
    invented figure sitting on an investment surface, which is the thing
    the archive was built to stop. The same holds for a VIX that moved
    without leaving its band. The quotes and the figures are recorded, so
    the measure can be built later on evidence rather than on a guess.

    A snapshot's classification is derived from its own figures on the way
    out of the archive, so both sides of a comparison are classified by the
    same rules — never one under today's thresholds and one under whatever
    was in force when it was filed.
    """

    #: The mood ladder, as `MarketService` classifies it. Ordered so the
    #: distance between two moods can be measured rather than judged.
    MOOD_LADDER = ("negative", "neutral", "positive")

    #: The volatility ladder, as `MarketService` bands the VIX.
    VOLATILITY_LADDER = ("low", "medium", "high")

    def changes(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> tuple[ChangeEvent, ...]:
        """Everything that measurably moved between these two observations."""

        events = (
            self._mood_change(previous, current),
            self._volatility_change(previous, current),
            self._sentiment_change(previous, current),
        )

        return tuple(event for event in events if event is not None)

    def _mood_change(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> ChangeEvent | None:
        if previous.market_mood == current.market_mood:
            return None

        return ChangeEvent(
            title=(
                f"Market mood moved from {previous.market_mood} "
                f"to {current.market_mood}"
            ),
            # The snapshot's own summary of itself, not a fresh reading of
            # what the move meant. This service does not interpret.
            description=current.summary,
            category=ChangeCategory.MARKET,
            severity=self._rungs_apart(
                self.MOOD_LADDER,
                previous.market_mood,
                current.market_mood,
            ),
            timestamp=current.timestamp,
        )

    def _volatility_change(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> ChangeEvent | None:
        if previous.volatility == current.volatility:
            return None

        # "unknown" is the band of a VIX that was never read. Moving into
        # or out of it is a change in what the platform could see, not a
        # change in the market, and reporting it as one would tell the
        # investor volatility fell when the reading simply arrived.
        if "unknown" in (previous.volatility, current.volatility):
            return None

        return ChangeEvent(
            title=(
                f"Volatility moved from {previous.volatility} "
                f"to {current.volatility}"
            ),
            description=self._vix_figures(previous, current),
            # The VIX is a reading of the market's own expectations rather
            # than of any security in it.
            category=ChangeCategory.MACRO,
            severity=self._rungs_apart(
                self.VOLATILITY_LADDER,
                previous.volatility,
                current.volatility,
            ),
            timestamp=current.timestamp,
        )

    def _sentiment_change(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> ChangeEvent | None:
        before = previous.sentiment
        after = current.sentiment

        # An index that could not be read on one of the two days leaves
        # nothing to compare. That absence is reported where the reading
        # itself is reported; it is not a movement in sentiment.
        if before is None or after is None:
            return None

        # Two readings of different asset classes are not a change in
        # either. This is the whole reason a reading carries its subject.
        if before.subject is not after.subject:
            return None

        if before.label == after.label:
            return None

        subject = after.subject.value.capitalize()

        return ChangeEvent(
            title=(f"{subject} sentiment moved from {before.label} to {after.label}"),
            description=(
                f"{after.reading.source} read {before.score}, and now reads "
                f"{after.score}, on an index running 0 to 100."
            ),
            category=ChangeCategory.MARKET,
            severity=self._index_move(before.score, after.score),
            timestamp=current.timestamp,
        )

    def _vix_figures(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> str:
        """
        The figures the bands were decided by, where both were read.

        A band change with only one figure behind it states the one it has.
        Neither figure is estimated from the band it produced: "medium"
        covers 15 to 25, and picking a number out of that range would be
        reporting a measurement nobody took.
        """

        before = previous.vix
        after = current.vix

        if before is not None and after is not None:
            return f"The VIX read {before:.2f}, and now reads {after:.2f}."

        if after is not None:
            return f"The VIX reads {after:.2f}."

        if before is not None:
            return f"The VIX read {before:.2f}. It could not be read this time."

        return "The VIX was not read on either observation."

    @staticmethod
    def _rungs_apart(
        ladder: tuple[str, ...],
        previous: str,
        current: str,
    ) -> ChangeSeverity:
        """
        How far a classification moved along its own ladder.

        Banded exactly as the decision feed bands a lifecycle move: a
        measured distance, not an opinion about importance. A value that is
        not on the ladder cannot be measured against one, and is reported
        at the lowest severity rather than at a guessed one.
        """

        if previous not in ladder or current not in ladder:
            return ChangeSeverity.LOW

        distance = abs(ladder.index(current) - ladder.index(previous))

        if distance >= 3:
            return ChangeSeverity.HIGH

        if distance == 2:
            return ChangeSeverity.MEDIUM

        return ChangeSeverity.LOW

    @staticmethod
    def _index_move(
        previous: int,
        current: int,
    ) -> ChangeSeverity:
        """
        How far the sentiment index moved, as a share of its own range.

        The index runs 0 to 100 and its labels are the publisher's, not
        this platform's, so the labels cannot be counted as rungs the way
        a mood can. The distance that can be measured is the score, and it
        is banded by thirds of the published range: over a third HIGH, over
        a sixth MEDIUM. The bands are this platform's and are stated as
        such; the figures they band are the publisher's.
        """

        distance = abs(current - previous)

        if distance > 33:
            return ChangeSeverity.HIGH

        if distance > 16:
            return ChangeSeverity.MEDIUM

        return ChangeSeverity.LOW
