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
        self._observation_service = observation_service or InvestorObservationService()
        self._memory_service = memory_service or MemoryService(repository)
        self._pattern_engine = pattern_engine or PatternEngine()
        self._investor_dna_service = investor_dna_service or InvestorDNAService()

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
