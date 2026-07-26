import argparse
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn

from app.commands import (
    committee,
    daily,
    decision,
    doctor,
    explain,
    intelligence,
    market,
    morning,
    policy,
    status,
    watchlist,
)

CommandHandler = Callable[[], Coroutine[Any, Any, int]]

COMMANDS: dict[str, tuple[str, CommandHandler]] = {
    "status": (
        "Show the live eToro account status",
        status.run,
    ),
    "morning": (
        "Show the deterministic morning brief",
        morning.run,
    ),
    "market": (
        "Show the current market snapshot",
        market.run,
    ),
    "policy": (
        "Show the configured investment policy",
        policy.run,
    ),
    "decision": (
        "Generate a deterministic investment decision",
        decision.run,
    ),
    "intelligence": (
        "Show the current market intelligence",
        intelligence.run,
    ),
    "committee": (
        "Run the investment committee",
        committee.run,
    ),
    "daily": (
        "Show the daily investment briefing",
        daily.run,
    ),
    "doctor": (
        "Analyze your portfolio health",
        doctor.run,
    ),
    "explain": (
        "Explain an investment decision",
        explain.run,
    ),
    "watchlist": (
        "Analyze your watchlist",
        watchlist.run,
    ),
}


def main() -> NoReturn:
    parser = argparse.ArgumentParser(
        prog="movrvest",
        description="MOVRvest — Invest with intelligence.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name, (help_text, _) in COMMANDS.items():
        command_parser = subparsers.add_parser(
            name,
            help=help_text,
        )

        if name == "explain":
            command_parser.add_argument(
                "symbol",
                nargs="?",
                default="SPY",
                help="Ticker symbol, for example MSFT, ASML or BTC-USD",
            )

    args = parser.parse_args()

    if args.command == "explain":
        raise SystemExit(
            asyncio.run(
                explain.run(args.symbol),
            )
        )

    _, command_handler = COMMANDS[args.command]
    raise SystemExit(asyncio.run(command_handler()))


if __name__ == "__main__":
    main()
