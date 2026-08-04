from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    recommendation: str
    confidence: int
    reasons: tuple[str, ...]
