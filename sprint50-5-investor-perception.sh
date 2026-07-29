#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "MOVRvest — Sprint 50.5: Extract InvestorPerception"
echo "============================================================"

PERCEPTION_FILE="app/application/brain/perception/investor_perception.py"
BUILDER_FILE="app/services/brain_context_builder.py"
TEST_FILE="tests/test_investor_perception.py"

mkdir -p app/application/brain/perception

cat > "$PERCEPTION_FILE" <<'PY'
"""Investor perception component for the MOVRvest investment brain."""

from dataclasses import dataclass

from app.domain.investor_dna import InvestorDNA
from app.domain.observation import Observation
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.repositories.event_repository import EventRepository
from app.services.investor_dna_service import InvestorDNAService
from app.services.investor_observation_service import InvestorObservationService
from app.services.memory_service import MemoryService
from app.services.pattern_engine import PatternEngine
from app.services.signal_service import SignalService


@dataclass(frozen=True)
class InvestorPerceptionResult:
    """Investor intelligence produced during the perception stage."""

    observation: Observation
    investor_dna: InvestorDNA


class InvestorPerception:
    """Interpret portfolio signals and historical investor behaviour."""

    def __init__(
        self,
        repository: EventRepository,
        signal_service: SignalService | None = None,
        observation_service: InvestorObservationService | None = None,
        memory_service: MemoryService | None = None,
        pattern_engine: PatternEngine | None = None,
        investor_dna_service: InvestorDNAService | None = None,
    ) -> None:
        self._signal_service = signal_service or SignalService()
        self._observation_service = (
            observation_service or InvestorObservationService()
        )
        self._memory_service = memory_service or MemoryService(repository)
        self._pattern_engine = pattern_engine or PatternEngine()
        self._investor_dna_service = (
            investor_dna_service or InvestorDNAService()
        )

    def execute(
        self,
        portfolio: PortfolioSnapshot,
        previous_portfolio: PortfolioSnapshot | None = None,
    ) -> InvestorPerceptionResult:
        """Build the current observation and investor DNA."""

        signals = self._signal_service.analyze(
            current=portfolio,
            previous=previous_portfolio,
        )

        observation = self._observation_service.observe(signals)

        memories = self._memory_service.history()
        patterns = self._pattern_engine.analyze(memories)
        investor_dna = self._investor_dna_service.analyze(patterns)

        return InvestorPerceptionResult(
            observation=observation,
            investor_dna=investor_dna,
        )
PY

python - <<'PY'
from pathlib import Path

path = Path("app/services/brain_context_builder.py")
content = path.read_text()

content = content.replace(
    """from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
""",
    """from app.application.brain.perception.investor_perception import (
    InvestorPerception,
)
from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
""",
)

content = content.replace(
    """from app.services.investor_dna_service import (
    InvestorDNAService,
)
from app.services.investor_observation_service import (
    InvestorObservationService,
)
""",
    "",
)

content = content.replace(
    """from app.services.memory_service import MemoryService
from app.services.pattern_engine import PatternEngine
from app.services.signal_service import SignalService
""",
    "",
)

old_block = """        signals = SignalService().analyze(
            current=portfolio,
            previous=None,
        )

        observation = InvestorObservationService().observe(
            signals,
        )

        memories = MemoryService(
            repository,
        ).history()

        patterns = PatternEngine().analyze(
            memories,
        )

        investor_dna = InvestorDNAService().analyze(
            patterns,
        )
"""

new_block = """        investor = InvestorPerception(
            repository=repository,
        ).execute(
            portfolio=portfolio,
        )
"""

if old_block not in content:
    raise SystemExit(
        "Expected investor-perception block was not found in BrainContextBuilder."
    )

content = content.replace(old_block, new_block)

content = content.replace(
    """            observation=observation,
            investor_dna=investor_dna,
""",
    """            observation=investor.observation,
            investor_dna=investor.investor_dna,
""",
)

path.write_text(content)
PY

cat > "$TEST_FILE" <<'PY'
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
PY

ruff check --fix \
  "$PERCEPTION_FILE" \
  "$BUILDER_FILE" \
  "$TEST_FILE"

ruff format \
  "$PERCEPTION_FILE" \
  "$BUILDER_FILE" \
  "$TEST_FILE"

pytest "$TEST_FILE"
ruff check .
ruff format --check .
mypy app
pytest

echo
echo "============================================================"
echo "Sprint 50.5 InvestorPerception extraction complete"
echo "============================================================"
echo
echo "Suggested commit:"
echo "git add \\"
echo "  $PERCEPTION_FILE \\"
echo "  $BUILDER_FILE \\"
echo "  $TEST_FILE"
echo
echo 'git commit -m "refactor: extract investor perception"'
