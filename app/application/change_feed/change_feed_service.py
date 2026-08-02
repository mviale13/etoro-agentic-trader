"""What the Artificial CIO changed its mind about."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.application.learning.decision_journal import DecisionJournal
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.change_feed.change_feed import ChangeFeed
from app.domain.decision_history import DecisionHistory, DecisionRecord


@dataclass(slots=True)
class ChangeFeedService:
    """
    Report every decision the Artificial CIO changed, newest first.

    A change is a recorded fact: the journal holds one state, then a
    different one. Nothing here re-decides, and a quiet feed means the CIO
    has not changed its mind — never that the feed has nothing to show.

    Market and macro movements are not recorded anywhere yet, so they are
    absent from this feed rather than illustrated.
    """

    journal: DecisionJournal

    def build(
        self,
        symbols: Sequence[str] | None = None,
        limit: int = 10,
    ) -> ChangeFeed:
        """
        Build the feed, optionally narrowed to the symbols the investor holds.

        `limit` caps how many changes are reported, newest first.
        """

        wanted = (
            {symbol.upper().strip() for symbol in symbols}
            if symbols is not None
            else None
        )

        events: list[ChangeEvent] = []

        for symbol, history in self.journal.histories().items():
            if wanted is not None and symbol not in wanted:
                continue

            events.extend(self._changes_in(history))

        events.sort(
            key=lambda event: event.timestamp,
            reverse=True,
        )

        return ChangeFeed(
            events=tuple(events[:limit] if limit > 0 else events),
        )

    def _changes_in(
        self,
        history: DecisionHistory,
    ) -> Iterable[ChangeEvent]:
        records = history.records

        for previous, current in zip(records, records[1:], strict=False):
            if previous.state is current.state:
                continue

            yield self._change(history.symbol, previous, current)

    @staticmethod
    def _change(
        symbol: str,
        previous: DecisionRecord,
        current: DecisionRecord,
    ) -> ChangeEvent:
        """
        Describe one recorded change.

        Severity is how far the decision moved along the investment-case
        lifecycle — a measured distance, not an opinion about importance.
        """

        distance = abs(
            current.state.lifecycle_rank - previous.state.lifecycle_rank,
        )

        if distance >= 3:
            severity = ChangeSeverity.HIGH
        elif distance == 2:
            severity = ChangeSeverity.MEDIUM
        else:
            severity = ChangeSeverity.LOW

        return ChangeEvent(
            title=(
                f"{symbol} moved from {previous.state.value} to {current.state.value}"
            ),
            # The rationale the CIO recorded at the time, not a new one.
            description=current.rationale,
            category=ChangeCategory.DECISION,
            severity=severity,
            timestamp=current.decided_at,
            action_required=current.state.asks_for_action,
        )
