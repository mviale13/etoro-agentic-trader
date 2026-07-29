from dataclasses import dataclass
from enum import StrEnum

from app.domain.opinion import Opinion


class EquityTrendVerdict(StrEnum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EquityTrendOpinion(Opinion):
    verdict: EquityTrendVerdict
