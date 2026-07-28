from dataclasses import dataclass
from enum import StrEnum


class GrowthVerdict(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    DECLINING = "DECLINING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class GrowthOpinion:
    score: int | None
    confidence: float
    verdict: GrowthVerdict
    evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]
