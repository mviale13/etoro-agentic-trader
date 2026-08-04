from app.domain.insight import Insight


class InsightRenderer:
    def render(
        self,
        insights: list[Insight],
    ) -> str:
        if not insights:
            return (
                "No significant developments today. Continue monitoring the portfolio."
            )

        lines: list[str] = [
            "Executive Brief",
            "",
        ]

        for insight in insights:
            lines.append(f"• {insight.title}")
            lines.append(f"  {insight.message}")

            if insight.evidence:
                lines.append("  Evidence:")

                for evidence in insight.evidence:
                    lines.append(f"    - {evidence}")

            lines.append("")

        return "\n".join(lines).strip()
