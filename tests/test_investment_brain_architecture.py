"""Architecture tests for the InvestmentBrain migration."""

import inspect

from app.application.brain import InvestmentBrain
from app.services.brain_service import BrainService


def test_legacy_brain_service_is_investment_brain() -> None:
    assert BrainService is InvestmentBrain


def test_investment_brain_is_defined_in_application_layer() -> None:
    assert InvestmentBrain.__module__ == "app.application.brain.investment_brain"


def test_investment_brain_analyze_is_async() -> None:
    assert inspect.iscoroutinefunction(InvestmentBrain.analyze)


def test_legacy_build_verb_remains_async() -> None:
    assert inspect.iscoroutinefunction(InvestmentBrain.build)
