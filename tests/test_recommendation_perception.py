from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)


def test_recommendation_perception_is_in_perception_layer():
    assert RecommendationPerception.__module__ == (
        "app.application.brain.perception.recommendation_perception"
    )
