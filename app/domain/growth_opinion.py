from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class GrowthVerdict(Verdict):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    DECLINING = "declining"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GrowthOpinion(Opinion[GrowthVerdict]):
    pass
