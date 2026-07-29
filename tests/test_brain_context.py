from datetime import UTC, datetime

from app.brain import Brain, BrainContext
from app.cio.investment_case import InvestmentCase
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot


def make_portfolio() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=20.0,
            stocks=50.0,
            etfs=20.0,
            crypto=10.0,
            unclassified=0.0,
        ),
        total_value=100_000.0,
        positions=4,
        largest_position="MSFT",
        largest_position_pct=18.0,
        risk_flags=(),
        total_value_eur=86_000.0,
    )


def make_market() -> MarketSnapshot:
    return MarketSnapshot(
        quotes=(
            MarketQuote(
                symbol="MSFT",
                name="Microsoft",
                price=500.0,
                change_percent=1.5,
            ),
        ),
        market_mood="constructive",
        volatility="normal",
        summary="Markets are constructive with normal volatility.",
        timestamp=datetime.now(UTC),
    )


def make_policy() -> InvestmentPolicy:
    return InvestmentPolicy(
        risk_profile="balanced",
        target=AllocationTarget(
            stocks=50.0,
            etfs=25.0,
            crypto=10.0,
            cash=15.0,
        ),
        constraints=InvestmentConstraints(
            max_single_position=20.0,
            max_crypto=15.0,
            rebalance_threshold=5.0,
        ),
    )


def test_brain_context_contains_complete_working_memory() -> None:
    investment_case = InvestmentCase(
        symbol="MSFT",
        company_name="Microsoft",
    )

    context = BrainContext(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        investment_cases={"MSFT": investment_case},
        evidence={"MSFT": ("Strong profitability",)},
        committee_opinions={"MSFT": ("Quality committee approves",)},
        memory={"last_review": "2026-07-29"},
        alerts=("Technology concentration approaching limit.",),
    )

    assert context.portfolio.total_value == 100_000.0
    assert context.market.quote("msft") is not None
    assert context.investment_case(" msft ") == investment_case
    assert context.evidence_for("msft") == ("Strong profitability",)
    assert context.opinions_for("MSFT") == ("Quality committee approves",)
    assert context.alerts == ("Technology concentration approaching limit.",)


def test_brain_context_defaults_to_empty_optional_memory() -> None:
    context = BrainContext(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    )

    assert context.investment_cases == {}
    assert context.evidence_for("MSFT") == ()
    assert context.opinions_for("MSFT") == ()
    assert context.memory == {}
    assert context.alerts == ()


def test_brain_exposes_its_working_context() -> None:
    investment_case = InvestmentCase(
        symbol="MSFT",
        company_name="Microsoft",
    )

    context = BrainContext(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        investment_cases={"MSFT": investment_case},
        evidence={"MSFT": ("Strong profitability",)},
        committee_opinions={"MSFT": ("Quality committee approves",)},
        memory={"last_review": "2026-07-29"},
        alerts=("Technology concentration approaching limit.",),
    )

    brain = Brain(context=context)

    assert brain.portfolio is context.portfolio
    assert brain.market is context.market
    assert brain.investment_policy is context.investment_policy
    assert brain.investment_case(" msft ") == investment_case
    assert brain.evidence_for("msft") == ("Strong profitability",)
    assert brain.opinions_for("MSFT") == ("Quality committee approves",)
    assert brain.memory == {"last_review": "2026-07-29"}
    assert brain.alerts == ("Technology concentration approaching limit.",)


def test_brain_returns_copies_of_mutable_mappings() -> None:
    context = BrainContext(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        memory={"cycle": 1},
    )

    brain = Brain(context=context)

    exposed_memory = brain.memory
    exposed_memory["cycle"] = 2

    assert brain.memory == {"cycle": 1}
    assert context.memory == {"cycle": 1}
