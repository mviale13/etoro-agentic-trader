from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.equity_trend_opinion import (
    EquityTrendOpinion,
    EquityTrendVerdict,
)
from app.domain.market_facts import MarketFacts


class EquityTrendAnalyst(Analyst[MarketFacts, EquityTrendOpinion]):
    _SYMBOLS = (
        "SPY",
        "QQQ",
        "IWM",
    )

    @property
    def expected_observation_count(self) -> int:
        return len(self._SYMBOLS)

    def observations(
        self,
        market: MarketFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        for symbol in self._SYMBOLS:
            quote = market.quote(symbol)

            if quote is not None:
                observations.append(
                    AnalystObservation(
                        key=symbol,
                        label=symbol,
                        value=quote.change_percent,
                    )
                )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        return self._change_score(observation.value)

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        return f"{observation.label} changed {observation.value:.1f}%."

    def uncertainty(
        self,
        market: MarketFacts,
    ) -> tuple[str, ...]:
        uncertainty: list[str] = []

        for symbol in self._SYMBOLS:
            if market.quote(symbol) is None:
                uncertainty.append(f"{symbol} daily change data is unavailable.")

        return tuple(uncertainty)

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> EquityTrendOpinion:
        return EquityTrendOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        market: MarketFacts,
    ) -> EquityTrendOpinion:
        return EquityTrendOpinion(
            score=50,
            confidence=0.0,
            verdict=EquityTrendVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(market),
        )

    @staticmethod
    def _change_score(
        value: float,
    ) -> int:
        if value >= 1.0:
            return 100

        if value >= 0.0:
            return 75

        if value >= -1.0:
            return 40

        return 0

    @staticmethod
    def _verdict(
        score: int,
    ) -> EquityTrendVerdict:
        if score >= 85:
            return EquityTrendVerdict.BULLISH

        if score >= 50:
            return EquityTrendVerdict.NEUTRAL

        return EquityTrendVerdict.BEARISH
