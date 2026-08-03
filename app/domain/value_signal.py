from dataclasses import dataclass

from app.domain.finding import Finding


@dataclass(frozen=True, slots=True)
class ValueSignal:
    valuation: str

    confidence: int

    evidence: tuple[Finding, ...]
