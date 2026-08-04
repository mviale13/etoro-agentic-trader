"""Scoring what the Artificial CIO decided against what happened next."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from app.application.learning.decision_journal import DecisionJournal
from app.domain.decision_outcome import (
    DecisionOutcome,
    TrackRecord,
    UnscoredDecision,
)
from app.domain.provenance import Provenance


class PriceHistory(Protocol):
    """Daily closes for one security, by date."""

    async def closes(self, symbol: str) -> dict[date, float] | None: ...


class DecisionOutcomeService:
    """
    Join the decision journal to what the market did afterwards.

    The journal has recorded decisions since the CIO started making them
    and nothing has ever read them back against a price. That is the
    difference between a record and a track record, and it is what makes
    a platform that claims to improve able to.

    Nothing here re-decides. It measures the move since each decision and
    reports which decisions it could not measure, which on a young
    journal is most of them.
    """

    #: How long a decision must have stood before its price move says
    #: anything about it.
    #:
    #: Policy, and deliberately stated rather than buried: a decision made
    #: yesterday has a price move and no outcome, and reporting one would
    #: turn a day of noise into a claim about judgement. Thirty days is
    #: the same floor the platform holds a volatility or drawdown series
    #: to — long enough to be a window, short enough to be feedback.
    MINIMUM_DAYS = 30

    def __init__(
        self,
        journal: DecisionJournal,
        prices: PriceHistory,
    ) -> None:
        self._journal = journal
        self._prices = prices

    async def build(
        self,
        now: datetime | None = None,
    ) -> TrackRecord:
        """Measure every recorded decision that is old enough to measure."""

        moment = now or datetime.now(UTC)

        outcomes: list[DecisionOutcome] = []
        unscored: list[UnscoredDecision] = []

        for history in self._journal.histories().values():
            for record in history.records:
                days = (moment - record.decided_at).days

                if days < self.MINIMUM_DAYS:
                    unscored.append(
                        UnscoredDecision(
                            symbol=record.symbol,
                            state=record.state,
                            decided_at=record.decided_at,
                            reason=(
                                f"Decided {self._days(days)} ago; "
                                f"{self.MINIMUM_DAYS} days are needed before a "
                                "price move says anything about it."
                            ),
                        )
                    )

                    continue

                closes = await self._prices.closes(record.symbol)

                if not closes:
                    unscored.append(
                        UnscoredDecision(
                            symbol=record.symbol,
                            state=record.state,
                            decided_at=record.decided_at,
                            reason=(
                                f"{record.symbol} could not be priced, so what "
                                "it did after this decision is unknown."
                            ),
                        )
                    )

                    continue

                priced = self._close_on_or_before(closes, record.decided_at.date())

                if priced is None:
                    unscored.append(
                        UnscoredDecision(
                            symbol=record.symbol,
                            state=record.state,
                            decided_at=record.decided_at,
                            reason=(
                                "The price history does not reach back to "
                                f"{record.decided_at.date().isoformat()}."
                            ),
                        )
                    )

                    continue

                priced_on, price_at_decision = priced

                if price_at_decision <= 0:
                    unscored.append(
                        UnscoredDecision(
                            symbol=record.symbol,
                            state=record.state,
                            decided_at=record.decided_at,
                            reason=(
                                f"{record.symbol} was priced at zero on "
                                f"{priced_on.isoformat()}, so a move from it is "
                                "not a percentage."
                            ),
                        )
                    )

                    continue

                latest_on = max(closes)

                outcomes.append(
                    DecisionOutcome(
                        symbol=record.symbol,
                        state=record.state,
                        conviction=record.conviction,
                        decided_at=record.decided_at,
                        priced_on=priced_on,
                        price_at_decision=price_at_decision,
                        price_now=closes[latest_on],
                        days_elapsed=days,
                        reading=Provenance(
                            source="Yahoo Finance",
                            observed_at=datetime.combine(
                                latest_on,
                                datetime.min.time(),
                                tzinfo=UTC,
                            ),
                        ),
                    )
                )

        return TrackRecord(
            outcomes=tuple(outcomes),
            unscored=tuple(unscored),
        )

    @staticmethod
    def _close_on_or_before(
        closes: dict[date, float],
        wanted: date,
    ) -> tuple[date, float] | None:
        """
        The close the decision was made against.

        Markets shut. A decision taken on a Sunday is measured from
        Friday's close, which is the last price that existed when it was
        made — not the next one, which the decision could not have seen.

        A window that only starts after the decision cannot price it, and
        says so rather than reaching forward.
        """

        available = [day for day in closes if day <= wanted]

        if not available:
            return None

        # Not an unlimited reach back: a close from long before the
        # decision is not the price the decision was made against.
        day = max(available)

        if (wanted - day) > timedelta(days=7):
            return None

        return day, closes[day]

    @staticmethod
    def _days(days: int) -> str:
        if days <= 0:
            return "less than a day"

        return f"{days} day{'s' if days != 1 else ''}"
