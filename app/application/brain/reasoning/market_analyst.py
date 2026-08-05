"""Market analysis engine."""

from __future__ import annotations

from statistics import fmean

from app.application.brain.analysts import Analyst
from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
    MarketRegime,
    MarketTrend,
)
from app.brain import Brain
from app.domain.market_snapshot import MarketQuote, MarketSnapshot


class MarketAnalyst(Analyst[MarketAssessment]):
    """Transform the Brain's market snapshot into a structured assessment."""

    #: The market panel a full reading prices; see
    #: `YahooMarketProvider.DEFAULT_INSTRUMENTS`. Confidence is measured
    #: against it, so a reading assembled from three instruments that
    #: answered is not trusted like one built on the whole panel. Kept in
    #: step with that panel by hand — a reading is only ever as broad as
    #: what MarketPerception actually prices.
    EXPECTED_INSTRUMENTS = 9

    def assess(
        self,
        source: Brain,
    ) -> MarketAssessment:
        return self._assess_snapshot(source.market)

    def _assess_snapshot(
        self,
        market: MarketSnapshot,
    ) -> MarketAssessment:
        changes = tuple(quote.change_percent for quote in market.quotes)

        average_change = fmean(changes) if changes else 0.0
        average_absolute_change = (
            fmean(abs(change) for change in changes) if changes else 0.0
        )

        momentum = self._snapshot_momentum_score(average_change)
        volatility = self._snapshot_volatility_score(average_absolute_change)

        trend = self._trend(momentum)
        regime = self._regime(momentum, volatility)

        confidence = self._snapshot_confidence(market.quotes)

        opportunities: list[str] = []
        risks: list[str] = []

        if momentum >= 0.70:
            opportunities.append("Positive market momentum")
        elif momentum <= 0.30:
            risks.append("Weak market momentum")

        if volatility >= 0.70:
            risks.append("Elevated market volatility")
        elif volatility <= 0.30:
            opportunities.append("Stable market conditions")

        evidence: tuple[Evidence, ...] = (
            Evidence(
                description=(
                    f"Average market move is {average_change:+.2f}% "
                    f"across {len(changes)} quoted instruments."
                ),
                source="MarketSnapshot",
                strength=0.90,
            ),
            Evidence(
                description=(
                    f"Average absolute market move is {average_absolute_change:.2f}%."
                ),
                source="MarketSnapshot",
                strength=0.85,
            ),
            Evidence(
                description=(
                    f"Market snapshot contains {len(market.quotes)} quoted instruments."
                ),
                source="MarketSnapshot",
                strength=0.80,
            ),
        )

        # Reported, never folded into momentum or volatility. It describes
        # one asset class, and the scores above describe nine instruments;
        # mixing them would let a crypto mood move an equity reading.
        sentiment = market.sentiment

        if sentiment is not None:
            evidence = (
                *evidence,
                Evidence(
                    description=(
                        f"{sentiment.stated}, which describes "
                        f"{sentiment.subject.value} only."
                    ),
                    source=sentiment.reading.stated(),
                    strength=0.70,
                    # Named, not merely said in the sentence. The market
                    # assessment is shared by every security in the cycle,
                    # and a per-security case can only leave this out if it
                    # can tell which class the fact is about.
                    subject=sentiment.subject,
                ),
            )

        return MarketAssessment(
            trend=trend,
            regime=regime,
            volatility_score=volatility,
            momentum_score=momentum,
            confidence=confidence,
            opportunities=tuple(opportunities),
            risks=tuple(risks),
            evidence=evidence,
        )

    def _snapshot_momentum_score(
        self,
        average_change: float,
    ) -> float:
        """
        Convert average percentage change into a normalized momentum score.

        -5% or lower maps to 0.0.
        0% maps to 0.5.
        +5% or higher maps to 1.0.
        """

        return max(
            0.0,
            min(0.5 + average_change / 10.0, 1.0),
        )

    def _snapshot_volatility_score(
        self,
        average_absolute_change: float,
    ) -> float:
        """
        Convert average absolute percentage movement into volatility.

        0% maps to 0.0.
        5% or higher maps to 1.0.
        """

        return max(
            0.0,
            min(average_absolute_change / 5.0, 1.0),
        )

    def _snapshot_confidence(
        self,
        quotes: tuple[MarketQuote, ...],
    ) -> float:
        """
        How well evidenced the market reading is — not which way it moved.

        A confidence restored to meaning what its name says. It used to move
        with how *uniformly* the instruments happened to move on the day:
        `1 − ||momentum − 0.5| × 2 − volatility|` is exactly 1 whenever they
        all move together, so a flat market and one down 8% across the board
        both read 0.94 — and that number is one third of a cognitive average
        that gates real decisions. Direction is the market's, and it belongs
        in the trend and the regime; how much to trust the reading is this,
        and it must not rise or fall with where the market went.

        Two things make a reading well evidenced: how much of the panel
        actually priced, and how much of what priced carries the year-long
        volatility measurement rather than only the day's change. A reading
        is at its strongest when the whole panel came back with its history,
        and it falls where instruments went missing or arrived as a bare
        price — which is the honest reason to trust one reading less than
        another, unlike the dispersion it replaces.
        """

        if not quotes:
            return 0.0

        priced = len(quotes)
        measured = sum(1 for quote in quotes if quote.realized_volatility is not None)

        breadth = min(priced / self.EXPECTED_INSTRUMENTS, 1.0)
        depth = measured / priced

        return round(breadth * 0.5 + depth * 0.5, 4)

    def _trend(
        self,
        momentum: float,
    ) -> MarketTrend:
        if momentum >= 0.90:
            return MarketTrend.STRONGLY_BULLISH

        if momentum >= 0.70:
            return MarketTrend.BULLISH

        if momentum >= 0.30:
            return MarketTrend.NEUTRAL

        if momentum >= 0.10:
            return MarketTrend.BEARISH

        return MarketTrend.STRONGLY_BEARISH

    def _regime(
        self,
        momentum: float,
        volatility: float,
    ) -> MarketRegime:
        if momentum >= 0.70 and volatility <= 0.50:
            return MarketRegime.RISK_ON

        if momentum <= 0.30 and volatility >= 0.70:
            return MarketRegime.RISK_OFF

        if abs(momentum - volatility) <= 0.20:
            return MarketRegime.TRANSITION

        return MarketRegime.UNCERTAIN
