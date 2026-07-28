from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class BalanceSheetVerdict(StrEnum):
    EXCELLENT = "EXCELLENT"
    STRONG = "STRONG"
    ADEQUATE = "ADEQUATE"
    WEAK = "WEAK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class BalanceSheetOpinion(Opinion):
    verdict: BalanceSheetVerdict
