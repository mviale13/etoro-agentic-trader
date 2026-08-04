"""Architecture tests for the MOVRvest learning-layer migration."""

from app.application.learning import LearningEngine
from app.services.learning_service import LearningService


def test_legacy_learning_service_is_learning_engine() -> None:
    assert LearningService is LearningEngine


def test_learning_engine_is_defined_in_application_layer() -> None:
    assert LearningEngine.__module__ == "app.application.learning.learning_engine"


def test_learning_engine_exposes_explicit_learning_entry_point() -> None:
    assert callable(LearningEngine.learn)


def test_legacy_insights_entry_point_remains_available() -> None:
    assert callable(LearningEngine.insights)
