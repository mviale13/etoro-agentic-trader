from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class ProfitabilityVerdict(Verdict):
    EXCELLENT = "excellent"
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProfitabilityOpinion(Opinion[ProfitabilityVerdict]):
    pass
