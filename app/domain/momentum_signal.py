from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MomentumSignal:
    trend: str
    strength: str
    confidence: int
    evidence: tuple[str, ...]
