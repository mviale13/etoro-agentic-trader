"""Ranking shared by every service that evaluates several securities.

**A conviction is comparable only against one computed over the same
score families.** The owner's ruling of 2026-08-21 (prerequisite 2,
`SECURITY_VOLATILITY_DECISION_ROLE.md`), and the measurement behind it
is concrete: quality is a provider proxy or absent for 60 of 64 stored
equities, and an unmeasured quality is *omitted* from the conviction
mean rather than penalised — so LUNR, judged on four families, outranks
AMD, judged on five, on two numbers that were never on one scale.

Ordering asserts comparability. Two numbers under a rank say *this one
is higher than that one*, and where the denominators differ that
sentence has no referent. So the order is withheld rather than reversed,
hedged or re-weighted: this module orders by conviction where coverage
is uniform, and by nothing where it is not.
"""

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


def coverage_of(workspace: ExecutiveWorkspace) -> tuple[str, ...] | None:
    """Which score families this evaluation's conviction did without.

    The absent families as the decision itself recorded them (#231's
    amendment 4), never re-derived here. None for an evaluation carrying
    no conviction: nothing was computed, so there is no coverage to
    compare, and such a case is already ordered last as an absence
    rather than as a low number.
    """

    decision = workspace.decision

    if decision is None or decision.conviction is None:
        return None

    return decision.conviction_absent_families


def comparable(workspaces: Sequence[ExecutiveWorkspace]) -> bool:
    """Whether these convictions were computed over the same families.

    **Counts are not enough.** Two securities each judged on four of
    five families are not comparable when one is missing business
    quality and the other is missing valuation: the numbers average
    different things, and only the *set* says so. The comparison is
    therefore over the absent-family tuples, never over their lengths.

    A group carrying at most one conviction is trivially comparable —
    there is nothing to place it against — and so is one where every
    conviction covers the same families.
    """

    coverages = {
        coverage for coverage in map(coverage_of, workspaces) if coverage is not None
    }

    return len(coverages) <= 1


def rank_by_conviction(
    workspaces: Sequence[ExecutiveWorkspace],
) -> tuple[ExecutiveWorkspace, ...]:
    """
    Order evaluations by the conviction behind them, highest first.

    Ranking expresses priority, never certainty, and it never drops an
    evaluation: everything judged is reported.

    **Where coverage differs, nothing is ordered by conviction.** The
    evaluations come back by symbol instead — an order that is obviously
    not a judgment, and stable, so a page does not reshuffle between two
    reads of one record. Callers ask `comparable()` before printing a
    rank number and print none where it is False.
    """

    if not comparable(workspaces):
        return tuple(sorted(workspaces, key=lambda item: item.symbol))

    return tuple(
        sorted(
            workspaces,
            key=conviction_of,
            reverse=True,
        )
    )
