from app.application.executive.executive_brief_service import (
    ExecutiveBriefService,
)
from app.application.executive.models.executive_recommendation import (
    ExecutiveRecommendation,
    RecommendationAction,
)


def make_recommendation(
    *,
    action: RecommendationAction = RecommendationAction.ADD,
    confidence: float = 0.82,
) -> ExecutiveRecommendation:
    return ExecutiveRecommendation(
        action=action,
        confidence=confidence,
        priority=0.78,
        summary="The opportunity is attractive.",
        rationale=(
            "Market momentum is positive.",
            "Portfolio risk remains controlled.",
        ),
        opportunities=("Positive market momentum",),
        risks=("Volatility may increase",),
        evidence=(),
    )


def test_builds_investor_facing_executive_brief() -> None:
    service = ExecutiveBriefService()

    brief = service.build(make_recommendation())

    assert brief.title == "Executive Recommendation"
    assert brief.headline == "Increase exposure."
    assert brief.confidence_label == "High"
    assert brief.confidence == 0.82
    assert brief.priority == 0.78
    assert brief.opportunities == ("Positive market momentum",)
    assert brief.risks == ("Volatility may increase",)
    assert "Market momentum is positive." in brief.narrative


def test_maps_hold_action_to_hold_headline() -> None:
    service = ExecutiveBriefService()

    brief = service.build(
        make_recommendation(action=RecommendationAction.HOLD),
    )

    assert brief.headline == "Maintain the current position."


def test_labels_moderate_confidence() -> None:
    service = ExecutiveBriefService()

    brief = service.build(make_recommendation(confidence=0.65))

    assert brief.confidence_label == "Moderate"


def test_labels_low_confidence() -> None:
    service = ExecutiveBriefService()

    brief = service.build(make_recommendation(confidence=0.40))

    assert brief.confidence_label == "Low"
