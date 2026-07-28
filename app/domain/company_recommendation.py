from dataclasses import dataclass

from app.domain.company_signals import CompanySignals


@dataclass(frozen=True, slots=True)
class CompanyRecommendation:
    symbol: str
    recommendation: str
    confidence: int
    summary: str
    signals: CompanySignals
    evidence: tuple[str, ...]
