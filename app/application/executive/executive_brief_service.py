"""Executive brief generation service."""

from __future__ import annotations

from app.application.executive.models.executive_brief import ExecutiveBrief
from app.application.executive.models.executive_recommendation import (
    ExecutiveRecommendation,
    RecommendationAction,
)


class ExecutiveBriefService:
    """Transforms an executive recommendation into investor-facing language."""

    _HEADLINES: dict[RecommendationAction, str] = {
        RecommendationAction.BUY: "Build a new position.",
        RecommendationAction.ADD: "Increase exposure.",
        RecommendationAction.HOLD: "Maintain the current position.",
        RecommendationAction.REDUCE: "Reduce exposure.",
        RecommendationAction.SELL: "Exit the position.",
    }

    def build(
        self,
        recommendation: ExecutiveRecommendation,
    ) -> ExecutiveBrief:
        """Create a concise and explainable executive brief."""

        return ExecutiveBrief(
            title="Executive Recommendation",
            headline=self._HEADLINES[recommendation.action],
            narrative=self._build_narrative(recommendation),
            confidence_label=self._confidence_label(
                recommendation.confidence,
            ),
            confidence=recommendation.confidence,
            priority=recommendation.priority,
            opportunities=recommendation.opportunities,
            risks=recommendation.risks,
        )

    def _build_narrative(
        self,
        recommendation: ExecutiveRecommendation,
    ) -> str:
        action_text = recommendation.action.value.replace("_", " ").lower()

        rationale = " ".join(recommendation.rationale).strip()

        if not rationale:
            rationale = recommendation.summary.strip()

        return (
            f"The Executive Committee recommends {action_text}. {rationale}"
        ).strip()

    @staticmethod
    def _confidence_label(confidence: float) -> str:
        if confidence >= 0.80:
            return "High"

        if confidence >= 0.55:
            return "Moderate"

        return "Low"
