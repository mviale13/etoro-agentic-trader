from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.finding import Dimension


class CompanyCommitteeService:
    VALUE_WEIGHT = 0.40
    QUALITY_WEIGHT = 0.35
    MOMENTUM_WEIGHT = 0.25

    BUY_THRESHOLD = 0.50
    SELL_THRESHOLD = -0.50

    def evaluate(
        self,
        symbol: str,
        signals: CompanySignals,
    ) -> CompanyRecommendation:
        score = (
            self.VALUE_WEIGHT * self._value_score(signals)
            + self.QUALITY_WEIGHT * self._quality_score(signals)
            + self.MOMENTUM_WEIGHT * self._momentum_score(signals)
        )

        recommendation = self._recommendation(score)
        confidence = round(50 + abs(score) * 50)

        # Attributed here because here is where the producing signal is
        # known by name. A later layer reading this flat list cannot tell
        # a valuation finding from a quality one except by its wording,
        # and a committee whose remit was matched on wording would be
        # guessing at exactly the thing this composition already knows.
        evidence = (
            *(item.about(Dimension.VALUATION) for item in signals.value.evidence),
            *(item.about(Dimension.QUALITY) for item in signals.quality.evidence),
            *(item.about(Dimension.MOMENTUM) for item in signals.momentum.evidence),
        )

        return CompanyRecommendation(
            symbol=symbol.upper().strip(),
            recommendation=recommendation,
            confidence=confidence,
            summary=self._summary(
                recommendation,
                signals,
            ),
            signals=signals,
            evidence=evidence,
            reading=signals.reading,
        )

    @staticmethod
    def _value_score(
        signals: CompanySignals,
    ) -> int:
        return {
            "CHEAP": 1,
            "FAIR": 0,
            "EXPENSIVE": -1,
            "UNKNOWN": 0,
        }.get(signals.value.valuation, 0)

    @staticmethod
    def _quality_score(
        signals: CompanySignals,
    ) -> int:
        return {
            "HIGH": 1,
            "MEDIUM": 0,
            "LOW": -1,
            "UNKNOWN": 0,
        }.get(signals.quality.quality, 0)

    @staticmethod
    def _momentum_score(
        signals: CompanySignals,
    ) -> int:
        return {
            "BULLISH": 1,
            "NEUTRAL": 0,
            "BEARISH": -1,
            "UNKNOWN": 0,
        }.get(signals.momentum.trend, 0)

    def _recommendation(
        self,
        score: float,
    ) -> str:
        if score >= self.BUY_THRESHOLD:
            return "BUY"

        if score <= self.SELL_THRESHOLD:
            return "SELL"

        return "HOLD"

    @staticmethod
    def _summary(
        recommendation: str,
        signals: CompanySignals,
    ) -> str:
        return (
            f"{recommendation}: "
            f"value is {signals.value.valuation.lower()}, "
            f"quality is {signals.quality.quality.lower()}, "
            f"and momentum is {signals.momentum.trend.lower()}."
        )
