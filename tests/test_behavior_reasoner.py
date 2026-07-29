from app.application.brain.reasoning.behavior_reasoner import BehaviorReasoner


def test_behavior_reasoner_exists() -> None:
    assert BehaviorReasoner() is not None
