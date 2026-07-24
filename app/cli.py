import argparse
import asyncio
from collections.abc import Awaitable, Callable
from typing import NoReturn

from app.commands import (
    decision,
    market,
    morning,
    policy,
    status,
)

CommandHandler = Callable[[], Awaitable[int]]

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
        subparsers.add_parser(
            name,
            help=help_text,
        )

    args = parser.parse_args()

    _, handler = COMMANDS[args.command]
    raise SystemExit(asyncio.run(handler()))


if __name__ == "__main__":
    main()
