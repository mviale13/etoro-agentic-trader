from dataclasses import dataclass
from datetime import datetime

HOLD_TOLERANCE_PCT = 2.0


@dataclass(frozen=True, slots=True)
class CommitteeOutcome:
    recommendation_timestamp: datetime
    evaluation_timestamp: datetime
    symbol: str
    recommendation: str
    entry_price: float
    evaluation_price: float
    return_pct: float
    successful: bool


def is_recommendation_successful(
    recommendation: str,
    return_pct: float,
) -> bool:
    normalized = recommendation.upper().strip()

    if normalized == "BUY":
        return return_pct > 0

    if normalized == "SELL":
        return return_pct < 0

    if normalized == "HOLD":
        return abs(return_pct) <= HOLD_TOLERANCE_PCT

    raise ValueError(f"Unsupported recommendation: {recommendation}")
