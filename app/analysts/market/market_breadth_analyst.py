from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.market_breadth_opinion import (
    MarketBreadthOpinion,
    MarketBreadthVerdict,
)
from app.domain.market_facts import MarketFacts


class MarketBreadthAnalyst(
    Analyst[
        MarketFacts,
        MarketBreadthOpinion,
    ]
):
    _SYMBOLS = (
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
    )

    @property
    def expected_observation_count(self) -> int:
        return len(self._SYMBOLS)

    def observations(
        self,
        facts: MarketFacts,
    ) -> tuple[AnalystObservation, ...]:
        observations: list[AnalystObservation] = []

        for symbol in self._SYMBOLS:
            quote = facts.quote(symbol)

            if quote is None:
                continue

            observations.append(
                AnalystObservation(
                    key=symbol.lower(),
                    label=symbol,
                    value=quote.change_percent,
                )
            )

        return tuple(observations)

    def score_observation(
        self,
        observation: AnalystObservation,
    ) -> int:
        if observation.value > 0:
            return 100

        return 0

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        direction = "advanced" if observation.value > 0 else "declined"

        return f"{observation.label} {direction} {abs(observation.value):.1f}%."

    def uncertainty(
        self,
        facts: MarketFacts,
    ) -> tuple[str, ...]:
        return tuple(
            f"{symbol} daily change data is unavailable."
            for symbol in self._SYMBOLS
            if facts.quote(symbol) is None
        )

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> MarketBreadthOpinion:
        return MarketBreadthOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        facts: MarketFacts,
    ) -> MarketBreadthOpinion:
        return MarketBreadthOpinion(
            score=50,
            confidence=0.0,
            verdict=MarketBreadthVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(facts),
        )

    @staticmethod
    def _verdict(
        score: int,
    ) -> MarketBreadthVerdict:
        if score >= 75:
            return MarketBreadthVerdict.STRONG

        if score >= 25:
            return MarketBreadthVerdict.MIXED

        return MarketBreadthVerdict.WEAK
