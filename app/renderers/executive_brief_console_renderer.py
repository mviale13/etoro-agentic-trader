"""Render an ExecutiveBrief on the command line."""

from __future__ import annotations

from rich.console import Console

from app.domain.executive.executive_brief import ExecutiveBrief

console = Console()


class ExecutiveBriefConsoleRenderer:
    """
    Present an executive brief.

    This renderer never reasons and never decides.
    """

    @staticmethod
    def render(
        brief: ExecutiveBrief,
    ) -> None:
        console.print()
        console.print("[bold cyan]MOVRvest[/bold cyan]")
        console.print("[bold]Executive Brief[/bold]")
        console.print("══════════════════════════════════════")
        console.print()

        console.print(f"[bold]{brief.headline}[/bold]")
        console.print()

        console.print("[bold]Why?[/bold]")
        console.print(brief.summary)
        console.print()

        # Not the CIO's conviction in its decision — that number lives on
        # the decision and does not reach this brief. This is how far the
        # committees agreed, which is worth reading on a RECOMMEND but is
        # not the same claim.
        console.print(
            "Committee agreement: "
            f"{ExecutiveBriefConsoleRenderer._percent(brief.confidence)}"
        )
        console.print(
            "Portfolio health: "
            f"{ExecutiveBriefConsoleRenderer._percent(brief.portfolio_health)}"
        )
        console.print()

        for case in brief.investment_cases:
            console.print("──────────────────────────────────────")
            console.print()
            console.print(f"[bold]{case.symbol}[/bold] — {case.recommendation}")
            console.print()

            if case.evidence_weighed:
                console.print("[bold]Evidence weighed[/bold]")

                for finding in case.evidence_weighed:
                    console.print(f"• {finding}")

                console.print()

            # Named for what they describe. "Healthy liquidity" is a fact
            # about the investor's account, and printing it as a strength
            # under a ticker attributes it to the security instead.
            if case.strengths:
                console.print("[bold]Portfolio and market strengths[/bold]")

                for strength in case.strengths:
                    console.print(f"• {strength}")

                console.print()

            if case.risks:
                console.print("[bold]Portfolio and market risks[/bold]")

                for risk in case.risks:
                    console.print(f"• {risk}")

                console.print()

            console.print(f"Expected holding period: {case.expected_holding_period}")

            if case.previous_decisions:
                console.print(f"Previously: {case.previous_decisions}")

            console.print()

        if brief.priorities:
            console.print("──────────────────────────────────────")
            console.print()
            console.print("[bold cyan]What should I do?[/bold cyan]")

            for priority in brief.priorities:
                console.print(f"• {priority.title}: {priority.description}")

            console.print()

    @staticmethod
    def _percent(
        value: float,
    ) -> str:
        return f"{round(value * 100)}%"
