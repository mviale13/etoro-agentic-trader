"""Market reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
    MarketRegime,
    MarketTrend,
)
from app.domain.brain_context import BrainContext
from app.domain.market_context import MarketContext


class MarketReasoner:
    """Transforms a market context into a structured assessment."""

    def assess(
        self,
        context: BrainContext,
    ) -> MarketAssessment:
        market = context.market

        momentum = self._momentum_score(market)
        volatility = self._volatility_score(market)

        trend = self._trend(momentum)
        regime = self._regime(momentum, volatility)
        confidence = max(0.5, 1.0 - abs(momentum - volatility) * 0.5)

        opportunities: list[str] = []
        risks: list[str] = []

        if momentum >= 0.7:
            opportunities.append("Positive market momentum")
        elif momentum <= 0.3:
            risks.append("Weak market momentum")

        if volatility >= 0.7:
            risks.append("Elevated market volatility")
        elif volatility <= 0.3:
            opportunities.append("Stable market conditions")

        evidence = (
            Evidence(
                description=f"Market regime is '{market.regime}'.",
                source="MarketContext",
                strength=0.9,
            ),
            Evidence(
                description=f"Market sentiment is '{market.sentiment}'.",
                source="MarketContext",
                strength=0.9,
            ),
            Evidence(
                description=market.headline,
                source="MarketContext",
                strength=0.8,
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

    def _momentum_score(
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

    def _volatility_score(
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
        if momentum >= 0.9:
            return MarketTrend.STRONGLY_BULLISH
        if momentum >= 0.7:
            return MarketTrend.BULLISH
        if momentum >= 0.3:
            return MarketTrend.NEUTRAL
        if momentum >= 0.1:
            return MarketTrend.BEARISH
        return MarketTrend.STRONGLY_BEARISH

    def _regime(
        self,
        momentum: float,
        volatility: float,
    ) -> MarketRegime:
        if momentum >= 0.7 and volatility <= 0.5:
            return MarketRegime.RISK_ON

        if momentum <= 0.3 and volatility >= 0.7:
            return MarketRegime.RISK_OFF

        if abs(momentum - volatility) <= 0.2:
            return MarketRegime.TRANSITION

        return MarketRegime.UNCERTAIN
