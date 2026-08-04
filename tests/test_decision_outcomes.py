"""Scoring a decision against what the security did next."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from app.application.learning.decision_journal import DecisionJournal
from app.application.learning.decision_outcome_service import (
    DecisionOutcomeService,
)
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import ExecutiveDecision
from app.domain.event import Event
from app.domain.event_type import EventType

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


class Repository:
    """An event store held in memory, in the order things happened."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def save(self, event: Event) -> None:
        self.events.append(event)

    def load_all(self) -> list[Event]:
        return list(self.events)


class Prices:
    """Daily closes the test decides, and a record of what was asked for."""

    def __init__(self, **series: dict[date, float] | None) -> None:
        self._series = series
        self.asked: list[str] = []

    async def closes(self, symbol: str) -> dict[date, float] | None:
        self.asked.append(symbol)

        return self._series.get(symbol)


def rising(start: date, days: int, first: float, last: float) -> dict[date, float]:
    """A straight line from `first` to `last`, one close per day."""

    step = (last - first) / (days - 1)

    return {
        start + timedelta(days=offset): first + step * offset for offset in range(days)
    }


def journal(repository: Repository, *decisions: ExecutiveDecision) -> DecisionJournal:
    written = DecisionJournal(repository)

    for decision in decisions:
        written.record(decision)

    return written


def decision(
    symbol: str,
    state: DecisionState,
    days_ago: int,
    conviction: int = 70,
) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol=symbol,
        state=state,
        conviction=conviction,
        rationale="recorded by a test",
        decided_at=NOW - timedelta(days=days_ago),
    )


def build(journal_: DecisionJournal, prices: Prices):
    return asyncio.run(DecisionOutcomeService(journal_, prices).build(now=NOW))


def test_a_decision_is_measured_against_the_close_it_was_made_on() -> None:
    repository = Repository()

    record = build(
        journal(repository, decision("MSFT", DecisionState.RECOMMEND, days_ago=40)),
        Prices(MSFT=rising(date(2026, 6, 1), 70, 100.0, 169.0)),
    )

    assert len(record.outcomes) == 1

    outcome = record.outcomes[0]

    assert outcome.symbol == "MSFT"
    assert outcome.priced_on == date(2026, 6, 24)
    assert outcome.price_at_decision == 123.0
    assert outcome.days_elapsed == 40
    assert round(outcome.change, 4) == round((169.0 - 123.0) / 123.0, 4)


def test_a_decision_too_recent_to_have_an_outcome_is_not_given_one() -> None:
    """
    A decision made yesterday has a price move and no outcome. Reporting
    one turns a day of noise into a claim about judgement.
    """

    repository = Repository()

    record = build(
        journal(repository, decision("MSFT", DecisionState.RECOMMEND, days_ago=1)),
        Prices(MSFT=rising(date(2026, 6, 1), 70, 100.0, 169.0)),
    )

    assert not record.outcomes
    assert len(record.unscored) == 1
    assert "1 day ago" in record.unscored[0].reason
    assert "30 days are needed" in record.unscored[0].reason


def test_only_decisions_that_asked_for_something_are_scored_as_calls() -> None:
    """
    MONITOR and INVESTIGATE are the platform saying it does not know yet.
    Scoring them would build a track record out of decisions that never
    claimed anything.
    """

    repository = Repository()
    prices = Prices(
        MSFT=rising(date(2026, 6, 1), 70, 100.0, 169.0),
        DIS=rising(date(2026, 6, 1), 70, 100.0, 169.0),
        MCD=rising(date(2026, 6, 1), 70, 100.0, 169.0),
    )

    record = build(
        journal(
            repository,
            decision("MSFT", DecisionState.RECOMMEND, days_ago=40),
            decision("DIS", DecisionState.INVESTIGATE, days_ago=40),
            decision("MCD", DecisionState.MONITOR, days_ago=40),
        ),
        prices,
    )

    assert len(record.outcomes) == 3
    assert {outcome.symbol for outcome in record.calls} == {"MSFT"}

    by_symbol = {outcome.symbol: outcome for outcome in record.outcomes}

    assert by_symbol["DIS"].moved_as_the_decision_implied is None
    assert by_symbol["MCD"].moved_as_the_decision_implied is None


def test_a_rejection_agrees_with_a_fall_not_a_rise() -> None:
    """
    REJECT says this is not worth owning, so a fall agrees with it.
    Counting the rise as a loss would be the opposite error.
    """

    repository = Repository()

    falling = {
        day: 200.0 - price
        for day, price in rising(date(2026, 6, 1), 70, 100.0, 169.0).items()
    }

    vindicated = build(
        journal(repository, decision("UUUU", DecisionState.REJECT, days_ago=40)),
        Prices(UUUU=falling),
    )

    assert vindicated.outcomes[0].moved_as_the_decision_implied is True
    assert vindicated.outcomes[0].change < 0

    missed = build(
        journal(Repository(), decision("UUUU", DecisionState.REJECT, days_ago=40)),
        Prices(UUUU=rising(date(2026, 6, 1), 70, 100.0, 169.0)),
    )

    assert missed.outcomes[0].moved_as_the_decision_implied is False


def test_a_security_that_barely_moved_is_evidence_for_nobody() -> None:
    """
    The first live run priced a holding at exactly its decision price and
    marked it against the decision. A flat month is not a black mark.
    """

    repository = Repository()

    flat = {
        date(2026, 6, 24): 21.06,
        date(2026, 6, 25): 21.06,
        date(2026, 8, 3): 21.06,
    }

    record = build(
        journal(repository, decision("UMI.BR", DecisionState.PREPARE, days_ago=40)),
        Prices(**{"UMI.BR": flat}),
    )

    assert record.outcomes[0].change == 0.0
    assert record.outcomes[0].moved_as_the_decision_implied is None
    assert not record.calls


def test_a_symbol_that_cannot_be_priced_is_named_not_dropped() -> None:
    repository = Repository()

    record = build(
        journal(repository, decision("#1238", DecisionState.PREPARE, days_ago=40)),
        Prices(),
    )

    assert not record.outcomes
    assert record.unscored[0].symbol == "#1238"
    assert "could not be priced" in record.unscored[0].reason


def test_a_price_history_that_starts_after_the_decision_cannot_price_it() -> None:
    """It must not reach forward to a close the decision could not see."""

    repository = Repository()

    record = build(
        journal(repository, decision("MSFT", DecisionState.RECOMMEND, days_ago=60)),
        Prices(MSFT=rising(date(2026, 7, 20), 15, 100.0, 114.0)),
    )

    assert not record.outcomes
    assert "does not reach back to" in record.unscored[0].reason


def test_a_weekend_decision_is_measured_from_the_last_close_before_it() -> None:
    """Markets shut. Friday's close is the price the decision was made against."""

    repository = Repository()

    weekdays = {
        day: 100.0 for day in (date(2026, 6, 24), date(2026, 6, 25), date(2026, 6, 26))
    }
    weekdays[date(2026, 6, 29)] = 150.0

    # Decided on Sunday 28 June, 36 days before NOW.
    record = build(
        journal(repository, decision("MSFT", DecisionState.RECOMMEND, days_ago=36)),
        Prices(MSFT=weekdays),
    )

    assert record.outcomes[0].decided_at.date() == date(2026, 6, 28)
    assert record.outcomes[0].priced_on == date(2026, 6, 26)


def test_each_security_is_priced_once_however_often_it_was_decided() -> None:
    """The journal records one decision per state per day; the provider limits."""

    repository = Repository()
    prices = Prices(MSFT=rising(date(2026, 6, 1), 70, 100.0, 169.0))

    record = build(
        journal(
            repository,
            decision("MSFT", DecisionState.PREPARE, days_ago=40),
            decision("MSFT", DecisionState.RECOMMEND, days_ago=35),
        ),
        prices,
    )

    assert len(record.outcomes) == 2
    assert prices.asked == ["MSFT", "MSFT"]


def test_a_hit_rate_is_withheld_until_there_are_enough_calls() -> None:
    """A rate over three decisions is not a rate."""

    repository = Repository()
    prices = Prices(
        **{
            symbol: rising(date(2026, 6, 1), 70, 100.0, 169.0)
            for symbol in ("MSFT", "DIS", "MCD")
        }
    )

    record = build(
        journal(
            repository,
            decision("MSFT", DecisionState.RECOMMEND, days_ago=40),
            decision("DIS", DecisionState.PREPARE, days_ago=40),
            decision("MCD", DecisionState.PREPARE, days_ago=40),
        ),
        prices,
    )

    assert len(record.calls) == 3
    assert record.agreed == 3
    assert record.hit_rate is None


def test_an_unreadable_record_never_becomes_an_outcome() -> None:
    """A state the current DecisionState no longer knows is skipped."""

    repository = Repository()

    repository.save(
        Event(
            timestamp=NOW - timedelta(days=40),
            event_type=EventType.EXECUTIVE_DECISION_RECORDED,
            symbol="MSFT",
            payload={"state": "ABOLISHED", "conviction": 70, "rationale": ""},
        )
    )

    record = build(
        DecisionJournal(repository),
        Prices(MSFT=rising(date(2026, 6, 1), 70, 100.0, 169.0)),
    )

    assert not record.outcomes
    assert not record.unscored
