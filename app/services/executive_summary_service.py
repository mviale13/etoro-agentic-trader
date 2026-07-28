from app.domain.executive_brief import ExecutiveBrief
from app.domain.insight import Insight


class ExecutiveSummaryService:
    def build(
        self,
        insights: list[Insight],
    ) -> ExecutiveBrief:
        if not insights:
            return ExecutiveBrief(
                headline="No urgent decision today",
                why=(
                    "MOVRvest found no significant events "
                    "requiring immediate attention."
                ),
                action="Continue monitoring your portfolio.",
                confidence="medium",
            )

        insight = insights[0]

        return ExecutiveBrief(
            headline=insight.title,
            why=insight.message,
            action=(insight.recommended_action or "Review the available evidence."),
            confidence=insight.confidence,
        )

    def summarize(
        self,
        insights: list[Insight],
    ) -> str:
        brief = self.build(insights)

        return (
            f"{brief.headline}\n\n"
            f"Why it matters:\n"
            f"{brief.why}\n\n"
            f"Recommended action:\n"
            f"{brief.action}\n\n"
            f"Confidence: {brief.confidence.upper()}"
        )
