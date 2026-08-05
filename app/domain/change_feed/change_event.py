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

    #: The security this change is about, where it is about one.
    #:
    #: The symbol was known when the change was described and then lived
    #: only inside the title, so nothing downstream could tell three
    #: changes to one holding from three holdings changing. None for a
    #: change about the market rather than about a security.
    symbol: str | None = None
