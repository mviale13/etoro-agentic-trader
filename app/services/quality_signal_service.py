from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.quality_signal import QualitySignal


class QualitySignalService:
    LARGE_CAP_THRESHOLD = 10_000_000_000

    def build(
        self,
        company: CompanyFacts,
    ) -> QualitySignal:
        evidence: list[Finding] = []
        score = 0

        # Each finding carries the sense this service scored it with, so
        # nothing downstream has to guess. Size and dividend are scored as
        # a point or no point, never as a penalty — a small company is not
        # thereby a bad one — so the absence of the point is neutral.
        if company.market_cap is not None:
            if company.market_cap >= self.LARGE_CAP_THRESHOLD:
                score += 1
                evidence.append(Finding.favourable("Large-cap company."))
            else:
                evidence.append(Finding.neutral("Small or mid-cap company."))

        if company.eps is not None:
            if company.eps > 0:
                score += 1
                evidence.append(Finding.favourable("Positive earnings."))
            else:
                evidence.append(Finding.adverse("Negative earnings."))

        if company.dividend_yield is not None:
            if company.dividend_yield > 0:
                score += 1
                evidence.append(Finding.favourable("Dividend-paying business."))
            else:
                evidence.append(Finding.neutral("No dividend."))

        if not evidence:
            return QualitySignal(
                quality="UNKNOWN",
                confidence=20,
                evidence=(Finding.neutral("Insufficient quality data."),),
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
