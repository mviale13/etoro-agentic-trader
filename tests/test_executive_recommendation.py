from app.application.executive.models.executive_recommendation import (
    ExecutiveRecommendation,
    RecommendationAction,
)


def test_executive_recommendation_exists() -> None:
    recommendation = ExecutiveRecommendation(
        action=RecommendationAction.HOLD,
        confidence=0.80,
        priority=0.60,
        summary="Maintain current allocation.",
    )

    assert recommendation.action is RecommendationAction.HOLD
