from app.config import Settings
from app.models import PortfolioState, Side, TradeProposal
from app.risk import RiskEngine


def make_settings(**changes):
    return Settings(_env_file=None, **changes)


def make_proposal(**changes):
    values = {
        "symbol": "BTC",
        "side": Side.buy,
        "amount_usd": 50,
        "leverage": 1,
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.06,
        "confidence": 0.7,
        "strategy": "test",
        "reasons": ["test"],
        "approved_by_user": True,
    }
    values.update(changes)
    return TradeProposal(**values)


def test_safe_crypto_order_allowed():
    decision = RiskEngine(make_settings()).evaluate(
        make_proposal(),
        PortfolioState(),
    )
    assert decision.allowed
    assert decision.adjusted_amount_usd == 50


def test_unapproved_order_blocked():
    decision = RiskEngine(make_settings()).evaluate(
        make_proposal(approved_by_user=False),
        PortfolioState(),
    )
    assert not decision.allowed


def test_crypto_exposure_cap():
    decision = RiskEngine(make_settings()).evaluate(
        make_proposal(),
        PortfolioState(equity_usd=2000, crypto_exposure_usd=400),
    )
    assert not decision.allowed


def test_daily_loss_breaker():
    decision = RiskEngine(make_settings()).evaluate(
        make_proposal(),
        PortfolioState(equity_usd=2000, daily_pnl_usd=-31),
    )
    assert not decision.allowed
