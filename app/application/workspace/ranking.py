"""Ranking shared by every service that evaluates several securities."""

from __future__ import annotations

from collections.abc import Sequence

from app.application.workspace.executive_workspace import ExecutiveWorkspace


def conviction_of(
    workspace: ExecutiveWorkspace,
) -> int:
    """The conviction the Artificial CIO assigned, or none at all."""

    return workspace.decision.conviction if workspace.decision else 0


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
