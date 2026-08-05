"""Turn a decision about a security into something to consider doing."""

from __future__ import annotations

from dataclasses import dataclass

from app.cio.decision_state import DecisionState
from app.domain.executive.executive_action import ActionKind, ExecutiveAction
from app.domain.executive_decision import ExecutiveDecision


@dataclass(slots=True)
class ExecutiveActionBuilder:
    """
    What the investor should consider, which the decision alone cannot say.

    Every case on the dashboard read "Monitor", including the ones the
    Artificial CIO had moved to RECOMMEND. The action was not derived from
    anything; it was a constant.

    It cannot be the decision state renamed, either. RECOMMEND on a
    security the investor already holds and RECOMMEND on one they do not
    are the same judgement and different actions — the first is about
    adding, the second about opening — and only the portfolio knows which
    case this is.

    Every line is a consideration. No sentence here instructs, and none
    names a size, a price or a quantity: this platform recommends, and the
    investor decides.
    """

    def build(
        self,
        decision: ExecutiveDecision,
        held: bool,
        catalysts: tuple[str, ...] = (),
    ) -> ExecutiveAction:
        symbol = decision.symbol

        kind, statement = self._considered(decision.state, held, symbol)

        return ExecutiveAction(
            kind=kind,
            statement=statement,
            # The Artificial CIO's own words for why the case stands where
            # it does. Rewriting them here would be a second opinion.
            because=self._because(decision),
            checkpoint=catalysts[0] if catalysts else None,
        )

    @staticmethod
    def _considered(
        state: DecisionState,
        held: bool,
        symbol: str,
    ) -> tuple[ActionKind, str]:
        """The action, from where the case stands and what is already owned."""

        if state is DecisionState.RECOMMEND:
            if held:
                return (
                    ActionKind.ADD,
                    f"Consider adding to {symbol}.",
                )

            return (
                ActionKind.OPEN,
                f"Consider opening a position in {symbol}.",
            )

        if state is DecisionState.PREPARE:
            if held:
                return (
                    ActionKind.HOLD,
                    f"Continue holding {symbol}. Nothing supports adding yet.",
                )

            return (
                ActionKind.WAIT,
                f"Wait before opening {symbol}. The case is credible but "
                "not yet actionable.",
            )

        if state is DecisionState.INVESTIGATE:
            return (
                ActionKind.RESEARCH,
                f"Research {symbol} before the thesis can progress.",
            )

        if state is DecisionState.MONITOR:
            return (
                ActionKind.WATCH,
                f"Watch {symbol}. There is nothing to act on yet.",
            )

        # REJECT. A held position the case no longer supports is worth
        # reviewing; one the investor never opened asks nothing of them.
        # Neither is worded as an instruction to sell — that decision is
        # the investor's, and this platform does not take it.
        if held:
            return (
                ActionKind.REDUCE,
                f"Review whether to keep holding {symbol}.",
            )

        return (
            ActionKind.NONE,
            f"No action on {symbol}.",
        )

    @staticmethod
    def _because(decision: ExecutiveDecision) -> str:
        """
        Why the case stands where it does, in the CIO's own words.

        Where the case is short of something specific, that is the more
        useful answer: "Research MSFT" is worth acting on only once the
        reader knows which figure is missing.
        """

        if decision.state is DecisionState.INVESTIGATE and decision.missing_evidence:
            return decision.missing_evidence[0]

        return decision.rationale
