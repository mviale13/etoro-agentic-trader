"""Report how far the grounded selector reaches over the book today.

The measurement surface. It prints the population, the three selector
outcomes kept apart, the knowledge widths, which grounded playbooks
actually serve, then the part the roadmap is decided from: every
blocked company with its one blocking claim, the distribution of
blockers, and the same distribution ranked as recommendations — most
companies unlocked per claim established first.
"""

from __future__ import annotations

from app.domain.knowledge_consensus import QUORUM
from app.domain.playbook_coverage import (
    CoverageFunnel,
    CoverageOrigin,
    CoverageReport,
)
from app.services.playbook_coverage_service import PlaybookCoverageService


class PlaybookCoverageCommand:
    async def run(self) -> int:
        _render(await PlaybookCoverageService().report())

        return 0


def _leader(label: str, count: int, width: int = 42) -> str:
    dots = "." * max(width - len(label), 3)

    return f"  {label} {dots} {count}"


def _funnel(title: str, funnel: CoverageFunnel) -> None:
    """One origin's KPI: each row a strictly narrower capability, so
    the first gap from the top is the cheapest one to close."""

    print(f"  {title}:")

    def row(label: str, count: int) -> None:
        share = f"  ({count / funnel.companies:.0%})" if funnel.companies else ""
        print(_leader(label, count) + share)

    print(_leader("companies", funnel.companies))
    row("read (width ≥ 1)", funnel.read)
    row("understanding decided", funnel.decided)
    row("playbook mapped", funnel.mapped)
    row("quorate (authoritative)", funnel.quorate)

    if funnel.unresolved:
        print(_leader("identity unresolved", funnel.unresolved))

    if funnel.out_of_scope:
        print(_leader("out of scope (files nothing)", funnel.out_of_scope))


def _render(report: CoverageReport) -> None:
    print("grounded playbook coverage — the book as this platform knows it today")
    print()
    print(f"  {report.total} securities, portfolio and watchlists together")
    print()

    print("investor-visible understanding — the KPI, portfolio first:")
    _funnel("portfolio", report.funnel(CoverageOrigin.PORTFOLIO))
    _funnel("watchlist", report.funnel(CoverageOrigin.WATCHLIST))
    print()

    print("selector outcomes:")
    print(_leader("grounded (authoritative)", len(report.grounded)))
    print(_leader("industry fallback", len(report.fallbacks)))
    print(_leader("unclassified", len(report.unclassified)))
    print()

    print("business understanding:")
    print(_leader("quorate", report.quorate))
    print(_leader("below quorum", report.below_quorum))
    print(_leader("never read", report.unread))
    print()

    if report.grounded_kinds:
        print("grounded playbooks serving:")

        for kind, count in report.grounded_kinds:
            print(_leader(kind.value, count))

        print()

    print("securities:")

    for security in report.securities:
        served = f"{security.outcome.value}: {security.playbook.value}"
        print(
            f"  {security.symbol:<10} {security.width}/{QUORUM}  "
            f"{served}  [{security.origin.value}]"
        )

        if security.note is not None:
            print(f"             note: {security.note}")

    print()

    if not report.blocked:
        print("nothing is blocked — every security selects a grounded playbook.")
        return

    print("what blocks the rest — one claim each:")

    for security in report.blocked:
        print(f"  {security.symbol:<10} {security.blocker}")

        if security.blocking_claim is not None:
            print(f"             unlocked by: {security.blocking_claim}")

    print()

    print("blocker distribution:")

    for blocker, count in report.blocker_distribution:
        print(_leader(blocker.value, count))

    print()

    print("recommendations, ranked by companies unlocked:")

    for rank, (blocker, count) in enumerate(report.blocker_distribution, start=1):
        plural = "company" if count == 1 else "companies"
        print(f"  {rank}. {blocker.value} — {count} {plural}")
        print(f"     {blocker.unlocked_by}")


async def run() -> int:
    return await PlaybookCoverageCommand().run()
