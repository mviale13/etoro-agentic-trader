from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class ProfitabilityVerdict(StrEnum):
    EXCELLENT = "EXCELLENT"
    STRONG = "STRONG"
    AVERAGE = "AVERAGE"
    WEAK = "WEAK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ProfitabilityOpinion(Opinion):
    verdict: ProfitabilityVerdict
