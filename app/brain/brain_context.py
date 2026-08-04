from collections.abc import Mapping
from dataclasses import dataclass, field

from app.cio.investment_case import InvestmentCase
from app.domain.decision_history import DecisionHistory
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.research_candidate import ResearchCandidate


@dataclass(frozen=True, slots=True)
class BrainContext:
    """
    Complete working memory available to MOVRvest reasoning components.

    BrainContext contains facts and previously produced conclusions only.
    It must not contain services, repositories, providers, or API clients.
    """

    portfolio: PortfolioSnapshot
    market: MarketSnapshot
    investment_policy: InvestmentPolicy

    investment_cases: Mapping[str, InvestmentCase] = field(
        default_factory=dict,
    )
    evidence: Mapping[str, tuple[object, ...]] = field(
        default_factory=dict,
    )
    committee_opinions: Mapping[str, tuple[object, ...]] = field(
        default_factory=dict,
    )
    memory: Mapping[str, object] = field(
        default_factory=dict,
    )
    #: Securities the investor watches but does not hold.
    candidates: tuple[ResearchCandidate, ...] = ()
    #: Candidate symbols this cycle actually spent a fundamentals request
    #: on. A fact about what happened, recorded by the component that did
    #: it — the funnel's "reviewed" is read from here, never reconstructed
    #: by arithmetic on the budget.
    attempted_candidates: tuple[str, ...] = ()
    #: What the Artificial CIO decided before, keyed by symbol.
    decision_history: Mapping[str, DecisionHistory] = field(
        default_factory=dict,
    )
    alerts: tuple[str, ...] = ()

    def investment_case(self, symbol: str) -> InvestmentCase | None:
        """Return the investment case for a normalized market symbol."""

        return self.investment_cases.get(symbol.upper().strip())

    def evidence_for(self, symbol: str) -> tuple[object, ...]:
        """Return all available evidence for a normalized market symbol."""

        return self.evidence.get(symbol.upper().strip(), ())

    def opinions_for(self, symbol: str) -> tuple[object, ...]:
        """Return all committee opinions for a normalized market symbol."""

        return self.committee_opinions.get(symbol.upper().strip(), ())

    def decision_history_for(self, symbol: str) -> DecisionHistory:
        """
        Return every decision recorded for a normalized market symbol.

        A symbol the CIO has never judged returns an empty history, which
        reports the absence rather than implying a decision was made.
        """

        normalized = symbol.upper().strip()

        return self.decision_history.get(
            normalized,
            DecisionHistory(symbol=normalized),
        )
