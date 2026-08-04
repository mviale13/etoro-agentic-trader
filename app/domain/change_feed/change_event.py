from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ChangeCategory(StrEnum):
    DECISION = "decision"
    PORTFOLIO = "portfolio"
    WATCHLIST = "watchlist"
    MARKET = "market"
    MACRO = "macro"


class ChangeSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ChangeEvent:
    """
    Represents something meaningful that changed
    since the investor's previous visit.
    """

    title: str

    description: str

    category: ChangeCategory

    severity: ChangeSeverity

    timestamp: datetime

    action_required: bool = False
