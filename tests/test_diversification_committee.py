from datetime import UTC, datetime

from app.committee.diversification import DiversificationCommittee
from app.domain.committee_context import CommitteeContext
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


def build_context(position_pct: float):
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=70,
            etfs=20,
            crypto=0,
            cash=10,
            unclassified=0,
        ),
        total_value=100000,
        positions=8,
        largest_position=None,
        largest_position_pct=position_pct,
        risk_flags=(),
    )

    policy = InvestmentPolicy(
        risk_profile="moderate",
        target=AllocationTarget(
            stocks=60,
            etfs=20,
            crypto=10,
            cash=10,
        ),
        constraints=InvestmentConstraints(
            max_single_position=15,
            max_crypto=20,
            rebalance_threshold=5,
        ),
    )

    intelligence = MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="positive",
            volatility="low",
            summary="Healthy",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=70,
            label="Greed",
            source="Alternative.me",
        ),
        outlook="BULLISH",
        confidence=85,
        summary="Healthy market.",
    )

    return CommitteeContext(
        intelligence=intelligence,
        portfolio=portfolio,
        policy=policy,
    )


def test_overweight_position_votes_hold():
    opinion = DiversificationCommittee().evaluate(build_context(22))

    assert opinion.vote == "HOLD"


def test_balanced_portfolio_votes_buy():
    opinion = DiversificationCommittee().evaluate(build_context(10))

    assert opinion.vote == "BUY"
