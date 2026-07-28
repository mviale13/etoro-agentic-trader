from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValueSignal:
    valuation: str

    confidence: int

    evidence: tuple[str, ...]
