from dataclasses import dataclass


@dataclass(frozen=True)
class WatchlistResult:
    symbol: str
    recommendation: str
    confidence: int
