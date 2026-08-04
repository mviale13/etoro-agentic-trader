from app.application.brain.reasoning.behavior_analyst import BehaviorAnalyst


def test_behavior_analyst_exists() -> None:
    assert BehaviorAnalyst() is not None
