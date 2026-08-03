from datetime import UTC, datetime
from pathlib import Path

from app.application.change_feed.change_feed_service import ChangeFeedService
from app.application.learning.decision_journal import DecisionJournal
from app.application.services.market_service import MarketService
from app.cio.decision_state import DecisionState
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeSeverity,
)
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.repositories.json_event_repository import JsonEventRepository
from tests.test_decision_journal import make_decision


def make_service(tmp_path: Path) -> tuple[ChangeFeedService, DecisionJournal]:
    journal = DecisionJournal(JsonEventRepository(tmp_path))

    return ChangeFeedService(journal=journal), journal


def test_nothing_recorded_reports_no_changes(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)

    assert service.build().events == ()


def test_an_unchanged_decision_is_not_a_change(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )

    assert service.build().events == ()


def test_a_changed_decision_is_reported(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        )
    )

    feed = service.build()

    assert feed.total == 1

    change = feed.events[0]

    assert change.title == "MSFT moved from MONITOR to PREPARE"
    assert change.description == "The investment case satisfies every gate."
    assert change.category is ChangeCategory.DECISION
    assert change.timestamp == datetime(2026, 7, 30, 9, 0, tzinfo=UTC)
    assert change.action_required is True
    assert feed.action_required is True


def test_severity_measures_how_far_the_decision_moved(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    for index, state in enumerate(
        (
            DecisionState.REJECT,
            DecisionState.MONITOR,
            DecisionState.PREPARE,
            DecisionState.REJECT,
        )
    ):
        journal.record(
            make_decision(
                state=state,
                decided_at=datetime(2026, 7, 28 + index, 9, 0, tzinfo=UTC),
            )
        )

    severities = [change.severity for change in reversed(service.build().events)]

    assert severities == [
        ChangeSeverity.LOW,
        ChangeSeverity.MEDIUM,
        ChangeSeverity.HIGH,
    ]


def test_changes_are_reported_newest_first(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="NVDA",
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="NVDA",
            state=DecisionState.INVESTIGATE,
            decided_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        )
    )

    titles = [change.title for change in service.build().events]

    assert titles == [
        "NVDA moved from MONITOR to INVESTIGATE",
        "MSFT moved from MONITOR to PREPARE",
    ]


def test_the_feed_can_be_narrowed_to_the_symbols_held(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    for symbol in ("MSFT", "NVDA"):
        journal.record(
            make_decision(
                symbol=symbol,
                state=DecisionState.MONITOR,
                decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
            )
        )
        journal.record(
            make_decision(
                symbol=symbol,
                state=DecisionState.PREPARE,
                decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
            )
        )

    feed = service.build(symbols=["msft"])

    assert [change.title for change in feed.events] == [
        "MSFT moved from MONITOR to PREPARE"
    ]


def test_the_feed_is_capped(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    states = (
        DecisionState.REJECT,
        DecisionState.MONITOR,
        DecisionState.INVESTIGATE,
        DecisionState.PREPARE,
    )

    for index, state in enumerate(states):
        journal.record(
            make_decision(
                state=state,
                decided_at=datetime(2026, 7, 28 + index, 9, 0, tzinfo=UTC),
            )
        )

    assert service.build(limit=2).total == 2


def market_at(
    moment: datetime,
    *,
    change_percent: float = 0.0,
    vix: float | None = 16.0,
) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500 ETF",
                price=600.0,
                change_percent=change_percent,
                reading=Provenance(source="Yahoo Finance", observed_at=moment),
            ),
        ),
        vix=vix,
        timestamp=moment,
    )


class RecordedMarket:
    """Stands in for the archive, holding what it recorded, newest first."""

    def __init__(self, *snapshots: MarketSnapshot) -> None:
        self._snapshots = snapshots

    def recent(self, limit: int = 2) -> tuple[MarketSnapshot, ...]:
        return self._snapshots[:limit]


def test_a_market_that_moved_is_reported_beside_the_decisions(
    tmp_path: Path,
) -> None:
    """
    Market movements were absent from this feed until anything recorded them.

    Not because the market stood still — because quotes were cached for
    fifteen minutes and discarded, so no two readings ever existed at once.
    """

    journal = DecisionJournal(JsonEventRepository(tmp_path))

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )

    service = ChangeFeedService(
        journal=journal,
        market=RecordedMarket(
            market_at(datetime(2026, 7, 30, 9, 0, tzinfo=UTC), change_percent=-1.5),
            market_at(datetime(2026, 7, 29, 9, 0, tzinfo=UTC), change_percent=1.5),
        ),
    )

    events = service.build().events

    assert [event.category for event in events] == [
        ChangeCategory.MARKET,
        ChangeCategory.DECISION,
    ]
    assert events[0].title == "Market mood moved from positive to negative"


def test_one_observation_is_not_a_movement(tmp_path: Path) -> None:
    """
    A platform on its first cycle has one reading and no history.

    Reporting a change against nothing would be inventing the observation
    that came before.
    """

    service, _ = make_service(tmp_path)

    only_one = ChangeFeedService(
        journal=service.journal,
        market=RecordedMarket(market_at(datetime(2026, 7, 30, 9, 0, tzinfo=UTC))),
    )

    assert only_one.build().events == ()


def test_no_market_history_leaves_the_decisions_untouched(tmp_path: Path) -> None:
    """A caller with no archive gets the decisions alone, which is honest."""

    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )

    assert [event.category for event in service.build().events] == [
        ChangeCategory.DECISION
    ]


def test_narrowing_to_held_symbols_does_not_narrow_the_market(
    tmp_path: Path,
) -> None:
    """
    The market moved for the account, not for any holding in it.

    Narrowing the feed to what the investor holds must not drop it.
    """

    journal = DecisionJournal(JsonEventRepository(tmp_path))

    service = ChangeFeedService(
        journal=journal,
        market=RecordedMarket(
            market_at(datetime(2026, 7, 30, 9, 0, tzinfo=UTC), vix=31.0),
            market_at(datetime(2026, 7, 29, 9, 0, tzinfo=UTC), vix=12.0),
        ),
    )

    events = service.build(symbols=["MSFT"]).events

    assert [event.category for event in events] == [ChangeCategory.MACRO]
