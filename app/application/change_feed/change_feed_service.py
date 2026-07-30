from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.change_feed.change_feed import ChangeFeed


@dataclass(slots=True)
class ChangeFeedService:
    """
    Generates the Executive Changes Feed.

    Eventually this compares:
        previous ExecutiveWorkspace
        current ExecutiveWorkspace
    """

    def build(self) -> ChangeFeed:

        now = datetime.utcnow()

        return ChangeFeed(
            events=(
                ChangeEvent(
                    title="NVIDIA upgraded",
                    description="Recommendation changed from WATCH to BUY.",
                    category=ChangeCategory.WATCHLIST,
                    severity=ChangeSeverity.HIGH,
                    timestamp=now,
                ),
                ChangeEvent(
                    title="Portfolio risk increased",
                    description="Overall portfolio risk increased by 3%.",
                    category=ChangeCategory.PORTFOLIO,
                    severity=ChangeSeverity.MEDIUM,
                    timestamp=now,
                ),
                ChangeEvent(
                    title="Fed expectations improved",
                    description="Interest-rate expectations became more supportive.",
                    category=ChangeCategory.MACRO,
                    severity=ChangeSeverity.LOW,
                    timestamp=now,
                ),
            )
        )
