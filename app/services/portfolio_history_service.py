"""The account's equity curve, read out of eToro's balance history."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.brokers.etoro_history import EtoroHistoryBroker
from app.config import Settings
from app.domain.equity_curve import EquityCurve, EquityPoint
from app.domain.provenance import Provenance


class PortfolioHistoryService:
    """
    Turn `/balances/history` into a series something can measure.

    The broker returns the body eToro sent and does not interpret it. This
    is where that body becomes an ordered daily curve — or nothing, which
    is a legitimate answer and the one given whenever the payload cannot
    be read with confidence.
    """

    SOURCE = "eToro"

    CURRENCY = "USD"

    #: How far back the curve is asked to reach.
    #:
    #: A year, matching the window each security's own drawdown is measured
    #: over, so the account figure and the holding figures describe
    #: comparable stretches of time. The account may not be a year old; the
    #: window that comes back is reported rather than assumed.
    WINDOW_DAYS = 365

    def __init__(
        self,
        broker: EtoroHistoryBroker | None = None,
    ) -> None:
        self._broker = broker or EtoroHistoryBroker(Settings())

    async def equity_curve(
        self,
        since: date,
    ) -> EquityCurve | None:
        """The account's daily value from `since` onward, or nothing."""

        body = await self._broker.balances(
            from_date=since,
            display_currency=self.CURRENCY,
        )

        return self.parse(body)

    @classmethod
    def parse(
        cls,
        body: Any,
        observed_at: datetime | None = None,
    ) -> EquityCurve | None:
        """
        Read the daily totals out of a balance-history body.

        A snapshot whose date or total cannot be read is not skipped. The
        curve is abandoned instead, because a drawdown is measured from a
        peak to a trough and a missing day may be either — a series with a
        hole in it would report a shallower fall than the account took,
        which is the direction that flatters.
        """

        if not isinstance(body, dict):
            return None

        snapshots = body.get("snapshots")

        if not isinstance(snapshots, list) or not snapshots:
            return None

        points: list[EquityPoint] = []

        for snapshot in snapshots:
            point = cls._point(snapshot)

            if point is None:
                return None

            points.append(point)

        return EquityCurve(
            points=tuple(sorted(points, key=lambda point: point.observed_on)),
            reading=Provenance(
                source=cls.SOURCE,
                observed_at=observed_at or datetime.now(UTC),
            ),
        )

    @classmethod
    def _point(
        cls,
        snapshot: Any,
    ) -> EquityPoint | None:
        if not isinstance(snapshot, dict):
            return None

        observed_on = cls._date(snapshot.get("date"))
        total = cls._total(snapshot)

        if observed_on is None or total is None:
            return None

        return EquityPoint(
            observed_on=observed_on,
            total_value_usd=total,
        )

    @classmethod
    def _total(
        cls,
        snapshot: dict[str, Any],
    ) -> float | None:
        """
        The day's account value in the currency that was asked for.

        `displayTotalBalance` is the figure eToro converted into
        `displayCurrency`, so it is the one that can be trusted to be in
        it. `totalBalance` is only used where the snapshot says outright
        that it is already in the same currency — a number whose currency
        is unstated is not a dollar figure just because dollars were asked
        for.
        """

        display = cls._number(snapshot.get("displayTotalBalance"))

        if display is not None:
            return display

        if snapshot.get("totalCurrencyIso") != cls.CURRENCY:
            return None

        return cls._number(snapshot.get("totalBalance"))

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        return float(value)

    @staticmethod
    def _date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None

        try:
            # Live snapshots carry a plain `2026-07-01`; a timestamped
            # variant would still be the same day.
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
