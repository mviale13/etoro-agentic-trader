from dataclasses import replace
from datetime import UTC, datetime

from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_position import PortfolioPosition
from app.services.portfolio_service import PortfolioService


def build_account(
    *,
    equity: float | None,
    cash: float | None,
    invested: float | None,
    positions: int = 0,
) -> AccountSnapshot:
    return AccountSnapshot(
        broker="eToro",
        mode="demo",
        connected=True,
        positions_count=positions,
        positions=(),
        pending_orders=0,
        copy_portfolios=0,
        latency_ms=100,
        timestamp=datetime.now(UTC),
        cash_usd=cash,
        invested_usd=invested,
        unrealized_pnl_usd=0,
        equity_usd=equity,
    )


def test_zero_equity_leaves_the_cash_share_undefined_without_claiming_absence():
    """A measured zero cash on a zero account: the amount is 0, the share is not.

    0/0 is not 0%. The amount stays the measured zero it is, the share
    is absent, and no "could not be read" flag fires — cash WAS read.
    """

    portfolio = PortfolioService().analyze(build_account(equity=0, cash=0, invested=0))

    assert portfolio.available_cash_usd == 0.0, "the amount was measured"
    assert portfolio.allocation.cash is None, "the share of nothing is undefined"
    assert portfolio.risk_flags == (), "nothing failed to be read here"


def test_zero_equity_returns_zero_allocations():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=0,
            cash=0,
            invested=0,
        )
    )

    assert portfolio.total_value == 0
    assert portfolio.allocation.cash is None
    assert portfolio.allocation.unclassified == 0
    assert portfolio.risk_flags == ()


def test_missing_cash_stays_missing_and_is_never_reported_as_zero():
    """The repaired defect: absence survives instead of becoming 0.0."""

    portfolio = PortfolioService().analyze(
        build_account(
            equity=None,
            cash=None,
            invested=None,
        )
    )

    assert portfolio.total_value == 0
    assert portfolio.available_cash_usd is None
    assert portfolio.available_cash_eur is None
    assert portfolio.allocation.cash is None
    assert portfolio.liquidity_pct is None
    assert portfolio.allocation.unclassified == 0
    assert any("could not be read" in flag for flag in portfolio.risk_flags)


def test_high_cash_allocation_sets_cash_concentration_flag():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=100_000,
            cash=85_000,
            invested=15_000,
            positions=2,
        )
    )

    assert portfolio.allocation.cash == 85.0
    assert portfolio.allocation.unclassified == 15.0
    assert "Cash concentration" in portfolio.risk_flags
    assert (
        "Invested assets are not yet classified by asset type" in portfolio.risk_flags
    )


def test_percentage_rounding():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=3,
            cash=1,
            invested=2,
        )
    )

    assert portfolio.allocation.cash == 33.33
    assert portfolio.allocation.unclassified == 66.67


#: The broker's identifier per security, which is what identifies a
#: holding. Two buys of one security share it; the symbol does not
#: distinguish them and, before resolution, is not there at all.
INSTRUMENTS = {"BTC": 100_000, "ETH": 100_001, "SPCX": 15_618}


def held(symbol: str, value: float, named: bool = True) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol if named else "",
        quantity=1.0,
        invested_usd=value,
        market_value_usd=value,
        unrealized_pnl_usd=0.0,
        asset_class="crypto",
        instrument_id=INSTRUMENTS[symbol],
    )


def test_a_security_bought_twice_is_one_holding() -> None:
    """
    The broker reports a position per trade; the policy limits a security.

    Found on the real book: BTC bought twice arrived as 20.0% and 0.5%,
    and the largest *row* was read as the largest *holding*. The card
    said "0.0 pts over the limit" against a 20% limit while the investor
    actually held 20.5% — a breach of their own policy reported as
    compliance.
    """

    account = replace(
        build_account(equity=100_000.0, cash=0.0, invested=100_000.0, positions=3),
        positions=(
            held("BTC", 20_000.0),
            held("ETH", 10_000.0),
            held("BTC", 500.0),
        ),
    )

    snapshot = PortfolioService().analyze(account)

    assert snapshot.largest_position == "BTC"
    assert snapshot.largest_position_pct == 20.5


def test_the_largest_holding_can_be_one_the_broker_split() -> None:
    """
    Two small buys can outweigh one big one, and used not to.

    Ranking by row would have named ETH here, because neither BTC trade
    is individually the largest — the investor holds more BTC than ETH.
    """

    account = replace(
        build_account(equity=100_000.0, cash=0.0, invested=100_000.0, positions=3),
        positions=(
            held("BTC", 6_000.0),
            held("ETH", 9_000.0),
            held("BTC", 6_000.0),
        ),
    )

    snapshot = PortfolioService().analyze(account)

    assert snapshot.largest_position == "BTC"
    assert snapshot.largest_position_pct == 12.0


def test_holdings_are_summed_by_instrument_not_by_symbol() -> None:
    """
    The regression this nearly shipped as a fix.

    The broker reports every position with an **empty** symbol and a real
    instrument id; symbols are resolved from the watchlists a step later.
    Summing by symbol therefore collapsed all twelve holdings into one
    nameless bucket and reported the entire invested balance — 33.2% of
    the account — as the largest holding.
    """

    account = replace(
        build_account(equity=100_000.0, cash=0.0, invested=100_000.0, positions=3),
        positions=(
            held("BTC", 20_000.0, named=False),
            held("ETH", 10_000.0, named=False),
            held("BTC", 500.0, named=False),
        ),
    )

    snapshot = PortfolioService().analyze(account)

    assert snapshot.largest_position_pct == 20.5
