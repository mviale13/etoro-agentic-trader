from collections.abc import Mapping
from dataclasses import dataclass, field

from app.brain.brain import Brain
from app.brain.brain_context import BrainContext
from app.cio.investment_case import InvestmentCase
from app.domain.decision_history import DecisionHistory
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.research_candidate import ResearchCandidate


@dataclass(slots=True)
class BrainBuilder:
    """
    Assemble an immutable Brain from resolved investment facts.

    The builder performs no data retrieval, reasoning, filtering,
    committee execution, or investment decision-making.
    """

    portfolio: PortfolioSnapshot
    market: MarketSnapshot
    investment_policy: InvestmentPolicy

    investment_cases: Mapping[str, InvestmentCase] = field(default_factory=dict)
    evidence: Mapping[str, tuple[object, ...]] = field(default_factory=dict)
    committee_opinions: Mapping[str, tuple[object, ...]] = field(default_factory=dict)
    memory: Mapping[str, object] = field(default_factory=dict)
    candidates: tuple[ResearchCandidate, ...] = ()
    decision_history: Mapping[str, DecisionHistory] = field(default_factory=dict)
    alerts: tuple[str, ...] = ()

    def build(self) -> Brain:
        """Create a Brain containing one complete decision-cycle context."""

        context = BrainContext(
            portfolio=self.portfolio,
            market=self.market,
            investment_policy=self.investment_policy,
            investment_cases=dict(self.investment_cases),
            evidence={symbol: tuple(items) for symbol, items in self.evidence.items()},
            committee_opinions={
                symbol: tuple(opinions)
                for symbol, opinions in self.committee_opinions.items()
            },
            memory=dict(self.memory),
            candidates=tuple(self.candidates),
            decision_history=dict(self.decision_history),
            alerts=tuple(self.alerts),
        )

        return Brain(context=context)
