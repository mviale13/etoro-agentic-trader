from datetime import UTC, datetime

from app.domain.account_snapshot import AccountSnapshot
from app.domain.decision import Decision
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.morning_brief import MorningBrief
from app.renderers.decision_renderer import DecisionRenderer
from app.renderers.market_renderer import MarketRenderer
from app.renderers.morning_renderer import MorningRenderer
from app.renderers.policy_renderer import PolicyRenderer
from app.renderers.status_renderer import StatusRenderer


def test_status_renderer(capsys):
    snapshot = AccountSnapshot(
        broker="eToro",
        mode="demo",
        connected=True,
        positions_count=0,
        positions=(),
        pending_orders=0,
        copy_portfolios=0,
        latency_ms=125.0,
        timestamp=datetime.now(UTC),
        cash_usd=100_000,
        invested_usd=0,
        unrealized_pnl_usd=0,
        equity_usd=100_000,
    )

    StatusRenderer.render(snapshot)

    output = capsys.readouterr().out

    assert "eToro Demo" in output
    assert "$100,000.00" in output
    assert "Positions:       0" in output


def test_morning_renderer(capsys):
    brief = MorningBrief(
        portfolio_health="Healthy",
        portfolio_value=100_000,
        cash_allocation=100,
        open_positions=0,
        recommendation="WAIT",
        confidence=95,
        summary="No action is required.",
    )

    MorningRenderer.render(brief)

    output = capsys.readouterr().out

    assert "Good morning, Marcos." in output
    assert "WAIT" in output
    assert "95%" in output


def test_market_renderer(capsys):
    snapshot = MarketSnapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500 ETF",
                price=600,
                change_percent=0.5,
            ),
        ),
        market_mood="positive",
        volatility="low",
        summary="Markets are positive.",
        timestamp=datetime.now(UTC),
    )

    MarketRenderer.render(snapshot)

    output = capsys.readouterr().out

    assert "SPY" in output
    assert "+0.50%" in output
    assert "Positive" in output


def test_policy_renderer(capsys):
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

    PolicyRenderer.render(policy)

    output = capsys.readouterr().out

    assert "Moderate" in output
    assert "Stocks" in output
    assert "Max Crypto" in output


def test_decision_renderer(capsys):
    decision = Decision(
        action="HOLD",
        priority="LOW",
        confidence=85,
        explanation="Portfolio aligned.",
    )

    DecisionRenderer.render(decision)

    output = capsys.readouterr().out

    assert "HOLD" in output
    assert "85%" in output
    assert "Portfolio aligned." in output
