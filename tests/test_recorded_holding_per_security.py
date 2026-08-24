"""A recorded holding is a security, never a broker position.

The homepage's holdings table renders one row per `RecordedHolding` and
pairs it with the cycle's own per-security course. The cycle wrote one
entry per *broker position* — eToro reports a position per trade — while
`_portfolio_weights` computed one share per *security* and attached that
whole share to each partial row.

On the live account that produced a table where BTC appeared twice at
21.9% each (43.9% of the account, against a real 21.9%), the invested
book read 79.3% of an account holding 44.7% beside 55.3% cash, and 17
rows sat next to the 14 courses the same cycle produced from the same
account. The symbol was also the React key, so three of the rows were
duplicate keys.

The same defect was fixed one layer down in
`PortfolioService._largest_position`, where measuring the biggest *row*
measured a transaction and read a 20.0% + 0.5% BTC holding as compliant
with a 20% limit. These pin the fix at the layer that names the thing a
holding: the record.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.commands.cycle import _portfolio_weights, _recorded_portfolio
from app.domain.capital_policy import CapitalPolicyReading
from app.domain.daily_cycle import (
    RecordedHolding,
    RecordedPortfolio,
    holdings_by_security,
)
from app.domain.portfolio_position import PortfolioPosition
from app.infrastructure.evidence.daily_cycle_store import SCHEMA, DailyCycleStore

MOMENT = datetime(2026, 8, 20, 20, 59, tzinfo=UTC)


def position(
    symbol: str,
    value: float,
    *,
    instrument_id: int,
) -> PortfolioPosition:
    """One broker row: a trade, which is what eToro actually reports."""

    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=value,
        market_value_usd=value,
        unrealized_pnl_usd=0.0,
        asset_class=None,
        instrument_id=instrument_id,
    )


def brain(*positions: PortfolioPosition, total: float = 100_000.0):
    """The brain shape `_recorded_portfolio` reads, and nothing more."""

    return SimpleNamespace(
        portfolio=SimpleNamespace(
            total_value=total,
            holdings=positions,
            # All four measured shares, because that is what a
            # `PortfolioAllocation` carries and what the record now
            # reads the account's own shape from.
            allocation=SimpleNamespace(stocks=50.0, etfs=0.0, crypto=25.0, cash=25.0),
            available_cash_usd=25_000.0,
            last_sync=None,
        ),
        investment_policy=None,
    )


def recorded(*positions: PortfolioPosition, total: float = 100_000.0):
    stub = brain(*positions, total=total)
    weights, cash_pct, total_value = _portfolio_weights(stub)

    # No validated allocation policy: these pin the holdings fold,
    # and the plan beside it is a different fact. The refusal travels,
    # and the holdings must survive it intact.
    return _recorded_portfolio(
        stub,
        weights,
        cash_pct,
        total_value,
        policy_reading=CapitalPolicyReading(
            refused_because="no policy is loaded in this fixture"
        ),
    )


# ── the cycle records securities, not trades ────────────────────────


def test_two_trades_in_one_security_are_recorded_once() -> None:
    portfolio = recorded(
        position("BTC", 22_298.73, instrument_id=100_000),
        position("BTC", 567.37, instrument_id=100_000),
        position("ETH", 12_067.13, instrument_id=100_001),
    )

    assert portfolio is not None
    assert [holding.symbol for holding in portfolio.holdings] == ["BTC", "ETH"]

    btc = portfolio.holdings[0]

    assert btc.market_value_usd == 22_866.10, "the security's value, summed"


def test_the_weight_column_states_each_security_once() -> None:
    """The reported defect, as the investor met it.

    The share was already right; it was printed beside a partial value
    and printed twice. Nothing here recomputes it — the assertion is
    that the column now sums to the invested book rather than past it.
    """

    portfolio = recorded(
        position("BTC", 22_298.73, instrument_id=100_000),
        position("BTC", 567.37, instrument_id=100_000),
        position("ETH", 12_067.13, instrument_id=100_001),
        position("ETH", 487.04, instrument_id=100_001),
        position("ETOR", 481.49, instrument_id=100_002),
        position("ETOR", 81.53, instrument_id=100_002),
    )

    assert portfolio is not None

    shares = {holding.symbol: holding.weight_pct for holding in portfolio.holdings}

    assert shares["BTC"] == pytest.approx(22.8661), "one BTC share, not two"

    column = sum(holding.weight_pct or 0.0 for holding in portfolio.holdings)
    invested = sum(holding.market_value_usd for holding in portfolio.holdings)

    assert column == pytest.approx(invested / 100_000.0 * 100.0)


def test_a_security_bought_twice_can_outrank_a_larger_single_trade() -> None:
    """Ranking is over the security, because the fold changes the order.

    Left unfolded, the table ranked two 600 trades below a single 1,000
    one while the account held more of the first security than the
    second.
    """

    portfolio = recorded(
        position("SPCX", 1_000.0, instrument_id=200_000),
        position("ETOR", 600.0, instrument_id=200_001),
        position("ETOR", 600.0, instrument_id=200_001),
    )

    assert portfolio is not None
    assert [holding.symbol for holding in portfolio.holdings] == ["ETOR", "SPCX"]


def test_one_security_reached_through_two_broker_instruments_is_one_holding() -> None:
    """The weight was already keyed on the symbol; the rows now are too.

    `_portfolio_weights` sums by instrument and then keys by the
    resolved symbol, so two instrument ids naming one security already
    shared a single share. A row per instrument would have printed that
    share twice — the same defect wearing a different id.
    """

    portfolio = recorded(
        position("ETOR", 481.49, instrument_id=300_000),
        position("ETOR", 81.53, instrument_id=300_001),
    )

    assert portfolio is not None
    assert len(portfolio.holdings) == 1
    assert portfolio.holdings[0].market_value_usd == 563.02


def test_a_security_is_not_the_sum_of_its_rounded_trades() -> None:
    """Summed raw, rounded once — a cent is not invented by the fold."""

    portfolio = recorded(
        position("KO", 10.004, instrument_id=400_000),
        position("KO", 10.004, instrument_id=400_000),
    )

    assert portfolio is not None
    assert portfolio.holdings[0].market_value_usd == 20.01


def test_an_unresolved_position_still_contributes_no_row_and_no_share() -> None:
    """Unchanged by the fold: a holding with no ticker is not recorded."""

    portfolio = recorded(
        position("KO", 500.0, instrument_id=500_000),
        position("#500001", 250.0, instrument_id=500_001),
    )

    assert portfolio is not None
    assert [holding.symbol for holding in portfolio.holdings] == ["KO"]


# ── the record enforces its own shape ───────────────────────────────


def test_a_recorded_portfolio_refuses_a_repeated_security() -> None:
    """Enforced at construction, the way `ComparisonBasis` is.

    A caller holding the broker's rows folds them first. One that does
    not cannot build the object at all, so this cannot regress quietly
    into a page that renders it.
    """

    with pytest.raises(ValueError, match="one entry per security"):
        RecordedPortfolio(
            total_value=100_000.0,
            holdings=(
                RecordedHolding(symbol="BTC", market_value_usd=22_298.73),
                RecordedHolding(symbol="BTC", market_value_usd=567.37),
            ),
        )


def test_rows_of_one_security_that_disagree_about_the_share_are_a_contradiction() -> (
    None
):
    """The fold's precondition is checked, never assumed.

    Summing values is only the right reading where the rows agree that
    the share belongs to the whole security. Two different shares mean
    the reading is unknown, and an unknown reading is refused rather
    than aggregated into a plausible one.
    """

    with pytest.raises(ValueError, match="different shares"):
        holdings_by_security(
            (
                RecordedHolding(symbol="BTC", market_value_usd=1.0, weight_pct=21.9),
                RecordedHolding(symbol="BTC", market_value_usd=1.0, weight_pct=1.4),
            )
        )


def test_an_unmeasured_share_folds_without_becoming_a_number() -> None:
    """Absent on every row stays absent — never 0.0 (#223)."""

    folded = holdings_by_security(
        (
            RecordedHolding(symbol="KO", market_value_usd=5.0, weight_pct=None),
            RecordedHolding(symbol="KO", market_value_usd=5.0, weight_pct=None),
        )
    )

    assert folded == (
        RecordedHolding(symbol="KO", market_value_usd=10.0, weight_pct=None),
    )


# ── the line already on disk ────────────────────────────────────────


def line(store: DailyCycleStore, cycle_id: str, holdings: list[dict]) -> None:
    """A terminal record written the way the cycle used to write one."""

    store.path.parent.mkdir(parents=True, exist_ok=True)

    with store.path.open("a", encoding="utf-8") as handle:
        for row in (
            {
                "schema": SCHEMA,
                "kind": "started",
                "cycle_id": cycle_id,
                "at": MOMENT.isoformat(),
            },
            {
                "schema": SCHEMA,
                "kind": "finished",
                "cycle_id": cycle_id,
                "at": MOMENT.isoformat(),
                "status": "complete",
                "portfolio": {
                    "total_value": 104_187.44,
                    "available_cash_usd": 57_583.21,
                    "cash_pct": 55.27,
                    "observed": "",
                    "compliant": None,
                    "holdings": holdings,
                    "allocations": [],
                },
            },
        ):
            handle.write(json.dumps(row))
            handle.write("\n")


def test_a_line_written_before_the_fold_reads_as_securities(tmp_path) -> None:
    """The live record, decoded — no line rewritten and no schema bumped.

    Every figure on that line is true: the values are the trades' and
    the share is the security's. Only the reading that one row is one
    security was wrong, so folding is arithmetic over the line's own
    numbers rather than a repair of them.
    """

    store = DailyCycleStore(tmp_path / "cycles")

    line(
        store,
        "c733f808",
        [
            {"symbol": "BTC", "market_value_usd": 22_298.73, "weight_pct": 21.947079},
            {"symbol": "ETH", "market_value_usd": 12_067.13, "weight_pct": 12.049600},
            {"symbol": "BTC", "market_value_usd": 567.37, "weight_pct": 21.947079},
            {"symbol": "ETH", "market_value_usd": 487.04, "weight_pct": 12.049600},
            {"symbol": "ETOR", "market_value_usd": 481.49, "weight_pct": 0.540391},
            {"symbol": "SPCX", "market_value_usd": 472.53, "weight_pct": 0.453538},
            {"symbol": "ETOR", "market_value_usd": 81.53, "weight_pct": 0.540391},
        ],
    )

    log = store.log()

    assert log.unreadable_records == 0, "the record stays readable"

    finished = log.records[-1].finished

    assert finished is not None
    assert finished.portfolio is not None

    holdings = finished.portfolio.holdings

    assert [holding.symbol for holding in holdings] == ["BTC", "ETH", "ETOR", "SPCX"]
    assert holdings[0].market_value_usd == 22_866.10
    assert holdings[0].weight_pct == pytest.approx(21.947079)

    # And the fold reordered them: ETOR's two trades total 563.02 and
    # outrank SPCX's single 472.53, which the stored order had first.
    assert holdings[2].market_value_usd == 563.02


def test_a_line_whose_repeats_disagree_is_unreadable_rather_than_folded(
    tmp_path,
) -> None:
    """A record the fold cannot read is counted and disclosed.

    The store's existing rule, reached by a new route: an unreadable
    line refuses the whole record instead of decoding into a lifecycle,
    and the count travels to the surface as an incomplete stream.
    """

    store = DailyCycleStore(tmp_path / "cycles")

    line(
        store,
        "c1",
        [
            {"symbol": "BTC", "market_value_usd": 1.0, "weight_pct": 21.9},
            {"symbol": "BTC", "market_value_usd": 1.0, "weight_pct": 1.4},
        ],
    )

    log = store.log()

    assert log.unreadable_records == 1
    assert log.is_complete_stream is False
    assert log.records[-1].finished is None, "no account is quietly invented"
