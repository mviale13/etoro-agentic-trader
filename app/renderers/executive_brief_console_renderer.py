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
            + (
                "not measured"
                if brief.confidence is None
                else ExecutiveBriefConsoleRenderer._percent(brief.confidence)
            )
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

            # The Artificial CIO's own conviction in this decision. The
            # brief carried only the committees' agreement, so a RECOMMEND
            # printed a number that answered a different question.
            console.print(
                "Conviction: "
                f"{ExecutiveBriefConsoleRenderer._percent(case.conviction / 100)}"
            )
            console.print()

            # The security's own case first, then the record it was drawn
            # from, then the account and market it sits in. Each section
            # says whose it is: "Healthy liquidity" is a fact about the
            # investor's cash, and under a bare heading beneath a ticker it
            # read as a fact about the security.
            ExecutiveBriefConsoleRenderer._section("Strengths", case.strengths)
            ExecutiveBriefConsoleRenderer._section("Risks", case.risks)
            ExecutiveBriefConsoleRenderer._section(
                "Evidence weighed",
                case.evidence_weighed,
            )
            ExecutiveBriefConsoleRenderer._section(
                "Portfolio and market strengths",
                case.context_strengths,
            )
            ExecutiveBriefConsoleRenderer._section(
                "Portfolio and market risks",
                case.context_risks,
            )

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
    def _section(
        title: str,
        lines: tuple[str, ...],
    ) -> None:
        if not lines:
            return

        console.print(f"[bold]{title}[/bold]")

        for line in lines:
            console.print(f"• {line}")

        console.print()

    @staticmethod
    def _percent(
        value: float,
    ) -> str:
        return f"{round(value * 100)}%"
