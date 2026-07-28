from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualitySignal:
    quality: str
    confidence: int
    evidence: tuple[str, ...]
