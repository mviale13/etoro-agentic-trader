from app.domain.company_facts import CompanyFacts
from app.domain.quality_signal import QualitySignal


class QualitySignalService:
    LARGE_CAP_THRESHOLD = 10_000_000_000

    def build(
        self,
        company: CompanyFacts,
    ) -> QualitySignal:
        evidence: list[str] = []
        score = 0

        if company.market_cap is not None:
            if company.market_cap >= self.LARGE_CAP_THRESHOLD:
                score += 1
                evidence.append("Large-cap company.")
            else:
                evidence.append("Small or mid-cap company.")

        if company.eps is not None:
            if company.eps > 0:
                score += 1
                evidence.append("Positive earnings.")
            else:
                evidence.append("Negative earnings.")

        if company.dividend_yield is not None:
            if company.dividend_yield > 0:
                score += 1
                evidence.append("Dividend-paying business.")
            else:
                evidence.append("No dividend.")

        if not evidence:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                evidence=("Insufficient quality data.",),
            )

        if score >= 3:
            return QualitySignal(
                quality="HIGH",
                confidence=90,
                evidence=tuple(evidence),
            )

        if score >= 2:
            return QualitySignal(
                quality="MEDIUM",
                confidence=75,
                evidence=tuple(evidence),
            )

        return QualitySignal(
            quality="LOW",
            confidence=65,
            evidence=tuple(evidence),
        )
