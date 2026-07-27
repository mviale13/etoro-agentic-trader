from dataclasses import dataclass
from enum import StrEnum


class MarketRegimeType(StrEnum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"


@dataclass(frozen=True, slots=True)
class MarketRegime:
    regime: MarketRegimeType
    confidence: int
    summary: str
