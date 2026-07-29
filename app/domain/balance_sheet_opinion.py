from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class BalanceSheetVerdict(Verdict):
    EXCELLENT = "excellent"
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BalanceSheetOpinion(Opinion[BalanceSheetVerdict]):
    pass
