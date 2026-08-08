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
    decide,
    decision,
    defect_ledger,
    doctor,
    evaluate,
    explain,
    intelligence,
    knowledge,
    market,
    morning,
    observe,
    observe_statements,
    playbook,
    playbook_coverage,
    policy,
    reader_defects,
    reader_stability,
    record,
    statements,
    status,
    today,
    understanding,
    watchlist,
    writer_compare,
)
from app.services.reader_calibration import DEFAULT_READINGS

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

    understanding_parser = subparsers.add_parser(
        "understanding",
        help="Explain how a business creates value, from consensus knowledge",
        description=(
            "Derive, deterministically, how a business creates value from "
            "its consensus knowledge: the economic engine, the revenue "
            "mechanisms with their support, the archetype with what it "
            "rests on, and what could change the conclusion. No model is "
            "asked and nothing is read"
        ),
    )
    understanding_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, NVDA or CAT",
    )

    decide_parser = subparsers.add_parser(
        "decide",
        help="Ask the platform one investment question about one security",
        description=(
            "Answer one explicit question — entry, increase, decrease, or "
            "research_spend — with a canonical investment decision: a "
            "constitutional verdict or a worded refusal, its basis, its "
            "clauses with their edges, and the implications weighed with "
            "the losers preserved. Appends one event to the append-only "
            "(subject, question) stream; the current stance is always the "
            "latest answer"
        ),
    )
    decide_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example JPM",
    )
    decide_parser.add_argument(
        "question",
        help="One of: entry, increase, decrease, research_spend",
    )

    playbook_parser = subparsers.add_parser(
        "playbook",
        help="Show which playbook analyses a business, and what decided it",
        description=(
            "Select the investment playbook under the migration rule: from "
            "quorate business understanding where the mapping has earned "
            "the conclusion, otherwise from the reported industry — "
            "recorded as fallback, with the grounded route's refusal "
            "stated. The two routes never blend"
        ),
    )
    playbook_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, NVDA or CAT",
    )

    subparsers.add_parser(
        "playbook-coverage",
        help="Measure the grounded selector over the portfolio and watchlists",
        description=(
            "A read-only measurement: for every held or watched security, "
            "the stored knowledge width, the selector outcome, and — for "
            "every company without an authoritative grounded playbook — "
            "exactly one blocking claim. Nothing is acquired, fetched or "
            "read"
        ),
    )

    subparsers.add_parser(
        "reader-defects",
        help="Classify every reader-blocked claim in the store, with counts",
        description=(
            "The reader defect taxonomy: every absent claim's stored "
            "reason classified against the knowledge layer's own "
            "templates, counted by structural cause. The measurement that "
            "decides whether reader work is earned — a cause shared by "
            "several companies is a pattern; anything narrower stays a "
            "backlog entry. Read-only; nothing is acquired or fixed"
        ),
    )

    subparsers.add_parser(
        "defect-ledger",
        help="Show every defect pattern's history: cost, dates, status",
        description=(
            "The reader defect ledger: the store's readings replayed in "
            "the order they were taken, so every defect pattern carries "
            "when it first appeared, when a reading last found it, how "
            "many claims it has ever blocked, and whether a rerun still "
            "finds it. A PR that claims a resolution is credited only "
            "where the rerun agrees. Read-only; nothing is acquired, "
            "stored or fixed"
        ),
    )

    statements_parser = subparsers.add_parser(
        "statements",
        help="Show the figures the filer's own statements settled, with widths",
        description=(
            "The consensus over stored statement observations of the current "
            "filing: every concept with its width, cell, printed figure and "
            "caption, and every absence with its reason. The figures are the "
            "filer's, at addresses this platform checked; nothing here is "
            "derived or estimated"
        ),
    )
    statements_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example JPM",
    )

    observe_statements_parser = subparsers.add_parser(
        "observe-statements",
        help="Read the current filing's statements again, up to the quorum",
        description=(
            "Take independent statement observations of a company's current "
            "document until the quorum is reached, and show the consensus "
            "they derive. The stopping rule is the count, never the content"
        ),
    )
    observe_statements_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example JPM",
    )
    observe_statements_parser.add_argument(
        "--to",
        type=int,
        default=None,
        help=(
            "Observe up to this many observations instead of the quorum — "
            "a deeper, explicit spend. The count is fixed before anything "
            "is read; the content never moves it"
        ),
    )

    observe_parser = subparsers.add_parser(
        "observe",
        help="Read the current filing again, up to the consensus quorum",
        description=(
            "Take independent observations of a company's current document "
            "until the quorum is reached, and show the consensus they "
            "derive. The stopping rule is the count, never the content"
        ),
    )
    observe_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, NVDA or VOW3.DE",
    )
    observe_parser.add_argument(
        "--to",
        type=int,
        default=None,
        help=(
            "Observe up to this many observations instead of the quorum — "
            "a deeper, explicit spend. The count is fixed before anything "
            "is read; the content never moves it"
        ),
    )

    reader_stability_parser = subparsers.add_parser(
        "reader-stability",
        help="Read one filing repeatedly and report how far the readings agree",
        description=(
            "Read a company's current document several times under identical "
            "conditions and report where the readings agreed and where they "
            "did not. A measurement of this platform, not of the company: "
            "nothing is stored, and no reading is improved"
        ),
    )
    reader_stability_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example DIS, NVDA or VOW3.DE",
    )
    reader_stability_parser.add_argument(
        "--readings",
        type=int,
        default=DEFAULT_READINGS,
        help=(
            f"How many independent readings to run (default {DEFAULT_READINGS}). "
            "Each one costs a model call and reads the same document"
        ),
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

    if args.command == "reader-stability":
        return await reader_stability.run(args.symbol, args.readings)

    if args.command == "observe":
        return await observe.run(args.symbol, args.to)

    if args.command == "statements":
        return await statements.run(args.symbol)

    if args.command == "observe-statements":
        return await observe_statements.run(args.symbol, args.to)

    if args.command == "understanding":
        return await understanding.run(args.symbol)

    if args.command == "decide":
        return await decide.run(args.symbol, args.question)

    if args.command == "playbook":
        return await playbook.run(args.symbol)

    if args.command == "playbook-coverage":
        return await playbook_coverage.run()

    if args.command == "reader-defects":
        return await reader_defects.run()

    if args.command == "defect-ledger":
        return await defect_ledger.run()

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
