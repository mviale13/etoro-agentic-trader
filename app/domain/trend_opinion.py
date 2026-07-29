from dataclasses import dataclass

from app.domain.opinion import Opinion
from app.domain.verdict import Verdict


class TrendVerdict(Verdict):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TrendOpinion(Opinion[TrendVerdict]):
    pass
