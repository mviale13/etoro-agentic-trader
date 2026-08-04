"""What the market did between two recorded observations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt

from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.market_snapshot import MarketQuote, MarketSnapshot


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

    An individual instrument's move is reported too, but only where it is
    large *for that instrument*. Every instrument moves between any two
    readings, so reporting one used to mean deciding which moves matter, and
    the platform once had no measure of that. It does now: each quote carries
    a year of realised volatility, so a day's move can be judged against the
    instrument's own typical daily move rather than against a figure picked
    to look sensible. A quarter-percent day for the dollar and a five-percent
    day for oil are read on the same scale — each in multiples of what that
    instrument usually does — and only the moves past the threshold are named.

    **What is still not reported.** A move on an instrument whose history was
    too short to measure a typical move for: without that figure there is no
    scale to judge the day against, and one guessed would be the invented
    number the archive was built to stop. A VIX that moved without leaving
    its band is not an event either; its move is the volatility band above.

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

    #: Trading days in a year, to turn an annualised volatility back into the
    #: daily standard deviation it was built from.
    TRADING_DAYS = 252

    #: How many of an instrument's own daily standard deviations a move must
    #: cross before it is named. Two is a move in the top few percent of that
    #: instrument's days — notable for it, whatever its usual size. It is this
    #: platform's band, stated here, on a figure that is the instrument's own.
    SIGNIFICANT_MOVE = 2.0

    def changes(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> tuple[ChangeEvent, ...]:
        """Everything that measurably moved between these two observations."""

        classifications = (
            self._mood_change(previous, current),
            self._volatility_change(previous, current),
            self._sentiment_change(previous, current),
        )

        return (
            *(event for event in classifications if event is not None),
            *self._instrument_moves(previous, current),
        )

    def _instrument_moves(
        self,
        previous: MarketSnapshot,
        current: MarketSnapshot,
    ) -> tuple[ChangeEvent, ...]:
        """
        Each instrument whose day was large for it, and newly so.

        Judged in multiples of the instrument's own typical daily move, so
        the scale is the instrument's and only the threshold is this
        platform's. A move already past the threshold in the previous reading
        is not named again — it is the same move, not a new one — which is
        why a still market's feed stays quiet where a turning one does not.
        """

        events: list[ChangeEvent] = []

        for quote in current.quotes:
            multiple = self._move_in_sigmas(quote)

            if multiple is None or multiple < self.SIGNIFICANT_MOVE:
                continue

            already = self._move_in_sigmas(previous.quote(quote.symbol))

            if already is not None and already >= self.SIGNIFICANT_MOVE:
                continue

            events.append(self._instrument_event(quote, multiple, current.timestamp))

        return tuple(events)

    @classmethod
    def _move_in_sigmas(
        cls,
        quote: MarketQuote | None,
    ) -> float | None:
        """
        A day's move as a multiple of the instrument's typical daily one.

        None where the instrument was not read, or its history was too short
        to have a typical move to judge against. The annualised volatility is
        turned back into a daily standard deviation — the figure it was built
        from — and the day's change measured against that.
        """

        if quote is None or quote.realized_volatility is None:
            return None

        daily_sigma = quote.realized_volatility / sqrt(cls.TRADING_DAYS)

        if daily_sigma <= 0:
            return None

        return abs(quote.change_percent / 100.0) / daily_sigma

    def _instrument_event(
        self,
        quote: MarketQuote,
        multiple: float,
        moment: datetime,
    ) -> ChangeEvent:
        verb = "rose" if quote.change_percent >= 0 else "fell"
        typical_daily = (
            (quote.realized_volatility or 0.0) / sqrt(self.TRADING_DAYS) * 100.0
        )

        return ChangeEvent(
            title=f"{quote.symbol} {verb} {abs(quote.change_percent):.1f}%",
            description=(
                f"{quote.name} {verb} {abs(quote.change_percent):.1f}% — "
                f"{multiple:.1f}× its typical daily move of {typical_daily:.1f}%."
            ),
            category=ChangeCategory.MARKET,
            severity=self._move_severity(multiple),
            # The observation's own time, as the mood and volatility events
            # use, so the whole feed sorts on one clock.
            timestamp=moment,
        )

    @staticmethod
    def _move_severity(multiple: float) -> ChangeSeverity:
        """
        How far past its own scale the instrument moved.

        Banded like every other severity here: a measured distance, not an
        opinion about importance. Four of the instrument's own daily standard
        deviations is a rare day for it; three is an unusual one.
        """

        if multiple >= 4.0:
            return ChangeSeverity.HIGH

        if multiple >= 3.0:
            return ChangeSeverity.MEDIUM

        return ChangeSeverity.LOW

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
                f"Volatility moved from {previous.volatility} to {current.volatility}"
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
