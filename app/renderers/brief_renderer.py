from rich.console import Console

from app.domain.brief_snapshot import BriefSnapshot

console = Console()


class BriefRenderer:
    @staticmethod
    def render(snapshot: BriefSnapshot) -> None:
        recommendation = snapshot.recommendation
        decision = recommendation.decision
        health = snapshot.health

        console.print()
        console.print("[bold cyan]MOVRvest[/bold cyan]")
        console.print("[bold]Morning Brief[/bold]")
        console.print("══════════════════════════════════════")
        console.print()

        console.print(f"[bold]{snapshot.greeting}[/bold]")
        console.print()

        console.print("[bold]Portfolio Health[/bold]")
        console.print(
            f"{BriefRenderer._health_icon(health.overall_score)} "
            f"{health.overall_score} / 100"
        )
        console.print()

        console.print("[bold]Summary[/bold]")
        console.print(snapshot.summary)
        console.print()

        console.print("──────────────────────────────────────")
        console.print()
        console.print("[bold]What Changed?[/bold]")

        for change in snapshot.changes:
            console.print(f"• {change}")

        console.print()
        console.print("──────────────────────────────────────")
        console.print()
        console.print("[bold]Today's Focus[/bold]")
        console.print(f"[bold]{recommendation.symbol}[/bold]")

        decision_color = {
            "BUY": "green",
            "HOLD": "yellow",
            "SELL": "red",
        }.get(decision.recommendation, "white")

        console.print(
            f"[bold {decision_color}]{decision.recommendation}[/bold {decision_color}]"
        )
        console.print(f"Confidence: {decision.confidence}%")
        console.print()

        console.print("[bold]Why?[/bold]")

        for opinion in decision.opinions:
            console.print(f"• {opinion.member}: {opinion.vote} — {opinion.rationale}")

        console.print()
        console.print("──────────────────────────────────────")
        console.print()
        console.print("[bold cyan]Next Action[/bold cyan]")
        console.print(snapshot.next_action)
        console.print()

    @staticmethod
    def _health_icon(score: int) -> str:
        if score >= 85:
            return "🟢"

        if score >= 70:
            return "🟡"

        return "🔴"
