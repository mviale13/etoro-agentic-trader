import argparse
import asyncio
from typing import NoReturn

import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.domain.account_snapshot import AccountSnapshot
from app.services.account_service import AccountService


def _money(value: float | None) -> str:
    return "Unavailable" if value is None else f"${value:,.2f}"


def _print_status(snapshot: AccountSnapshot) -> None:
    print()
    print("MOVRvest")
    print("Invest with intelligence.")
    print()
    print(f"Broker:          {snapshot.broker} {snapshot.mode.title()}")
    print("Status:          Connected")
    print(f"Latency:         {snapshot.latency_ms:.1f} ms")
    print(f"Last sync:       {snapshot.timestamp.astimezone():%Y-%m-%d %H:%M:%S %Z}")
    print()
    print(f"Equity:          {_money(snapshot.equity_usd)}")
    print(f"Available cash:  {_money(snapshot.cash_usd)}")
    print(f"Invested:        {_money(snapshot.invested_usd)}")
    print(f"Unrealized P&L:  {_money(snapshot.unrealized_pnl_usd)}")
    print(f"Positions:       {snapshot.positions}")
    print(f"Pending orders:  {snapshot.pending_orders}")
    print(f"Copy portfolios: {snapshot.copy_portfolios}")
    print()


async def _status() -> int:
    settings = get_settings()
    service = AccountService(EtoroAccountBroker(settings))
    try:
        snapshot = await service.snapshot()
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


def main() -> NoReturn:
    parser = argparse.ArgumentParser(prog="movrvest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show the live eToro account status")
    args = parser.parse_args()

    if args.command == "status":
        raise SystemExit(asyncio.run(_status()))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
