from datetime import UTC, datetime

from app.committee.cash import CashCommittee
from app.domain.asset_class import AssetClass
from app.domain.committee_context import CommitteeContext
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot


def build_context(cash: float) -> CommitteeContext:
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            stocks=100 - cash,
            etfs=0,
            crypto=0,
            cash=cash,
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

    intelligence = MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="neutral",
            volatility="medium",
            summary="Test market.",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=50,
            label="Neutral",
            subject=AssetClass.CRYPTO,
            reading=Provenance(
                source="Alternative.me",
                observed_at=datetime.now(UTC),
            ),
        ),
        outlook="NEUTRAL",
        confidence=60,
        summary="Mixed signals.",
    )

    return CommitteeContext(
        intelligence=intelligence,
        portfolio=portfolio,
        policy=policy,
    )


def test_excess_cash_votes_buy():
    opinion = CashCommittee().evaluate(
        build_context(cash=30),
    )

    assert opinion.member == "Cash"
    assert opinion.vote == "BUY"
    assert opinion.confidence == 90
    assert "above" in opinion.rationale


def test_low_cash_votes_hold():
    opinion = CashCommittee().evaluate(
        build_context(cash=2),
    )

    assert opinion.vote == "HOLD"
    assert opinion.confidence == 90
    assert "below" in opinion.rationale


def test_cash_within_threshold_votes_hold():
    opinion = CashCommittee().evaluate(
        build_context(cash=14),
    )

    assert opinion.vote == "HOLD"
    assert opinion.confidence == 80
    assert "within" in opinion.rationale
