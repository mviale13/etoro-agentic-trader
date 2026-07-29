from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class EquityTrendVerdict(Verdict):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EquityTrendOpinion(Opinion[EquityTrendVerdict]):
    pass
