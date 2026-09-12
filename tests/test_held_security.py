"""The one fold of the broker's trade rows into the securities held.

Four layers folded these rows before this existed, three of them over
the same input with the same key. These pin the rules the shared fold
owns, and — because two of those layers were rewired onto it — that
rewiring changed no answer.
"""

from app.api.routes.brain import _held_securities, _holdings
from app.domain.held_security import held_securities
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.portfolio_service import PortfolioService


def position(
    symbol: str = "BTC",
    *,
    instrument_id: int = 1,
    market_value_usd: float = 100.0,
    invested_usd: float = 90.0,
    unrealized_pnl_usd: float = 10.0,
    quantity: float = 1.0,
    asset_class: str | None = "crypto",
) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=quantity,
        invested_usd=invested_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=unrealized_pnl_usd,
        asset_class=asset_class,
        instrument_id=instrument_id,
    )


def snapshot(
    positions: tuple[PortfolioPosition, ...],
    total_value: float = 1_000.0,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=50.0, stocks=25.0, etfs=0.0, crypto=25.0, unclassified=0.0
        ),
        total_value=total_value,
        positions=len(positions),
        largest_position=None,
        largest_position_pct=0.0,
        risk_flags=(),
        holdings=positions,
    )


# ── the fold ────────────────────────────────────────────────────────


def test_two_trades_in_one_instrument_are_one_holding() -> None:
    """The money adds; the identity does not."""

    folded = held_securities(
        (
            position(
                "BTC",
                instrument_id=7,
                market_value_usd=23_732.12,
                invested_usd=19_999.96,
                unrealized_pnl_usd=3_732.16,
                quantity=0.25,
            ),
            position(
                "BTC",
                instrument_id=7,
                market_value_usd=603.84,
                invested_usd=499.98,
                unrealized_pnl_usd=103.86,
                quantity=0.006,
            ),
        )
    )

    assert len(folded) == 1
    held = folded[0]

    assert held.symbol == "BTC"
    assert held.trades == 2
    assert held.market_value_usd == 23_732.12 + 603.84
    assert held.invested_usd == 19_999.96 + 499.98
    assert held.unrealized_pnl_usd == 3_732.16 + 103.86
    assert held.quantity == 0.25 + 0.006


def test_a_fold_changes_the_ranking_so_it_ranks() -> None:
    """
    Two small trades outweigh a larger single one. A caller handed an
    order that no longer matched its own values could only fix it by
    sorting — which a presentation layer may not do.
    """

    folded = held_securities(
        (
            position("SPCX", instrument_id=1, market_value_usd=536.12),
            position("ETOR", instrument_id=2, market_value_usd=492.37),
            position("ETOR", instrument_id=2, market_value_usd=83.37),
        )
    )

    assert [held.symbol for held in folded] == ["ETOR", "SPCX"]

    # The largest single *trade* is SPCX's; the largest *holding* is not.
    assert max(536.12, 492.37, 83.37) == 536.12
    assert folded[0].market_value_usd == 492.37 + 83.37


def test_it_folds_on_the_instrument_and_never_on_the_symbol() -> None:
    """
    The broker reports every position with an empty symbol and a real
    instrument id. Folding on the symbol collapsed the whole account
    into one nameless holding and reported it as the largest.
    """

    folded = held_securities(
        (
            position("", instrument_id=11, market_value_usd=100.0),
            position("", instrument_id=22, market_value_usd=200.0),
            position("", instrument_id=33, market_value_usd=300.0),
        )
    )

    assert len(folded) == 3
    assert [held.instrument_id for held in folded] == [33, 22, 11]


def test_two_instruments_sharing_a_symbol_stay_two_holdings() -> None:
    folded = held_securities(
        (
            position("DIS", instrument_id=1, market_value_usd=100.0),
            position("DIS", instrument_id=2, market_value_usd=200.0),
        )
    )

    assert len(folded) == 2


def test_a_placeholder_never_displaces_a_resolved_ticker() -> None:
    """An unresolved row is still the same holding; its label is not."""

    folded = held_securities(
        (
            position("#4231", instrument_id=5, market_value_usd=10.0),
            position("NOVO-B.CO", instrument_id=5, market_value_usd=90.0),
        )
    )

    assert len(folded) == 1
    assert folded[0].symbol == "NOVO-B.CO"
    assert folded[0].resolved is True
    assert folded[0].market_value_usd == 100.0


def test_an_unresolved_holding_is_carried_and_never_dropped() -> None:
    """A row the broker reported is a row the investor owns."""

    folded = held_securities((position("#9001", instrument_id=9),))

    assert len(folded) == 1
    assert folded[0].resolved is False
    assert folded[0].symbol == "#9001"


def test_the_first_stated_asset_class_names_the_holding() -> None:
    folded = held_securities(
        (
            position("ETH", instrument_id=3, asset_class=None),
            position("ETH", instrument_id=3, asset_class="crypto"),
        )
    )

    assert folded[0].asset_class == "crypto"


def test_ties_keep_the_order_the_broker_reported() -> None:
    folded = held_securities(
        (
            position("AAA", instrument_id=1, market_value_usd=50.0),
            position("BBB", instrument_id=2, market_value_usd=50.0),
        )
    )

    assert [held.symbol for held in folded] == ["AAA", "BBB"]


def test_an_account_with_no_positions_folds_to_nothing() -> None:
    assert held_securities(()) == ()


def test_the_summed_value_is_not_rounded() -> None:
    """
    Rounding belongs where the figure is presented. `_largest_position`
    measures a policy limit with a percentage derived from this value,
    and rounding here would move it.
    """

    folded = held_securities(
        (
            position("X", instrument_id=1, market_value_usd=0.005),
            position("X", instrument_id=1, market_value_usd=0.004),
        )
    )

    assert folded[0].market_value_usd == 0.005 + 0.004


# ── the share ───────────────────────────────────────────────────────


def test_a_share_of_an_account_with_no_value_is_absent_not_zero() -> None:
    empty = snapshot((position(),), total_value=0.0)

    assert empty.weight_of(100.0) is None
    assert empty.weight_pct(position()) is None


def test_the_folded_share_is_taken_once_over_the_summed_value() -> None:
    """
    Not a sum of the trades' percentages: that drifts, and it
    re-implements the absent-not-zero rule badly.
    """

    account = snapshot((), total_value=1_000.0)

    assert account.weight_of(250.0) == 25.0
    assert account.weight_pct(position(market_value_usd=250.0)) == 25.0


# ── the two rewired callers answer exactly as before ────────────────


def _largest_position_as_it_was(
    positions: tuple[PortfolioPosition, ...],
    equity_usd: float,
) -> tuple[str | None, float]:
    """The implementation this replaced, kept here as the oracle."""

    if not positions:
        return None, 0.0

    held: dict[int, tuple[str, float]] = {}

    for item in positions:
        symbol, value = held.get(item.instrument_id, ("", 0.0))
        held[item.instrument_id] = (
            symbol or item.symbol,
            value + item.market_value_usd,
        )

    symbol, value = max(held.values(), key=lambda holding: holding[1])

    return symbol or None, PortfolioService._percentage(value, equity_usd)


def test_the_largest_position_is_unchanged_by_the_extraction() -> None:
    corpora = (
        (),
        (position("BTC", instrument_id=1, market_value_usd=23_732.12),),
        (
            position("BTC", instrument_id=1, market_value_usd=23_732.12),
            position("BTC", instrument_id=1, market_value_usd=603.84),
            position("ETH", instrument_id=2, market_value_usd=13_196.90),
            position("ETH", instrument_id=2, market_value_usd=532.64),
            position("ETOR", instrument_id=3, market_value_usd=492.37),
            position("ETOR", instrument_id=3, market_value_usd=83.37),
            position("NOVO-B.CO", instrument_id=4, market_value_usd=7_249.62),
        ),
        (
            position("", instrument_id=1, market_value_usd=100.0),
            position("AAA", instrument_id=2, market_value_usd=100.0),
        ),
        (
            position("#4231", instrument_id=5, market_value_usd=10.0),
            position("#4231", instrument_id=5, market_value_usd=90.0),
        ),
    )

    for corpus in corpora:
        for equity in (0.0, 1.0, 106_441.61):
            assert PortfolioService._largest_position(
                corpus, equity
            ) == _largest_position_as_it_was(corpus, equity)


def test_a_placeholder_no_longer_outranks_a_resolved_ticker_in_the_name() -> None:
    """
    The one answer the extraction deliberately changes.

    The implementation this replaced took the first *non-empty* symbol
    for an instrument, so a placeholder arriving before the resolved
    ticker named the largest position — the investor read `#4231` where
    the account holds NOVO-B.CO. The shared fold prefers the resolved
    ticker.

    Unreachable from the live resolution path, which resolves per
    instrument and so gives every row of one instrument the same answer.
    Changed anyway because the better answer costs nothing, and pinned
    here so the change is a decision rather than a side effect.
    """

    mixed = (
        position("#4231", instrument_id=5, market_value_usd=10.0),
        position("NOVO-B.CO", instrument_id=5, market_value_usd=90.0),
    )

    assert _largest_position_as_it_was(mixed, 1_000.0) == ("#4231", 10.0)
    assert PortfolioService._largest_position(mixed, 1_000.0) == (
        "NOVO-B.CO",
        10.0,
    )


def test_the_cycle_weights_are_unchanged_by_the_extraction() -> None:
    """
    `_portfolio_weights` folded on the instrument and then keyed by the
    resolved symbol. The shared fold does the first half; this pins that
    the second half still produces the same shares.
    """

    from app.commands.cycle import _portfolio_weights

    class _Brain:
        def __init__(self, portfolio: PortfolioSnapshot) -> None:
            self.portfolio = portfolio

    positions = (
        position("btc ", instrument_id=1, market_value_usd=200.0),
        position("BTC", instrument_id=1, market_value_usd=300.0),
        position("#4231", instrument_id=2, market_value_usd=400.0),
        position("ETH", instrument_id=3, market_value_usd=100.0),
    )

    weights, cash, total = _portfolio_weights(
        _Brain(snapshot(positions, total_value=1_000.0))  # type: ignore[arg-type]
    )

    # Normalised to the ticker, summed across the instrument's trades,
    # and an unresolved instrument contributes no symbol weight at all.
    assert weights == {"BTC": 50.0, "ETH": 10.0}
    assert cash == 50.0
    assert total == 1_000.0


def test_no_weights_are_stated_for_an_account_with_no_value() -> None:
    from app.commands.cycle import _portfolio_weights

    class _Brain:
        def __init__(self, portfolio: PortfolioSnapshot) -> None:
            self.portfolio = portfolio

    weights, _, _ = _portfolio_weights(
        _Brain(snapshot((position(),), total_value=0.0))  # type: ignore[arg-type]
    )

    assert weights == {}


# ── what the dashboard is told ──────────────────────────────────────


def test_the_payload_serves_both_questions_and_conflates_neither() -> None:
    """
    "What trades are open" and "what does this account hold" are two
    questions. Only the second one was ever served.
    """

    account = snapshot(
        (
            position("BTC", instrument_id=1, market_value_usd=750.0),
            position("BTC", instrument_id=1, market_value_usd=50.0),
            position("ETH", instrument_id=2, market_value_usd=200.0),
        ),
        total_value=1_000.0,
    )

    trades = _holdings(account)
    securities = _held_securities(account)

    assert len(trades) == 3
    assert len(securities) == 2

    # The trade rows are the broker's own fact and are untouched.
    assert [row["market_value_usd"] for row in trades] == [750.0, 50.0, 200.0]

    btc = securities[0]
    assert btc["symbol"] == "BTC"
    assert btc["market_value_usd"] == 800.0
    assert btc["weight_pct"] == 80.0
    assert btc["trades"] == 2


def test_a_consolidated_share_is_absent_where_the_account_has_no_value() -> None:
    account = snapshot((position("BTC", market_value_usd=100.0),), total_value=0.0)

    assert _held_securities(account)[0]["weight_pct"] is None


def test_the_consolidated_rows_arrive_ranked_by_the_folded_value() -> None:
    """So the page never has to sort them, which would be analysis."""

    account = snapshot(
        (
            position("SPCX", instrument_id=1, market_value_usd=536.12),
            position("ETOR", instrument_id=2, market_value_usd=492.37),
            position("ETOR", instrument_id=2, market_value_usd=83.37),
        ),
        total_value=10_000.0,
    )

    assert [row["symbol"] for row in _held_securities(account)] == ["ETOR", "SPCX"]
