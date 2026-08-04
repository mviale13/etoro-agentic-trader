"""What the Artificial CIO changed its mind about."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from app.application.change_feed.market_change_service import (
    MarketChangeService,
)
from app.application.learning.decision_journal import DecisionJournal
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.change_feed.change_feed import ChangeFeed
from app.domain.decision_history import DecisionHistory, DecisionRecord
from app.domain.market_snapshot import MarketSnapshot


class MarketHistory(Protocol):
    """Anything that can hand back the market observations it recorded."""

    def recent(self, limit: int = 2) -> tuple[MarketSnapshot, ...]: ...


@dataclass(slots=True)
class ChangeFeedService:
    """
    Report what changed since the last cycle, newest first.

    A change is a recorded fact. The journal holds one decision state, then
    a different one; the market archive holds one observation, then a
    different one. Nothing here re-decides and nothing here re-fetches, and
    a quiet feed means nothing moved — never that the feed has nothing to
    show.

    Market and macro movements were absent from this feed until the market
    was recorded at all. They are reported now only where an archive is
    supplied: a caller with no market history gets the decisions alone,
    which is what a fresh clone honestly has.
    """

    journal: DecisionJournal

    #: Where the recorded market observations are read from. None means no
    #: market history is available to this caller, not that the market did
    #: not move.
    market: MarketHistory | None = None

    market_changes: MarketChangeService = field(
        default_factory=MarketChangeService,
    )

    def build(
        self,
        symbols: Sequence[str] | None = None,
        limit: int = 10,
    ) -> ChangeFeed:
        """
        Build the feed, optionally narrowed to the symbols the investor holds.

        `symbols` narrows the decisions reported. It does not narrow the
        market, which moved for the whole account rather than for any
        holding in it.

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

        events.extend(self._market_moves())

        events.sort(
            key=lambda event: event.timestamp,
            reverse=True,
        )

        return ChangeFeed(
            events=tuple(events[:limit] if limit > 0 else events),
        )

    def _market_moves(self) -> Iterable[ChangeEvent]:
        """
        What the market did between the last two recorded observations.

        One observation is not a movement, and an archive holding only one
        says so by reporting nothing. It is the honest state of a platform
        on its first cycle, and it is not the same as a flat market.
        """

        if self.market is None:
            return ()

        recorded = self.market.recent(2)

        if len(recorded) < 2:
            return ()

        current, previous = recorded[0], recorded[1]

        return self.market_changes.changes(previous, current)

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
