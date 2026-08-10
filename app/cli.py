import argparse
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn

from app.commands import (
    acquire,
    archetype,
    brain,
    committee,
    company,
    credentials,
    crypto_events,
    crypto_market,
    crypto_playbook,
    crypto_quality,
    daily,
    decide,
    decision,
    defect_ledger,
    doctor,
    evaluate,
    explain,
    financials,
    intelligence,
    intelligence_brief,
    issuance,
    knowledge,
    market,
    morning,
    observe,
    observe_statements,
    playbook,
    playbook_coverage,
    policy,
    primary,
    reader_defects,
    reader_stability,
    record,
    statement_shape,
    statements,
    status,
    supply,
    today,
    understanding,
    watchlist,
    writer_compare,
)
from app.domain.financial_question import FinancialModel
from app.domain.financial_statements import StatementKind
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

    supply_parser = subparsers.add_parser(
        "supply",
        help="Show what each of a token's supply numbers actually counts",
        description=(
            "Crypto supply is an accounting vocabulary rather than one "
            "number. This shows which quantity each source reports, whose "
            "definition decided it, and whether two figures are a real "
            "disagreement or simply two different facts — two numbers "
            "conflict only if they claim to represent the same thing. "
            "Read-only, and it interprets nothing: dilution is not a word "
            "it knows"
        ),
    )
    supply_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example ADA or HYPE. Omit for the corpus",
    )

    primary_parser = subparsers.add_parser(
        "primary",
        help="Read canonical chain state directly and report what it can settle",
        description=(
            "The evidence-authority experiment: read primary state — "
            "Ethereum's block headers, Hyperliquid's own API, Cardano's "
            "ledger totals, and Bitcoin's fees for contrast — and report "
            "each figure with everything needed to reproduce it. A "
            "measurement of this platform, not of an asset: it costs a "
            "fetch, asks no model, stores nothing and decides nothing"
        ),
    )
    primary_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol: BTC, ETH, ADA or HYPE. Omit for all four",
    )

    crypto_market_parser = subparsers.add_parser(
        "crypto-market",
        help="Show what kind of crypto market an asset is trading inside",
        description=(
            "The crypto environment as the last acquisition cycle read "
            "it — total capitalisation, volume, dominance, breadth — and, "
            "with a symbol, that asset's place in it: its returns, its "
            "peer group and why that group, and the arithmetic between "
            "them at the one interval every side is published at. "
            "Read-only, and nothing here is a verdict: no band, no "
            "traffic light and no regime label"
        ),
    )
    crypto_market_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or HYPE. Omit for the market itself",
    )

    crypto_playbook_parser = subparsers.add_parser(
        "crypto-playbook",
        help=(
            "Show which investment questions a digital asset is asked, "
            "and which it is not"
        ),
        description=(
            "For one token: the archetype and what grounds it, every "
            "investment question with its applicability and the evidence "
            "held against it, the questions declined with the reason each "
            "is the wrong question, and each mapped economic entity's "
            "value chain from use to the token. With no symbol: the same "
            "applicability as a matrix over the corpus. Read-only — "
            "nothing is fetched, asked of a model or stored, and nothing "
            "here is an answer"
        ),
    )
    crypto_playbook_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or HYPE. Omit for the corpus matrix",
    )

    crypto_quality_parser = subparsers.add_parser(
        "crypto-quality",
        help=(
            "Show which durable qualities of a digital asset this "
            "platform can judge today"
        ),
        description=(
            "For one token: the quality band or the honest absence of "
            "one, the evidence coverage beneath it, and every applicable "
            "question with how it participated — scored against a named "
            "rule, shown with its standing and not scored, or not yet "
            "answerable with what would answer it. With no symbol: the "
            "question readiness table and the corpus as a matrix. "
            "Read-only — nothing is fetched, asked of a model or stored"
        ),
    )
    crypto_quality_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or HYPE. Omit for the corpus matrix",
    )

    issuance_parser = subparsers.add_parser(
        "issuance",
        help="Show how new supply enters a digital asset's system",
        description=(
            "For one token: the mechanism that creates new supply, every "
            "parameter with the surface it was read from, what could "
            "change the rule, and what the rule implies from here — "
            "MOVRvest's arithmetic under the currently observed policy, "
            "never a forecast. For an asset whose supply arrives by "
            "allocation release, the specific evidence that is missing. "
            "Without a symbol: the corpus. Nothing here is scored"
        ),
    )
    issuance_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or ADA. Omit for the corpus",
    )

    brief_parser = subparsers.add_parser(
        "crypto-intelligence",
        help="Show what is happening to a digital asset, and why it matters",
        description=(
            "What changed, what appears to be driving it, what is "
            "supportive and what is adverse, how it sits against the "
            "market, and what to watch — each line labelled as a "
            "measurement, a reported fact, an attributed view or this "
            "platform's own reading. Independent of Asset Quality, and "
            "it changes no recommendation"
        ),
    )
    brief_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or ETH. Omit for the corpus",
    )
    brief_parser.add_argument(
        "--evidence",
        action="store_true",
        help=(
            "Show the claim each driver rests on, and what each claim "
            "does not establish"
        ),
    )

    events_parser = subparsers.add_parser(
        "crypto-events",
        help="Show the developments held for a digital asset, and their sources",
        description=(
            "Every current development this platform holds for an asset, "
            "deduplicated across the surfaces that reported it: what each "
            "account asserts, what it merely reads into things, which "
            "figures a second source independently carries, and how close "
            "to the event the reporting gets. Read-only — it serves what "
            "`movrvest acquire` stored and fetches nothing"
        ),
    )
    events_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC or HYPE. Omit for the corpus",
    )
    events_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show every source's link and the event's identity key",
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
    statements_parser.add_argument(
        "--statement",
        choices=[kind.value for kind in StatementKind],
        default=StatementKind.INCOME_STATEMENT.value,
        help=(
            "Which primary statement to show. Three quorums share a "
            "document key and are never pooled, so one is asked for at a time"
        ),
    )

    financials_parser = subparsers.add_parser(
        "financials",
        help="Show what the filer's statements measure, and the analysts on them",
        description=(
            "The canonical financial facts a filing establishes — every "
            "measure with the cells it was computed from and the narrowest "
            "agreement beneath it — and the four financial analysts' answers "
            "over exactly those facts. Read-only: it derives from what is "
            "stored and never observes"
        ),
    )
    financials_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example JPM",
    )
    financials_parser.add_argument(
        "--model",
        choices=[model.value for model in FinancialModel],
        default=None,
        help=(
            "Ask another financial interpretation model's questions of the "
            "same facts. Inspection only: which model governs is derived "
            "from the business playbook, and this never changes that"
        ),
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
    observe_statements_parser.add_argument(
        "--statement",
        choices=[kind.value for kind in StatementKind],
        default=StatementKind.INCOME_STATEMENT.value,
        help=(
            "Which primary statement to observe. Each is its own quorum and "
            "its own spend"
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

    acquire_parser = subparsers.add_parser(
        "acquire",
        help="Read the market for the whole book, and fill the store pages serve from",
        description=(
            "Price every holding, the research candidates and the market "
            "strip in one reading, and store what came back. Every surface "
            "serves what this left behind and reaches no provider itself, "
            "so this is the act that makes a page current — and the one "
            "place a rate limit is spent"
        ),
    )
    acquire_parser.add_argument(
        "--candidates",
        type=int,
        default=acquire.DEFAULT_CANDIDATE_BUDGET,
        help=(
            "How many watched-but-unheld securities to price. The research "
            "page's own default, so the page it serves finds every security "
            "it evidences already priced"
        ),
    )

    statement_shape_parser = subparsers.add_parser(
        "statement-shape",
        help="Show what shape a filer's own statements have, and whose each absence is",
        description=(
            "Measure the shape of a company's primary statements: which "
            "figures the filer prints a line for, which it prints under a "
            "label this platform does not read, and which statement was "
            "never located. A measurement of this platform, not of the "
            "company: it costs a fetch, asks no model and stores nothing"
        ),
    )
    statement_shape_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example JPM",
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

    if args.command == "statement-shape":
        return statement_shape.run(args.symbol)

    if args.command == "observe":
        return await observe.run(args.symbol, args.to)

    if args.command == "acquire":
        return await acquire.run(args.candidates)

    if args.command == "statements":
        return await statements.run(args.symbol, StatementKind(args.statement))

    if args.command == "financials":
        return await financials.run(
            args.symbol,
            FinancialModel(args.model) if args.model else None,
        )

    if args.command == "observe-statements":
        return await observe_statements.run(
            args.symbol, args.to, StatementKind(args.statement)
        )

    if args.command == "understanding":
        return await understanding.run(args.symbol)

    if args.command == "decide":
        return await decide.run(args.symbol, args.question)

    if args.command == "playbook":
        return await playbook.run(args.symbol)

    if args.command == "supply":
        return await supply.run(args.symbol)

    if args.command == "primary":
        return await primary.run(args.symbol)

    if args.command == "crypto-market":
        return await crypto_market.run(args.symbol)

    if args.command == "crypto-playbook":
        return await crypto_playbook.run(args.symbol)

    if args.command == "crypto-quality":
        return await crypto_quality.run(args.symbol)

    if args.command == "issuance":
        return await issuance.run(args.symbol)

    if args.command == "crypto-intelligence":
        return await intelligence_brief.run(args.symbol, args.evidence)

    if args.command == "crypto-events":
        return await crypto_events.run(args.symbol, args.evidence)

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
