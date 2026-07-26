from rich.console import Console

from app.domain.recommendation import Recommendation

console = Console()


class WatchlistRenderer:
    @staticmethod
    def render(
        recommendations: list[Recommendation],
    ) -> None:
        console.print()

        console.print("[bold cyan]MOVRvest[/bold cyan]")
        console.print("[bold]Watchlist[/bold]")
        console.print("══════════════════════════════")
        console.print()

        for recommendation in recommendations:
            decision = recommendation.decision

            color = {
                "BUY": "green",
                "HOLD": "yellow",
                "SELL": "red",
            }.get(decision.recommendation, "white")

            console.print(
                f"{recommendation.symbol:<8}"
                f"[{color}]"
                f"{decision.recommendation:<5}"
                f"[/{color}]   "
                f"{decision.confidence}%"
            )
