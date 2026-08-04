import pytest

from app.domain.research_plan import AnalystKey
from app.services.analyst_registry import AnalystRegistry


class FakeGrowthAnalyst:
    pass


class FakeCashFlowAnalyst:
    pass


def test_registry_returns_registered_analyst() -> None:
    growth_analyst = FakeGrowthAnalyst()

    registry = AnalystRegistry(
        analysts={
            AnalystKey.GROWTH: growth_analyst,
        }
    )

    resolved = registry.get(AnalystKey.GROWTH)

    assert resolved is growth_analyst


def test_registry_resolves_different_analysts_by_key() -> None:
    growth_analyst = FakeGrowthAnalyst()
    cash_flow_analyst = FakeCashFlowAnalyst()

    registry = AnalystRegistry(
        analysts={
            AnalystKey.GROWTH: growth_analyst,
            AnalystKey.CASH_FLOW: cash_flow_analyst,
        }
    )

    assert registry.get(AnalystKey.GROWTH) is growth_analyst
    assert registry.get(AnalystKey.CASH_FLOW) is cash_flow_analyst


def test_registry_raises_clear_error_for_unregistered_analyst() -> None:
    registry = AnalystRegistry(analysts={})

    with pytest.raises(
        KeyError,
        match="No analyst registered for key: growth",
    ):
        registry.get(AnalystKey.GROWTH)
