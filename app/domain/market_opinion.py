from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketOpinion:
    """Final opinion produced by the Market Committee."""

    score: int
    confidence: float
    verdict: str
    rationale: tuple[str, ...]
