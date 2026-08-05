"""Which way an investment case has been moving."""

from datetime import UTC, datetime, timedelta

from app.cio.decision_state import DecisionState
from app.domain.decision_history import (
    DecisionHistory,
    DecisionRecord,
    TrendDirection,
)

START = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def history(*states: DecisionState) -> DecisionHistory:
    return DecisionHistory(
        symbol="MSFT",
        records=tuple(
            DecisionRecord(
                symbol="MSFT",
                state=state,
                conviction=60,
                rationale="Recorded at the time.",
                decided_at=START + timedelta(days=index),
            )
            for index, state in enumerate(states)
        ),
    )


def test_a_first_review_has_no_trend_at_all() -> None:
    """
    Not "stable" — nothing was recorded, so nothing has held.

    Calling a run of one settled would claim a history the Artificial CIO
    does not have, which is the same invention `previous_decisions`
    refused before it.
    """

    assert DecisionHistory(symbol="MSFT").trend_against(DecisionState.PREPARE) is None


def test_a_case_that_has_not_moved_is_stable_and_counted() -> None:
    """
    "PREPARE was also the previous decision" asked the reader to do the
    comparison. The direction is what they were computing.
    """

    trend = history(
        DecisionState.PREPARE,
        DecisionState.PREPARE,
    ).trend_against(DecisionState.PREPARE)

    assert trend is not None
    assert trend.direction is TrendDirection.STABLE

    # Today's decision counts: it is taken before it is recorded.
    assert "3 consecutive reviews" in trend.stated
    assert "2026-08-01" in trend.stated


def test_a_case_moving_up_the_lifecycle_is_improving() -> None:
    trend = history(DecisionState.PREPARE).trend_against(DecisionState.RECOMMEND)

    assert trend is not None
    assert trend.direction is TrendDirection.IMPROVING
    assert trend.stated == "Improving — PREPARE → RECOMMEND"


def test_a_case_moving_down_the_lifecycle_is_deteriorating() -> None:
    trend = history(DecisionState.RECOMMEND).trend_against(DecisionState.INVESTIGATE)

    assert trend is not None
    assert trend.direction is TrendDirection.DETERIORATING
    assert trend.stated == "Deteriorating — RECOMMEND → INVESTIGATE"


def test_direction_is_read_off_the_lifecycle_rather_than_judged() -> None:
    """
    The ranks already exist and already order the lifecycle.

    Any two states therefore compare the same way here as they do in the
    change feed's severity, which is what stops one surface calling a move
    an improvement while another calls it a decline.
    """

    for earlier in DecisionState:
        for later in DecisionState:
            trend = history(earlier).trend_against(later)

            assert trend is not None

            if later is earlier:
                assert trend.direction is TrendDirection.STABLE
            elif later.lifecycle_rank > earlier.lifecycle_rank:
                assert trend.direction is TrendDirection.IMPROVING
            else:
                assert trend.direction is TrendDirection.DETERIORATING
