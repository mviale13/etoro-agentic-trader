from rich.console import Console

from app.domain.recommendation import Recommendation

console = Console()


class ExplainRenderer:
    @staticmethod
    def render(recommendation: Recommendation) -> None:
        decision = recommendation.decision

        console.print()
        console.print("[bold cyan]MOVRvest[/bold cyan]")
        console.print("[bold]Explain[/bold]")
        console.print("══════════════════════════════")
        console.print()

        console.print(f"[bold]{recommendation.symbol}[/bold]")
        console.print()

        for opinion in decision.opinions:
            color = {
                "BUY": "green",
                "HOLD": "yellow",
                "SELL": "red",
            }.get(opinion.vote, "white")

            console.print(
                f"{opinion.member:<18}"
                f"[{color}]{opinion.vote:<6}[/{color}]"
                f"{opinion.confidence:>4}%"
            )
            console.print(f"  {opinion.rationale}")
            console.print()

        console.print("──────────────────────────────")
        console.print()
        console.print("[bold]Recommendation[/bold]")

        recommendation_color = {
            "BUY": "green",
            "HOLD": "yellow",
            "SELL": "red",
        }.get(decision.recommendation, "white")

        console.print(
            f"[bold {recommendation_color}]"
            f"{decision.recommendation}"
            f"[/bold {recommendation_color}]"
        )

        console.print()
        console.print("[bold]Confidence[/bold]")
        console.print(f"{decision.confidence}%")
        console.print()
