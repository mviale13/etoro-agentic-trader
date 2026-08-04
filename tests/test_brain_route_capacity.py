"""What the dashboard is told about the account's room to act."""

from dataclasses import replace

from app.api.routes.brain import _capacity, _holdings
from app.application.brain.reasoning.models.capacity_assessment import (
    CapacityAssessment,
)
from app.domain.portfolio_position import PortfolioPosition
from tests.test_brain_context import make_portfolio


def make_capacity() -> CapacityAssessment:
    return CapacityAssessment(
        cash_actual_pct=20.0,
        cash_target_pct=15.0,
        funding_room_pct=5.0,
        funding_room_usd=5_000.0,
        single_position_limit_pct=20.0,
        largest_position="MSFT",
        largest_position_pct=18.0,
        single_position_headroom_pct=2.0,
        crypto_limit_pct=15.0,
        crypto_actual_pct=10.0,
        crypto_headroom_pct=5.0,
        unmeasured=(),
    )


def make_holding(
    symbol: str = "MSFT",
    market_value_usd: float = 18_000.0,
) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=36.0,
        invested_usd=15_000.0,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=3_000.0,
        asset_class="stocks",
        instrument_id=1001,
    )


def test_absent_capacity_is_served_as_null_not_as_a_default() -> None:
    assert _capacity(None) is None


def test_capacity_is_served_with_every_term_and_its_absences() -> None:
    served = _capacity(
        replace(
            make_capacity(),
            crypto_actual_pct=None,
            crypto_headroom_pct=None,
            unmeasured=("5.0% of the account is unclassified.",),
        )
    )

    assert served is not None
    assert served["funding_room_pct"] == 5.0
    assert served["funding_room_usd"] == 5_000.0
    assert served["single_position_headroom_pct"] == 2.0
    assert served["largest_position"] == "MSFT"

    # An unmeasured term survives as null with its reason beside it.
    assert served["crypto_actual_pct"] is None
    assert served["crypto_headroom_pct"] is None
    assert served["unmeasured"] == ["5.0% of the account is unclassified."]


def test_a_breach_is_served_signed_not_clamped() -> None:
    served = _capacity(
        replace(make_capacity(), single_position_headroom_pct=-6.0),
    )

    assert served is not None
    assert served["single_position_headroom_pct"] == -6.0


def test_holdings_are_served_as_facts_with_the_snapshots_own_weight() -> None:
    portfolio = replace(
        make_portfolio(),
        holdings=(make_holding(), make_holding("BTC", 9_000.0)),
    )

    served = _holdings(portfolio)

    assert [row["symbol"] for row in served] == ["MSFT", "BTC"]
    assert served[0]["invested_usd"] == 15_000.0
    assert served[0]["market_value_usd"] == 18_000.0
    assert served[0]["unrealized_pnl_usd"] == 3_000.0
    assert served[0]["weight_pct"] == 18.0
    assert served[1]["weight_pct"] == 9.0
    assert served[0]["resolved"] is True


def test_an_unresolved_holding_keeps_its_reported_identity() -> None:
    """A row the broker reported is a row the investor owns."""

    portfolio = replace(
        make_portfolio(),
        holdings=(make_holding(symbol="#4711"),),
    )

    served = _holdings(portfolio)

    assert served[0]["symbol"] == "#4711"
    assert served[0]["resolved"] is False


def test_a_valueless_account_serves_weights_as_null_not_zero() -> None:
    portfolio = replace(
        make_portfolio(),
        total_value=0.0,
        holdings=(make_holding(),),
    )

    served = _holdings(portfolio)

    assert served[0]["weight_pct"] is None
