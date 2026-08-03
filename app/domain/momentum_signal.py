from dataclasses import dataclass

from app.domain.finding import Finding


@dataclass(frozen=True, slots=True)
class MomentumSignal:
    trend: str
    strength: str
    confidence: int
    evidence: tuple[Finding, ...]
