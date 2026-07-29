"""Tests for the investor perception component."""

from typing import cast

from app.application.brain.perception.investor_perception import (
    InvestorPerception,
    InvestorPerceptionResult,
)
from app.domain.investor_dna import InvestorDNA
from app.domain.memory_event import MemoryEvent
from app.domain.observation import Observation
from app.domain.pattern import Pattern
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.signal import Signal
from app.repositories.event_repository import EventRepository
from app.services.investor_dna_service import InvestorDNAService
from app.services.investor_observation_service import InvestorObservationService
from app.services.memory_service import MemoryService
from app.services.pattern_engine import PatternEngine
from app.services.signal_service import SignalService


def test_investor_perception_is_defined_in_perception_layer() -> None:
    assert InvestorPerception.__module__ == (
        "app.application.brain.perception.investor_perception"
    )


def test_investor_perception_result_is_immutable() -> None:
    assert InvestorPerceptionResult.__dataclass_params__.frozen is True


def test_investor_perception_executes_services_in_order() -> None:
    calls: list[str] = []

    portfolio = cast(PortfolioSnapshot, object())
    signals = cast(list[Signal], [])
    observation = cast(Observation, object())
    memories = cast(list[MemoryEvent], [])
    patterns = cast(list[Pattern], [])
    investor_dna = cast(InvestorDNA, object())

    class SignalServiceStub:
        def analyze(
            self,
            current: PortfolioSnapshot,
            previous: PortfolioSnapshot | None,
        ) -> list[Signal]:
            calls.append("signals")
            assert current is portfolio
            assert previous is None
            return signals

    class ObservationServiceStub:
        def observe(self, received_signals: list[Signal]) -> Observation:
            calls.append("observation")
            assert received_signals is signals
            return observation

    class MemoryServiceStub:
        def history(self) -> list[MemoryEvent]:
            calls.append("memory")
            return memories

    class PatternEngineStub:
        def analyze(
            self,
            received_memories: list[MemoryEvent],
        ) -> list[Pattern]:
            calls.append("patterns")
            assert received_memories is memories
            return patterns

    class InvestorDNAServiceStub:
        def analyze(
            self,
            received_patterns: list[Pattern],
        ) -> InvestorDNA:
            calls.append("investor_dna")
            assert received_patterns is patterns
            return investor_dna

    perception = InvestorPerception(
        repository=cast(EventRepository, object()),
        signal_service=cast(SignalService, SignalServiceStub()),
        observation_service=cast(
            InvestorObservationService,
            ObservationServiceStub(),
        ),
        memory_service=cast(MemoryService, MemoryServiceStub()),
        pattern_engine=cast(PatternEngine, PatternEngineStub()),
        investor_dna_service=cast(
            InvestorDNAService,
            InvestorDNAServiceStub(),
        ),
    )

    result = perception.execute(portfolio)

    assert result.observation is observation
    assert result.investor_dna is investor_dna
    assert calls == [
        "signals",
        "observation",
        "memory",
        "patterns",
        "investor_dna",
    ]


def test_investor_perception_forwards_previous_portfolio() -> None:
    current = cast(PortfolioSnapshot, object())
    previous = cast(PortfolioSnapshot, object())

    observation = cast(Observation, object())
    investor_dna = cast(InvestorDNA, object())

    class SignalServiceStub:
        def analyze(
            self,
            current: PortfolioSnapshot,
            previous: PortfolioSnapshot | None,
        ) -> list[Signal]:
            assert current is current_portfolio
            assert previous is previous_portfolio
            return []

    class ObservationServiceStub:
        def observe(self, signals: list[Signal]) -> Observation:
            assert signals == []
            return observation

    class MemoryServiceStub:
        def history(self) -> list[MemoryEvent]:
            return []

    class PatternEngineStub:
        def analyze(self, memories: list[MemoryEvent]) -> list[Pattern]:
            assert memories == []
            return []

    class InvestorDNAServiceStub:
        def analyze(self, patterns: list[Pattern]) -> InvestorDNA:
            assert patterns == []
            return investor_dna

    current_portfolio = current
    previous_portfolio = previous

    perception = InvestorPerception(
        repository=cast(EventRepository, object()),
        signal_service=cast(SignalService, SignalServiceStub()),
        observation_service=cast(
            InvestorObservationService,
            ObservationServiceStub(),
        ),
        memory_service=cast(MemoryService, MemoryServiceStub()),
        pattern_engine=cast(PatternEngine, PatternEngineStub()),
        investor_dna_service=cast(
            InvestorDNAService,
            InvestorDNAServiceStub(),
        ),
    )

    result = perception.execute(
        portfolio=current,
        previous_portfolio=previous,
    )

    assert result.observation is observation
    assert result.investor_dna is investor_dna
