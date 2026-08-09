"""Why the Artificial CIO's conviction moved, when it did."""

from datetime import UTC, datetime, timedelta

from app.cio.decision_state import DecisionState
from app.domain.asset_class import AssetClass
from app.domain.decision_history import (
    DecisionHistory,
    DecisionRecord,
    RecordedScores,
)
from app.domain.score_basis import score_labels_for

START = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def recorded(
    conviction: int,
    scores: RecordedScores | None = None,
    days: int = 0,
) -> DecisionRecord:
    return DecisionRecord(
        symbol="MSFT",
        state=DecisionState.PREPARE,
        conviction=conviction,
        rationale="Recorded at the time.",
        decided_at=START + timedelta(days=days),
        scores=scores if scores is not None else RecordedScores(),
    )


def history(*records: DecisionRecord) -> DecisionHistory:
    return DecisionHistory(symbol="MSFT", records=records)


def test_an_unchanged_conviction_is_not_a_change() -> None:
    """
    Reported as the absence of a change, not as a zero.

    An arrow on every case every day is an arrow that means nothing.
    """

    assert history(recorded(70)).conviction_change_against(70, RecordedScores()) is None


def test_a_first_decision_has_nothing_to_have_moved_from() -> None:
    assert (
        DecisionHistory(symbol="MSFT").conviction_change_against(
            70,
            RecordedScores(),
        )
        is None
    )


def test_the_move_is_arithmetic_on_two_recorded_numbers() -> None:
    change = history(
        recorded(74, RecordedScores(quality=62)),
    ).conviction_change_against(82, RecordedScores(quality=80))

    assert change is not None
    assert change.previous == 74
    assert change.delta == 8
    assert change.stated == "+8 conviction"


def test_a_fall_keeps_its_sign() -> None:
    change = history(
        recorded(82, RecordedScores(quality=80)),
    ).conviction_change_against(70, RecordedScores(quality=62))

    assert change is not None
    assert change.delta == -12
    assert change.stated == "-12 conviction"


def test_each_reason_is_a_score_that_measurably_moved() -> None:
    """
    Named and quoted, both ends. Nothing is attributed that cannot be shown.

    Every score runs the same way, so a rise is an improvement whichever
    one it is — the property the whole set was aligned for.
    """

    change = history(
        recorded(
            70,
            RecordedScores(
                quality=62,
                evidence=80,
                valuation=55,
                safety=55,
                portfolio_fit=98,
            ),
        ),
    ).conviction_change_against(
        78,
        RecordedScores(
            quality=80,
            evidence=80,
            valuation=80,
            safety=35,
            portfolio_fit=98,
        ),
    )

    assert change is not None
    assert change.because == (
        "Business quality improved, 62 → 80",
        "Valuation attractiveness improved, 55 → 80",
        "Safety fell, 55 → 35",
    )

    # The two that did not move are not mentioned at all.
    assert not any("Evidence" in line for line in change.because)
    assert not any("Portfolio fit" in line for line in change.because)


def test_a_tokens_quality_move_is_an_asset_quality_move() -> None:
    """The reasons are worded the way this security's dossier names them.

    The record's keys never vary; the labels do. A crypto dossier calls
    the quality score "Asset quality", and a conviction move under it
    saying "Business quality improved" would present a network reading
    as a company judgment nobody made.
    """

    change = history(
        recorded(70, RecordedScores(quality=62)),
    ).conviction_change_against(
        78,
        RecordedScores(quality=80),
        labels=score_labels_for(AssetClass.CRYPTO),
    )

    assert change is not None
    assert change.because == ("Asset quality improved, 62 → 80",)


def test_a_score_missing_on_either_side_is_passed_over() -> None:
    """An unmeasured score cannot have moved, and is not said to have."""

    change = history(
        recorded(70, RecordedScores(quality=62, valuation=None)),
    ).conviction_change_against(75, RecordedScores(quality=None, valuation=80))

    assert change is not None
    assert change.because == ()
    assert change.unexplained is False


def test_a_decision_recorded_before_the_scores_says_so() -> None:
    """
    The honest silence this exists for.

    Every decision recorded before the journal kept scores can say the
    conviction moved and cannot say why. An empty reason list would read
    as "nothing moved", which nobody established.
    """

    change = history(recorded(70)).conviction_change_against(
        78,
        RecordedScores(quality=80),
    )

    assert change is not None
    assert change.delta == 8
    assert change.unexplained is True
    assert change.because == ()
