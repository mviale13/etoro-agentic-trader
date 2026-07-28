from datetime import UTC, datetime

from app.domain.committee_vote import CommitteeVote
from app.domain.investment_dossier import InvestmentDossier


class InvestmentCaseBuilder:
    def build(
        self,
        *,
        symbol: str,
        name: str,
        executive_score: int,
        committee_votes: tuple[CommitteeVote, ...],
    ) -> InvestmentDossier:
        return InvestmentDossier(
            symbol=symbol,
            name=name,
            executive_score=executive_score,
            executive_summary=("Investment case prepared by the Artificial CIO."),
            committee_votes=committee_votes,
            market_summary="Market analysis pending.",
            portfolio_impact="Portfolio impact pending.",
            risk_summary="Risk assessment pending.",
            suggested_allocation=("Allocation guidance pending."),
            evidence=(),
            generated_at=datetime.now(UTC),
        )
