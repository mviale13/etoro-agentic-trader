from datetime import datetime
from pathlib import Path

import pytest

from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_outcome_service import CommitteeOutcomeService


def test_buy_is_successful_when_price_rises(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = CommitteeOutcomeService(repository)

    outcome = service.record(
        recommendation_timestamp=datetime(2026, 7, 20, 9, 0),
        evaluation_timestamp=datetime(2026, 7, 27, 9, 0),
        symbol="MSFT",
        recommendation="BUY",
        entry_price=100.0,
        evaluation_price=110.0,
    )

    assert outcome.return_pct == 10.0
    assert outcome.successful is True

    events = repository.load_all()

    assert len(events) == 1
    assert events[0].event_type == "recommendation_outcome_recorded"
    assert events[0].symbol == "MSFT"
    assert events[0].payload["successful"] is True


def test_sell_is_successful_when_price_falls(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = CommitteeOutcomeService(repository)

    outcome = service.record(
        recommendation_timestamp=datetime(2026, 7, 20, 9, 0),
        evaluation_timestamp=datetime(2026, 7, 27, 9, 0),
        symbol="SPY",
        recommendation="SELL",
        entry_price=100.0,
        evaluation_price=90.0,
    )

    assert outcome.return_pct == -10.0
    assert outcome.successful is True


def test_hold_is_successful_inside_tolerance(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = CommitteeOutcomeService(repository)

    outcome = service.record(
        recommendation_timestamp=datetime(2026, 7, 20, 9, 0),
        evaluation_timestamp=datetime(2026, 7, 27, 9, 0),
        symbol="BTC",
        recommendation="HOLD",
        entry_price=100.0,
        evaluation_price=101.5,
    )

    assert outcome.return_pct == 1.5
    assert outcome.successful is True


def test_invalid_entry_price_is_rejected(tmp_path: Path) -> None:
    service = CommitteeOutcomeService(JsonEventRepository(tmp_path))

    with pytest.raises(
        ValueError,
        match="Entry price must be greater than zero.",
    ):
        service.record(
            recommendation_timestamp=datetime(2026, 7, 20, 9, 0),
            evaluation_timestamp=datetime(2026, 7, 27, 9, 0),
            symbol="MSFT",
            recommendation="BUY",
            entry_price=0.0,
            evaluation_price=110.0,
        )
