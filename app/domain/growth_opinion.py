from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class GrowthVerdict(StrEnum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    DECLINING = "DECLINING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class GrowthOpinion(Opinion):
    verdict: GrowthVerdict
