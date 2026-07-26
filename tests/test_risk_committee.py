from datetime import UTC, datetime

from app.committee.risk import RiskCommittee
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


def context(volatility: str) -> CommitteeContext:
    intelligence = MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="positive",
            volatility=volatility,
            summary="Healthy",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=70,
            label="Greed",
            source="Alternative.me",
        ),
        outlook="BULLISH",
        confidence=80,
        summary="Healthy market.",
    )

    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=60,
            etfs=20,
            crypto=10,
            cash=10,
            unclassified=0,
        ),
        total_value=100_000,
        positions=5,
        largest_position=None,
        largest_position_pct=0,
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

    return CommitteeContext(
        intelligence=intelligence,
        portfolio=portfolio,
        policy=policy,
    )


def test_low_volatility():
    opinion = RiskCommittee().evaluate(
        context("low"),
    )

    assert opinion.vote == "BUY"


def test_medium_volatility():
    opinion = RiskCommittee().evaluate(
        context("medium"),
    )

    assert opinion.vote == "HOLD"


def test_high_volatility():
    opinion = RiskCommittee().evaluate(
        context("high"),
    )

    assert opinion.vote == "HOLD"
