import argparse
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn

from app.commands import (
    brain,
    committee,
    company,
    credentials,
    daily,
    decision,
    doctor,
    evaluate,
    explain,
    intelligence,
    market,
    morning,
    policy,
    record,
    status,
    today,
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
    "watchlist": (
        "Analyze your watchlist",
        watchlist.run,
    ),
    "today": (
        "Show the MOVRvest Morning Brief",
        today.run,
    ),
    "brain": (
        "Run the complete MOVRvest Artificial CIO pipeline",
        brain.run,
    ),
    "credentials": (
        "Show what the configured eToro credentials can reach",
        credentials.run,
    ),
    "record": (
        "Score past decisions against what the securities did next",
        record.run,
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="movrvest",
        description="MOVRvest — Invest with intelligence.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for name, (help_text, _) in COMMANDS.items():
        subparsers.add_parser(
            name,
            help=help_text,
            description=help_text,
        )

    explain_parser = subparsers.add_parser(
        "explain",
        help="Explain an investment decision",
        description="Explain an investment decision",
    )
    explain_parser.add_argument(
        "symbol",
        nargs="?",
        default="SPY",
        help="Ticker symbol, for example MSFT, ASML or BTC-USD",
    )

    company_parser = subparsers.add_parser(
        "company",
        help="Analyze a company from your eToro watchlists",
        description="Analyze a company from your eToro watchlists",
    )
    company_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example MSFT, NVDA or BTC",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Run the Artificial CIO pipeline and explain the decision",
        description="Run the Artificial CIO pipeline and explain the decision",
    )
    evaluate_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example MSFT, ASML or BTC-USD",
    )

    return parser


async def dispatch(args: argparse.Namespace) -> int:
    if args.command == "explain":
        return await explain.run(args.symbol)

    if args.command == "company":
        return await company.run(args.symbol)

    if args.command == "evaluate":
        return await evaluate.run(args.symbol)

    _, command_handler = COMMANDS[args.command]
    return await command_handler()


def main() -> NoReturn:
    parser = build_parser()
    args = parser.parse_args()

    raise SystemExit(
        asyncio.run(
            dispatch(args),
        )
    )


if __name__ == "__main__":
    main()
