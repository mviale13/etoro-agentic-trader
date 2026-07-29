from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class FundamentalVerdict(StrEnum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FundamentalOpinion(Opinion):
    verdict: FundamentalVerdict
