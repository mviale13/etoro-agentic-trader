"""What the Artificial CIO asks the investor to consider."""

from datetime import UTC, datetime

import pytest

from app.application.executive.executive_action_builder import (
    ExecutiveActionBuilder,
)
from app.cio.decision_state import DecisionState
from app.domain.executive.executive_action import ActionKind
from app.domain.executive_decision import ExecutiveDecision


def decision(
    state: DecisionState,
    missing: tuple[str, ...] = (),
) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol="MSFT",
        state=state,
        conviction=70,
        rationale="The gate the case stands at, in the CIO's own words.",
        missing_evidence=missing,
        decided_at=datetime(2026, 8, 5, tzinfo=UTC),
    )


def action(state: DecisionState, held: bool, **kwargs):
    return ExecutiveActionBuilder().build(decision(state, **kwargs), held=held)


def test_the_same_judgement_asks_different_things_of_an_owner() -> None:
    """
    The defect, stated: every case read "Monitor", including RECOMMEND.

    An action cannot be the decision state renamed either. RECOMMEND on a
    security the investor holds and RECOMMEND on one they do not are the
    same judgement about the business and different questions to put to
    the investor — and only the portfolio knows which case this is.
    """

    owned = action(DecisionState.RECOMMEND, held=True)
    unowned = action(DecisionState.RECOMMEND, held=False)

    assert owned.kind is ActionKind.ADD
    assert unowned.kind is ActionKind.OPEN

    assert owned.statement != unowned.statement
    assert "opening a position" in unowned.statement


@pytest.mark.parametrize("held", [True, False])
def test_every_decision_state_produces_a_distinct_consideration(
    held: bool,
) -> None:
    """
    No state falls through to a default, and none repeats another.

    Ownership is held fixed, because two states that ask the same thing
    of an owner and a non-owner alike are correct to say the same thing:
    researching a security does not depend on holding it.
    """

    statements = {state: action(state, held=held).statement for state in DecisionState}

    assert len(set(statements.values())) == len(DecisionState)


def test_only_the_states_that_turn_on_ownership_differ_by_it() -> None:
    """
    RECOMMEND, PREPARE and REJECT ask different things of an owner.

    INVESTIGATE and MONITOR do not: what is missing is evidence, and no
    amount of owning the security supplies it.
    """

    def differs(state: DecisionState) -> bool:
        return action(state, held=True).statement != action(state, held=False).statement

    assert differs(DecisionState.RECOMMEND)
    assert differs(DecisionState.PREPARE)
    assert differs(DecisionState.REJECT)

    assert not differs(DecisionState.INVESTIGATE)
    assert not differs(DecisionState.MONITOR)


@pytest.mark.parametrize(
    ("state", "held", "kind"),
    [
        (DecisionState.RECOMMEND, False, ActionKind.OPEN),
        (DecisionState.RECOMMEND, True, ActionKind.ADD),
        (DecisionState.PREPARE, True, ActionKind.HOLD),
        (DecisionState.PREPARE, False, ActionKind.WAIT),
        (DecisionState.INVESTIGATE, False, ActionKind.RESEARCH),
        (DecisionState.MONITOR, False, ActionKind.WATCH),
        (DecisionState.REJECT, True, ActionKind.REDUCE),
        (DecisionState.REJECT, False, ActionKind.NONE),
    ],
)
def test_the_kind_is_derived_from_the_case_and_the_book(
    state: DecisionState,
    held: bool,
    kind: ActionKind,
) -> None:
    assert action(state, held=held).kind is kind


def test_nothing_is_ever_worded_as_an_instruction_to_trade() -> None:
    """
    MOVRvest recommends; the investor decides.

    So no sentence commands, and none names a size, a price or a quantity
    — including the one about a case the CIO has rejected, which says to
    review the holding rather than to sell it.
    """

    forbidden = ("buy ", "sell ", "shares", "$", "%", "immediately")

    for state in DecisionState:
        for held in (True, False):
            statement = action(state, held=held).statement.lower()

            assert not any(word in statement for word in forbidden), statement
            assert statement.startswith(
                ("consider", "continue", "wait", "research", "watch", "review", "no ")
            ), statement


def test_a_case_short_of_something_names_it_rather_than_the_gate() -> None:
    """ "Research MSFT" is actionable only once the missing figure is named."""

    considered = action(
        DecisionState.INVESTIGATE,
        held=False,
        missing=("Valuation data is unavailable for MSFT.",),
    )

    assert considered.because == "Valuation data is unavailable for MSFT."


def test_the_next_dated_thing_rides_with_the_action() -> None:
    """The catalyst the cycle already dated, carried not reworded."""

    considered = ExecutiveActionBuilder().build(
        decision(DecisionState.PREPARE),
        held=True,
        catalysts=("Reports earnings in 6 days (Aug 11).",),
    )

    assert considered.checkpoint == "Reports earnings in 6 days (Aug 11)."

    # Nothing scheduled is null, never an invented date.
    assert action(DecisionState.PREPARE, held=True).checkpoint is None
