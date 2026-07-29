from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class CashFlowVerdict(StrEnum):
    EXCELLENT = "excellent"
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CashFlowOpinion(Opinion):
    verdict: CashFlowVerdict
