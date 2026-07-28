from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

from app.domain.brain_context import BrainContext
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.domain.market_opportunity import (
    MarketOpportunity,
)
from app.domain.portfolio_facts import (
    PortfolioFacts,
)
from app.domain.portfolio_snapshot import (
    Allocation,
    PortfolioSnapshot,
)
from app.services.executive.executive_meeting_service import (
    ExecutiveMeetingService,
)

NOW = datetime.now(
    UTC,
)


def market_fact(
    symbol: str,
    change_percent: float,
    price: float = 100.0,
) -> MarketFact:
    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=price,
        change_percent=change_percent,
        source="test",
        as_of=NOW,
    )


def test_runs_complete_executive_meeting() -> None:
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=100,
            stocks=0,
            etfs=0,
            crypto=0,
            unclassified=0,
        ),
        total_value=100000,
        total_value_eur=92000,
        positions=0,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    policy = InvestmentPolicy(
        risk_profile="long_term",
        target=AllocationTarget(
            stocks=20,
            etfs=10,
            crypto=65,
            cash=5,
        ),
        constraints=InvestmentConstraints(
            max_single_position=20,
            max_crypto=65,
            rebalance_threshold=5,
        ),
    )

    context = cast(
        BrainContext,
        SimpleNamespace(
            portfolio=portfolio,
            investment_policy=policy,
        ),
    )

    portfolio_facts = PortfolioFacts(
        total_value_usd=100000,
        total_value_eur=92000,
        cash_usd=100000,
        invested_usd=0,
        unrealized_pnl_usd=0,
        cash_allocation=100,
        positions=0,
        pending_orders=0,
        copy_portfolios=0,
        connected=True,
        latency_ms=200,
        last_sync=NOW,
        source="eToro Demo",
    )

    market_facts = MarketFacts(
        instruments=(
            market_fact("SPY", 0.8),
            market_fact("QQQ", 1.2),
            market_fact("IWM", 0.4),
            market_fact(
                "BTC",
                3.1,
                price=120000,
            ),
        ),
        vix=15,
        source="test",
        as_of=NOW,
    )

    opportunity = MarketOpportunity(
        symbol="BTC",
        asset_type="crypto",
        source="Scanner",
    )

    decision = ExecutiveMeetingService().analyze(
        opportunity=opportunity,
        context=context,
        portfolio_facts=portfolio_facts,
        market_facts=market_facts,
        proposed_position_pct=20,
    )

    assert decision.recommendation == "BUY"
    assert decision.confidence > 0
    assert len(decision.votes) == 5

    committees = {vote.committee for vote in decision.votes}

    assert committees == {
        "Portfolio",
        "Market",
        "Opportunity",
        "Risk",
        "Policy",
    }


def test_requires_investment_policy() -> None:
    portfolio = PortfolioSnapshot(
        allocation=Allocation(
            cash=100,
            stocks=0,
            etfs=0,
            crypto=0,
            unclassified=0,
        ),
        total_value=100000,
        total_value_eur=92000,
        positions=0,
        largest_position=None,
        largest_position_pct=0,
        risk_flags=(),
    )

    context = cast(
        BrainContext,
        SimpleNamespace(
            portfolio=portfolio,
            investment_policy=None,
        ),
    )

    portfolio_facts = PortfolioFacts(
        total_value_usd=100000,
        total_value_eur=92000,
        cash_usd=100000,
        invested_usd=0,
        unrealized_pnl_usd=0,
        cash_allocation=100,
        positions=0,
        pending_orders=0,
        copy_portfolios=0,
        connected=True,
        latency_ms=200,
        last_sync=NOW,
        source="eToro Demo",
    )

    market_facts = MarketFacts(
        instruments=(market_fact("BTC", 3.1),),
        vix=15,
        source="test",
        as_of=NOW,
    )

    opportunity = MarketOpportunity(
        symbol="BTC",
        asset_type="crypto",
        source="Scanner",
    )

    try:
        ExecutiveMeetingService().analyze(
            opportunity=opportunity,
            context=context,
            portfolio_facts=portfolio_facts,
            market_facts=market_facts,
            proposed_position_pct=20,
        )
    except ValueError as error:
        assert "Investment Policy" in str(error)
    else:
        raise AssertionError("Expected a missing-policy error.")
