from app.analysts.analyst import Analyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.market_facts import MarketFacts
from app.domain.trend_opinion import TrendOpinion, TrendVerdict


class TrendAnalyst(Analyst[MarketFacts, TrendOpinion]):
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
        value = observation.value

        if value >= 1.0:
            return 100

        if value >= 0.0:
            return 75

        if value >= -1.0:
            return 40

        return 0

    @staticmethod
    def format_evidence(
        observation: AnalystObservation,
    ) -> str:
        return f"{observation.label} changed {observation.value:.1f}%."

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
    ) -> TrendOpinion:
        return TrendOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(
        self,
        facts: MarketFacts,
    ) -> TrendOpinion:
        return TrendOpinion(
            score=None,
            confidence=0.0,
            verdict=TrendVerdict.UNKNOWN,
            evidence=(),
            uncertainty=self.uncertainty(facts),
        )

    @staticmethod
    def _verdict(
        score: int,
    ) -> TrendVerdict:
        if score >= 85:
            return TrendVerdict.BULLISH

        if score >= 50:
            return TrendVerdict.NEUTRAL

        return TrendVerdict.BEARISH
