from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Opinion:
    score: int | None
    confidence: float
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]
