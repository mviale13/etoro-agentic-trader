from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)


def test_policy_perception_is_in_perception_layer() -> None:
    assert PolicyPerception.__module__ == (
        "app.application.brain.perception.policy_perception"
    )
