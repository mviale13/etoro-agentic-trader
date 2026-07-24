import argparse
import asyncio
from typing import NoReturn

import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.domain.account_snapshot import AccountSnapshot
from app.domain.morning_brief import MorningBrief
from app.services.account_service import AccountService
from app.services.morning_brief_service import MorningBriefService
from app.services.portfolio_service import PortfolioService
from datetime import datetime

from app.providers.yahoo_market_provider import YahooMarketProvider
from app.domain.market_snapshot import MarketSnapshot
from app.services.market_service import MarketService


def _money(value: float | None) -> str:
    return "Unavailable" if value is None else f"${value:,.2f}"


def _account_service() -> AccountService:
    settings = get_settings()
    broker = EtoroAccountBroker(settings)
    return AccountService(broker)


def _print_status(snapshot: AccountSnapshot) -> None:
    print()
    print("MOVRvest")
    print("Invest with intelligence.")
    print()
    print(f"Broker:          {snapshot.broker} {snapshot.mode.title()}")
    print("Status:          Connected")
    print(f"Latency:         {snapshot.latency_ms:.1f} ms")
    print(
        f"Last sync:       "
        f"{snapshot.timestamp.astimezone():%Y-%m-%d %H:%M:%S %Z}"
    )
    print()
    print(f"Equity:          {_money(snapshot.equity_usd)}")
    print(f"Available cash:  {_money(snapshot.cash_usd)}")
    print(f"Invested:        {_money(snapshot.invested_usd)}")
    print(f"Unrealized P&L:  {_money(snapshot.unrealized_pnl_usd)}")
    print(f"Positions:       {snapshot.positions}")
    print(f"Pending orders:  {snapshot.pending_orders}")
    print(f"Copy portfolios: {snapshot.copy_portfolios}")
    print()


def _print_morning(brief: MorningBrief) -> None:
    print()
    print("MOVRvest")
    print("Invest with intelligence.")
    print()
    print("Good morning, Marcos.")
    print()
    print(f"Portfolio health: {brief.portfolio_health}")
    print(f"Portfolio value:  {_money(brief.portfolio_value)}")
    print(f"Cash allocation:  {brief.cash_allocation:.1f}%")
    print(f"Open positions:   {brief.open_positions}")
    print()
    print(f"Recommendation:   {brief.recommendation}")
    print(f"Confidence:       {brief.confidence}%")
    print()
    print(brief.summary)
    print()

def _print_market(snapshot: MarketSnapshot) -> None:
    print()
    print("MOVRvest")
    print("Invest with intelligence.")
    print()
    print("Market Snapshot")
    print("────────────────────────────────")
    print()

    for quote in snapshot.quotes:
        arrow = "▲" if quote.change_percent >= 0 else "▼"

        print(
            f"{quote.symbol:<6}"
            f"${quote.price:>10,.2f}   "
            f"{arrow} {quote.change_percent:+.2f}%"
        )

    print()
    print(f"Market Mood : {snapshot.market_mood.title()}")
    print(f"Volatility  : {snapshot.volatility.title()}")
    print()
    print(snapshot.summary)
    print()

async def _status() -> int:
    try:
        snapshot = await _account_service().snapshot()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]
        print(f"MOVRvest could not connect to eToro (HTTP {status}).")
        print(body)
        return 1
    except Exception as exc:
        print(f"MOVRvest status failed: {exc}")
        return 1

    _print_status(snapshot)
    return 0


async def _morning() -> int:
    try:
        account = await _account_service().snapshot()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]
        print(f"MOVRvest could not connect to eToro (HTTP {status}).")
        print(body)
        return 1
    except Exception as exc:
        print(f"MOVRvest morning brief failed: {exc}")
        return 1

    portfolio = PortfolioService().analyze(account)
    brief = MorningBriefService().build(portfolio)

    _print_morning(brief)
    return 0

async def _market() -> int:
    provider = YahooMarketProvider()

    market_data = await provider.snapshot()

    snapshot = MarketService().build_snapshot(
        quotes=market_data.quotes,
        vix=market_data.vix,
        timestamp=datetime.now(),
    )

    _print_market(snapshot)

    return 0

def main() -> NoReturn:
    parser = argparse.ArgumentParser(
        prog="movrvest",
        description="MOVRvest — Invest with intelligence.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "status",
        help="Show the live eToro account status",
    )

    subparsers.add_parser(
        "morning",
        help="Show the deterministic morning brief",
    )

    subparsers.add_parser(
        "market",
        help="Show the current market snapshot",
    )

    args = parser.parse_args()

    if args.command == "status":
        raise SystemExit(asyncio.run(_status()))

    if args.command == "morning":
        raise SystemExit(asyncio.run(_morning()))

    if args.command == "market":
        raise SystemExit(asyncio.run(_market()))

    raise SystemExit(2)


if __name__ == "__main__":
    main()