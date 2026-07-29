from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class FundamentalVerdict(Verdict):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FundamentalOpinion(Opinion[FundamentalVerdict]):
    pass
