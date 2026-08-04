from dataclasses import dataclass

from app.domain.company_signals import CompanySignals
from app.domain.finding import Finding
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class CompanyRecommendation:
    symbol: str
    recommendation: str
    confidence: int
    summary: str
    signals: CompanySignals
    evidence: tuple[Finding, ...]

    #: When the facts behind this were read.
    reading: Provenance | None = None
