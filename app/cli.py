import argparse
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn

from app.commands import (
    archetype,
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
    knowledge,
    market,
    morning,
    policy,
    record,
    status,
    today,
    watchlist,
    writer_compare,
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

    knowledge_parser = subparsers.add_parser(
        "knowledge",
        help="Show what was read from a company's own report, and from where",
        description=(
            "Show the structural facts read from a company's annual report, "
            "with the table cell behind every measured size so it can be "
            "checked against the filing by hand"
        ),
    )
    knowledge_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, ASML or VOW3.DE",
    )

    archetype_parser = subparsers.add_parser(
        "archetype",
        help="Show what kind of business a company is, and what decided it",
        description=(
            "Classify a company from its own report rather than from an "
            "industry: how much of its revenue earns which way, the rules "
            "that read it, and what could not be established"
        ),
    )
    archetype_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, NVDA or VOW3.DE",
    )

    writer_compare_parser = subparsers.add_parser(
        "writer-compare",
        help="Word one dossier with every writing provider and compare",
        description=(
            "Run the identical investment case through every configured "
            "writing provider and compare narrative, latency and cost"
        ),
    )
    writer_compare_parser.add_argument(
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

    if args.command == "knowledge":
        return await knowledge.run(args.symbol)

    if args.command == "archetype":
        return await archetype.run(args.symbol)

    if args.command == "writer-compare":
        return await writer_compare.run(args.symbol)

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
