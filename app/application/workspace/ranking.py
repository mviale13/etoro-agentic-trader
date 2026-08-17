"""Ranking shared by every service that evaluates several securities."""

from __future__ import annotations

from collections.abc import Sequence

from app.application.workspace.executive_workspace import ExecutiveWorkspace


def conviction_of(
    workspace: ExecutiveWorkspace,
) -> tuple[int, int]:
    """Where this evaluation sits in the order, and never a conviction.

    A sort position, deliberately not a number anyone can read. A case the
    CIO put no conviction on is ordered last — it cited no reason to act,
    so nothing about it competes for attention — but it is ordered last
    *as an absence*, on the first term of this key, rather than by being
    called a zero. Zero is the bottom of the conviction scale and is
    itself a judgment; withheld is the absence of one, and a ranking that
    spelt them the same way would let a case with no cited evidence be
    compared against one judged worthless.
    """

    decision = workspace.decision

    if decision is None or decision.conviction is None:
        return (0, 0)

    return (1, decision.conviction)


def rank_by_conviction(
    workspaces: Sequence[ExecutiveWorkspace],
) -> tuple[ExecutiveWorkspace, ...]:
    """
    Order evaluations by the conviction behind them, highest first.

    Ranking expresses priority, never certainty, and it never drops an
    evaluation: everything judged is reported.
    """

    return tuple(
        sorted(
            workspaces,
            key=conviction_of,
            reverse=True,
        )
    )
