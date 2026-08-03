"""The account's own equity curve, and the fall measured off it."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from app.domain.equity_curve import EquityCurve, EquityPoint
from app.domain.provenance import Provenance
from app.services.portfolio_drawdown_service import PortfolioDrawdownService
from app.services.portfolio_history_service import PortfolioHistoryService

READ_AT = datetime(2026, 8, 3, 16, 51, tzinfo=UTC)


def snapshot(day: str, total: float) -> dict[str, object]:
    """One day of `/balances/history`, shaped as the live API returns it."""

    return {
        "date": day,
        "displayTotalBalance": total,
        "totalBalance": total,
        "totalCurrencyIso": "USD",
        "totalCash": 802.49,
        "accountSnapshots": [{"accountId": "27756168", "total": total}],
    }


def body(*totals: float, start: date = date(2026, 7, 1)) -> dict[str, object]:
    return {
        "displayCurrency": "USD",
        "gcid": 28038841,
        "snapshots": [
            snapshot((start + timedelta(days=offset)).isoformat(), total)
            for offset, total in enumerate(totals)
        ],
    }


def curve(*totals: float) -> EquityCurve:
    parsed = PortfolioHistoryService.parse(body(*totals), observed_at=READ_AT)

    assert parsed is not None

    return parsed


def falling_then_recovering() -> tuple[float, ...]:
    """40 days: 20 flat, a 25% fall, then a partial recovery."""

    return (*(100.0,) * 20, *(75.0,) * 10, *(90.0,) * 10)


def test_the_live_payload_shape_becomes_a_curve() -> None:
    parsed = PortfolioHistoryService.parse(
        body(44714.24, 46000.92, 45100.00),
        observed_at=READ_AT,
    )

    assert parsed is not None
    assert parsed.observations == 3
    assert parsed.points[0] == EquityPoint(date(2026, 7, 1), 44714.24)
    assert parsed.starts_on == date(2026, 7, 1)
    assert parsed.ends_on == date(2026, 7, 3)
    assert parsed.reading == Provenance(source="eToro", observed_at=READ_AT)


def test_snapshots_are_ordered_by_date_whatever_order_they_arrived_in() -> None:
    """A peak-to-trough measure reads the series forwards or not at all."""

    payload = body(100.0, 90.0, 120.0)
    snapshots = payload["snapshots"]

    assert isinstance(snapshots, list)

    payload["snapshots"] = list(reversed(snapshots))

    parsed = PortfolioHistoryService.parse(payload)

    assert parsed is not None
    assert parsed.values == (100.0, 90.0, 120.0)


def test_a_snapshot_that_cannot_be_read_abandons_the_whole_curve() -> None:
    """
    Skipping the day would leave a hole, and the missing day may be the
    trough — a series with a gap reports a shallower fall than the account
    took, which is the direction that flatters.
    """

    payload = body(100.0, 90.0, 120.0)
    snapshots = payload["snapshots"]

    assert isinstance(snapshots, list)

    del snapshots[1]["displayTotalBalance"]
    del snapshots[1]["totalBalance"]

    assert PortfolioHistoryService.parse(payload) is None


def test_a_total_in_an_unstated_currency_is_not_read_as_dollars() -> None:
    """Asking for USD does not make an unlabelled number a dollar figure."""

    payload = body(100.0, 90.0)
    snapshots = payload["snapshots"]

    assert isinstance(snapshots, list)

    for item in snapshots:
        del item["displayTotalBalance"]

    snapshots[1]["totalCurrencyIso"] = "EUR"

    assert PortfolioHistoryService.parse(payload) is None


def test_an_empty_or_unrecognised_body_is_no_curve_at_all() -> None:
    assert PortfolioHistoryService.parse({"snapshots": []}) is None
    assert PortfolioHistoryService.parse({"balances": []}) is None
    assert PortfolioHistoryService.parse([]) is None
    assert PortfolioHistoryService.parse(None) is None


def test_the_broker_is_asked_for_the_window_the_caller_named() -> None:
    class BrokerStub:
        def __init__(self) -> None:
            self.asked: dict[str, object] = {}

        async def balances(
            self,
            from_date: date | None = None,
            to_date: date | None = None,
            display_currency: str = "USD",
        ) -> object:
            self.asked = {
                "from_date": from_date,
                "display_currency": display_currency,
            }

            return body(100.0, 95.0)

    broker = BrokerStub()

    service = PortfolioHistoryService(broker=broker)  # type: ignore[arg-type]

    parsed = asyncio.run(service.equity_curve(date(2025, 8, 3)))

    assert parsed is not None
    assert broker.asked == {
        "from_date": date(2025, 8, 3),
        "display_currency": "USD",
    }


def test_the_deepest_fall_is_measured_with_its_window() -> None:
    measured = PortfolioDrawdownService().measure(curve(*falling_then_recovering()))

    assert measured is not None
    assert measured.depth == 0.25

    assert measured.peak_on == date(2026, 7, 1)
    assert measured.peak_value_usd == 100.0
    assert measured.trough_on == date(2026, 7, 21)
    assert measured.trough_value_usd == 75.0

    # The window is stated, because 25% over 40 days and 25% over 40 months
    # are not the same statement about an account.
    assert measured.observations == 40
    assert measured.starts_on == date(2026, 7, 1)
    assert measured.ends_on == date(2026, 8, 9)

    # Still below the peak it fell from, and said so separately.
    assert measured.current_depth == 0.1
    assert not measured.recovered


def test_a_history_too_short_to_measure_is_reported_as_no_measurement() -> None:
    """
    The deepest fall inside eleven days is not "the account's drawdown",
    and putting it on a dashboard under that name would invite a decision
    nobody could defend.
    """

    assert PortfolioDrawdownService().measure(curve(*(100.0,) * 11)) is None
    assert PortfolioDrawdownService().measure(None) is None


def test_thirty_daily_balances_are_enough() -> None:
    """The floor the per-security drawdown is held to, held to here too."""

    measured = PortfolioDrawdownService().measure(
        curve(*(100.0,) * 29, 80.0),
    )

    assert measured is not None
    assert measured.depth == 0.2


def test_the_score_is_the_share_of_the_investors_own_tolerance_used() -> None:
    """
    15% is a mild year for one investor and a broken promise to another,
    so the fall is scored against what this investor said they could take.
    """

    measured = PortfolioDrawdownService().measure(curve(*falling_then_recovering()))

    assert measured is not None

    assert PortfolioDrawdownService.risk_score(measured, 50.0) == 0.5
    assert PortfolioDrawdownService.risk_score(measured, 25.0) == 1.0

    # Past the mandate is still 1.0: the score is bounded, and the account
    # having fallen further than allowed is already the worst reading.
    assert PortfolioDrawdownService.risk_score(measured, 10.0) == 1.0


def test_an_unstated_tolerance_falls_back_to_the_platforms_own() -> None:
    measured = PortfolioDrawdownService().measure(curve(*falling_then_recovering()))

    assert measured is not None

    default = PortfolioDrawdownService.risk_score(measured, None)

    assert default == PortfolioDrawdownService.risk_score(
        measured,
        PortfolioDrawdownService.DEFAULT_TOLERANCE_PCT,
    )

    # A tolerance of zero is not a tolerance; dividing by it would be a
    # crash on a dashboard rather than a reading.
    assert PortfolioDrawdownService.risk_score(measured, 0.0) == default
