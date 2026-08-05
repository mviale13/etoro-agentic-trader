"""What the dashboard is told about the platform's own track record."""

from datetime import UTC, date, datetime

from app.api.routes.track_record import _payload, _verdict
from app.cio.decision_state import DecisionState
from app.domain.decision_outcome import (
    DecisionOutcome,
    TrackRecord,
    UnscoredDecision,
)
from app.domain.provenance import Provenance


def make_outcome(
    symbol: str = "MSFT",
    state: DecisionState = DecisionState.RECOMMEND,
    price_at_decision: float = 100.0,
    price_now: float = 110.0,
) -> DecisionOutcome:
    return DecisionOutcome(
        symbol=symbol,
        state=state,
        conviction=70,
        decided_at=datetime(2026, 6, 1, tzinfo=UTC),
        priced_on=date(2026, 6, 1),
        price_at_decision=price_at_decision,
        price_now=price_now,
        days_elapsed=65,
        reading=Provenance(
            source="Yahoo Finance",
            observed_at=datetime(2026, 8, 5, tzinfo=UTC),
        ),
    )


def make_unscored(reason: str) -> UnscoredDecision:
    return UnscoredDecision(
        symbol="NVDA",
        state=DecisionState.MONITOR,
        decided_at=datetime(2026, 7, 30, tzinfo=UTC),
        reason=reason,
    )


def test_the_verdict_is_worded_once_in_the_backend() -> None:
    assert _verdict(make_outcome()) == "as decided"
    assert _verdict(make_outcome(price_now=90.0)) == "against the decision"

    # A decision that implied nothing is not coloured as a result.
    assert _verdict(make_outcome(state=DecisionState.MONITOR)) == "not a call"

    # Nor is a security that barely moved: evidence for nobody.
    assert _verdict(make_outcome(price_now=100.1)) == "not a call"


def test_the_payload_carries_counts_absences_and_reasons() -> None:
    record = TrackRecord(
        outcomes=(make_outcome(), make_outcome("ASML", price_now=95.0)),
        unscored=(
            make_unscored("Decided 6 days ago; 30 days are needed."),
            make_unscored("Decided 6 days ago; 30 days are needed."),
        ),
    )

    served = _payload(record)

    assert served.recorded == 4
    assert served.measured == 2
    assert served.calls == 2
    assert served.agreed == 1

    # Two calls is not a rate, and the bar is stated beside the absence.
    assert served.hit_rate is None
    assert served.minimum_calls == TrackRecord.MINIMUM_CALLS

    # The same sentence twice is one reason with a count of two.
    assert served.unscored_total == 2
    assert len(served.unscored_reasons) == 1
    assert served.unscored_reasons[0].count == 2

    # Best move first, and every row carries its provenance.
    assert [item.symbol for item in served.outcomes] == ["MSFT", "ASML"]
    assert served.outcomes[0].change_pct == 10.0
    assert "Yahoo Finance" in served.outcomes[0].reading


def test_an_empty_journal_serves_zeros_and_no_rate() -> None:
    served = _payload(TrackRecord(outcomes=(), unscored=()))

    assert served.recorded == 0
    assert served.measured == 0
    assert served.hit_rate is None
    assert served.outcomes == []
    assert served.unscored_reasons == []
