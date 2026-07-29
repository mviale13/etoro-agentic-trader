"""Market reasoning engine."""

from __future__ import annotations

from statistics import fmean

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
    MarketRegime,
    MarketTrend,
)
from app.brain import Brain
from app.domain.brain_context import BrainContext
from app.domain.market_context import MarketContext
from app.domain.market_snapshot import MarketSnapshot


class MarketReasoner:
    """
    Transform market knowledge into a structured assessment.

    The current Brain exposes a MarketSnapshot. Legacy BrainContext callers
    may still expose MarketContext, so both representations are supported
    during the architecture migration.
    """

    def assess(
        self,
        source: Brain | BrainContext,
    ) -> MarketAssessment:
        market = source.market

        if isinstance(market, MarketSnapshot):
            return self._assess_snapshot(market)

        return self._assess_context(market)

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

        confidence = self._snapshot_confidence(
            quote_count=len(changes),
            momentum=momentum,
            volatility=volatility,
        )

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

        evidence = (
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

    def _assess_context(
        self,
        market: MarketContext,
    ) -> MarketAssessment:
        momentum = self._context_momentum_score(market)
        volatility = self._context_volatility_score(market)

        trend = self._trend(momentum)
        regime = self._regime(momentum, volatility)
        confidence = max(
            0.50,
            1.0 - abs(momentum - volatility) * 0.50,
        )

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

        evidence = (
            Evidence(
                description=f"Market regime is '{market.regime}'.",
                source="MarketContext",
                strength=0.90,
            ),
            Evidence(
                description=f"Market sentiment is '{market.sentiment}'.",
                source="MarketContext",
                strength=0.90,
            ),
            Evidence(
                description=market.headline,
                source="MarketContext",
                strength=0.80,
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
        *,
        quote_count: int,
        momentum: float,
        volatility: float,
    ) -> float:
        sample_confidence = min(quote_count / 10.0, 1.0)

        consistency = 1.0 - abs(abs(momentum - 0.5) * 2.0 - volatility)

        confidence = sample_confidence * 0.60 + max(0.0, consistency) * 0.40

        return max(0.50, min(confidence, 1.0))

    def _context_momentum_score(
        self,
        market: MarketContext,
    ) -> float:
        sentiment = market.sentiment.lower()

        mapping = {
            "very bullish": 1.0,
            "bullish": 0.8,
            "positive": 0.7,
            "neutral": 0.5,
            "negative": 0.3,
            "bearish": 0.2,
            "very bearish": 0.0,
        }

        return mapping.get(sentiment, 0.5)

    def _context_volatility_score(
        self,
        market: MarketContext,
    ) -> float:
        mapping = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "extreme": 1.0,
        }

        return mapping.get(market.volatility.lower(), 0.5)

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
