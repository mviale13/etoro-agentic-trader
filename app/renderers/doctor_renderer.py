from rich.console import Console

from app.domain.portfolio_health import PortfolioHealth

console = Console()


class DoctorRenderer:
    @staticmethod
    def render(health: PortfolioHealth) -> None:
        console.print()
        console.print("[bold cyan]MOVRvest[/bold cyan]")
        console.print("[bold]Portfolio Doctor[/bold]")
        console.print("══════════════════════════════════════")
        console.print()

        score_color = DoctorRenderer._score_color(
            health.overall_score,
        )

        console.print("[bold]Overall Health[/bold]")
        console.print(
            f"[bold {score_color}]{health.overall_score} / 100[/bold {score_color}]"
        )
        console.print()

        for check in health.checks:
            icon, color = DoctorRenderer._status_style(
                check.status,
            )

            console.print("──────────────────────────────────────")
            console.print()
            console.print(f"[bold {color}]{icon} {check.name}[/bold {color}]")
            console.print(f"Score: {check.score} / 100")
            console.print(check.message)
            console.print()

        console.print("──────────────────────────────────────")
        console.print()
        console.print("[bold]Next Action[/bold]")
        console.print(f"[bold cyan]{health.recommendation}[/bold cyan]")
        console.print()

    @staticmethod
    def _score_color(score: int) -> str:
        if score >= 85:
            return "green"

        if score >= 70:
            return "yellow"

        return "red"

    @staticmethod
    def _status_style(
        status: str,
    ) -> tuple[str, str]:
        styles = {
            "HEALTHY": ("✓", "green"),
            "SUPPORTIVE": ("✓", "green"),
            "ACTION": ("→", "cyan"),
            "CAUTION": ("!", "yellow"),
            "NEUTRAL": ("•", "yellow"),
            "WARNING": ("⚠", "red"),
            "UNKNOWN": ("?", "dim"),
        }

        return styles.get(
            status,
            ("•", "white"),
        )
