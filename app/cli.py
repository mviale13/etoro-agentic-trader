import argparse
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, NoReturn

from app.commands import (
    acquire,
    archetype,
    assessment,
    brain,
    committee,
    committee_judgment,
    committees,
    company,
    considerations,
    credentials,
    crypto_decision,
    crypto_events,
    crypto_market,
    crypto_playbook,
    crypto_quality,
    cycle,
    daily,
    decide,
    decision,
    defect_ledger,
    doctor,
    evaluate,
    explain,
    financials,
    identity_history,
    intelligence,
    intelligence_brief,
    intelligence_journal,
    issuance,
    judge,
    judgment_history,
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
    statement_audit,
    statement_import,
    statement_shape,
    statements,
    status,
    supply,
    today,
    translations,
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

    crypto_decision_parser = subparsers.add_parser(
        "crypto-decision",
        help="What the Artificial CIO concludes about a digital asset",
        description=(
            "The canonical answer, asked rather than computed: the same "
            "decision the crypto dossier renders, the portfolio brief "
            "carries and the research pipeline admits on. Shows the posture, "
            "why, what is established, what is the wrong instrument for this "
            "asset, what is still open and what a later cycle could settle — "
            "each in the words of the layer that established it. Read-only, "
            "no model, no fetch: it prints what `judge` recorded and appends "
            "nothing. No conviction is stated because none exists, and "
            "nothing here is scored, ranked or combined"
        ),
    )
    crypto_decision_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC. Omit for the corpus",
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

    judgment_parser = subparsers.add_parser(
        "committee-judgment",
        help="Show what the Value Capture Committee judges, and from what",
        description=(
            "One committee, one question: does this network generate "
            "evidenced fee activity, and does an evidenced mechanism capture "
            "some of it for the token or its holders? Shows applicability, "
            "eligible evidence and the judgment as three separate steps. "
            "Neither answer is favourable or adverse, no share is banded, and "
            "nothing here is a recommendation"
        ),
    )
    judgment_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example ETH. Omit for the corpus",
    )
    judgment_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show every eligible finding the committee was given",
    )

    assessment_parser = subparsers.add_parser(
        "assessment",
        help="What can usefully be said to an investor about this asset",
        description=(
            "The strongest statement the evidence supports, per subject: a "
            "figure the evidence settles, a bound across estimates, a "
            "structural fact, something true within a stated limit, or an "
            "honest uncertainty. A difference between sources becomes an "
            "uncertainty only where the difference changes what can "
            "responsibly be said, and no figure is ever averaged into one "
            "nobody published. Read-only, no model — and no recommendation, "
            "score or ranking"
        ),
    )
    assessment_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example TAO. Omit for the corpus",
    )

    committees_parser = subparsers.add_parser(
        "committees",
        help="Show what every registered committee has concluded about an asset",
        description=(
            "The independent committee portfolio: for each registered "
            "committee, the question it owns, what it concluded, why, the "
            "confidence it expresses and the evidence beneath it. With a "
            "symbol, one block per committee; without one, the corpus as a "
            "grid. Read-only, no model, no fetch — and nothing is combined: "
            "no overall verdict, no agreement, no score, no ranking, and "
            "confidence is never compared across committees"
        ),
    )
    committees_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example ADA. Omit for the corpus grid",
    )
    committees_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show each committee's own reasoning and the refs it rests on",
    )

    considerations_parser = subparsers.add_parser(
        "considerations",
        help="Show what the committees establish, addressed to an investment layer",
        description=(
            "The decision bridge: each committee's own conclusion carried "
            "forward with its applicability, confidence and the exact "
            "judgment it rests on — and, beside each one, whether this "
            "platform has established what that conclusion means for an "
            "investment case. Today it has not, for any of them, because no "
            "layer has written such a rule. Read-only, no model, no fetch, "
            "and nothing is scored, weighted, ranked or combined"
        ),
    )
    considerations_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example HYPE. Omit for the whole corpus",
    )

    translations_parser = subparsers.add_parser(
        "translations",
        help="Show every governed provider translation and its warrant",
        description=(
            "The boundary between what a provider reported and what this "
            "platform has established: every crossing from an external "
            "field to a domain concept, which of the four questions it "
            "answers (identity, vocabulary, unit, semantic), and the "
            "authority it is performed under. A warrant is authority for "
            "a translation, never confidence in a value. Read-only, no "
            "model, no fetch, and nothing is scored or ranked by trust"
        ),
    )
    translations_parser.add_argument(
        "--markdown",
        action="store_true",
        help="Render the inventory document this registry generates",
    )

    judge_parser = subparsers.add_parser(
        "judge",
        help="Convene the committee and record what it concluded",
        description=(
            "The explicit spend that writes judgment history. Runs the Value "
            "Capture Committee, appends one judgment event to an append-only "
            "record, and states what changed against the last comparable "
            "judgment. Recording is separate from rendering on purpose: a "
            "surface that wrote history would count page views as reviews"
        ),
    )
    judge_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example ETH. Omit for the corpus",
    )

    judgment_history_parser = subparsers.add_parser(
        "judgment-history",
        help="Show how one bounded judgment has moved, and how far to trust it",
        description=(
            "What the committee concluded, when, and what changed since — "
            "with the committee's answer, the observation beneath it and the "
            "evidence itself kept as three separate facts, because evidence "
            "moving under a steady answer is the ordinary case and is not a "
            "changed conclusion. A previous verdict is never restated as "
            "today's. Read-only, no model, and a count of judgments is never "
            "presented as a duration of review"
        ),
    )
    judgment_history_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example ETH. Omit for the corpus",
    )
    judgment_history_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show the record ids, the cited refs and both change axes",
    )

    cycle_parser = subparsers.add_parser(  # noqa: F841
        "cycle",
        help="Run one explicit Daily CIO cycle: acquire, decide, record",
        description=(
            "The explicit daily operating loop: one acquisition, one "
            "canonical decision pass over the active book, and one durable "
            "cycle record — STARTED before the first network action, one "
            "terminal event after orchestration finishes, and a started "
            "cycle with no end rendered as interrupted rather than "
            "relabeled. COMPLETE means every stage ran, never that every "
            "provider answered; refusals stay visible inside it. No "
            "scheduler, no notifications, and it never trades"
        ),
    )

    cycle_parser.add_argument(
        "--candidates",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Also evidence and evaluate up to N watched-but-unheld "
            "securities, recording them ranked by the conviction the "
            "Artificial CIO assigned. Default 0: each candidate costs a "
            "fundamentals request against a rate-limited provider and a "
            "pipeline pass, so a cycle pays for them only when asked. "
            "Recording none means none were evaluated — never that none "
            "is worth holding"
        ),
    )

    identity_history_parser = subparsers.add_parser(
        "identity-history",
        help="Show what each provider has claimed this instrument was, look by look",
        description=(
            "The append-only identity observation stream, oldest first: both "
            "providers' claims verbatim from every explicit funded "
            "acquisition, the standing derived at each capture, and the raw "
            "tenancy fields the payload carried. A past dispute followed by "
            "newer agreement is worded as previously disputed with current "
            "claims agreeing — never as resolved or corrected, because no "
            "resolution evidence class is uniformly available. Read-only, no "
            "model, appends nothing, and historical contradiction is not "
            "decision-bearing"
        ),
    )
    identity_history_parser.add_argument(
        "symbol",
        help="Ticker symbol, for example SE",
    )

    journal_parser = subparsers.add_parser(
        "intelligence-journal",
        help="Show what this platform has observed over time, and how often",
        description=(
            "The append-only record and the deterministic reading of it: how "
            "many times this platform looked, when, the longest it went "
            "without looking, and for each finding whether it is new, "
            "unchanged, changed, no longer produced, or unreadable — with "
            "whether a change was the world moving, the source revising "
            "itself, or this platform's own reading changing. Read-only, no "
            "model, and a count of captures is never presented as a duration "
            "of monitoring"
        ),
    )
    journal_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol, for example BTC. Omit for the corpus",
    )
    journal_parser.add_argument(
        "--evidence",
        action="store_true",
        help="Show the journal entry ids each temporal fact rests on",
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

    statement_audit_parser = subparsers.add_parser(
        "statement-audit",
        help="Re-examine stored statement readings against the filings themselves",
        description=(
            "Ask, of every stored statement reading, whether today's parse "
            "of the same immutable filing could have produced it. A reading "
            "the filing itself refutes — the period header it recorded is "
            "not the one the filer printed, or the row no longer carries "
            "the figure it anchored on — may lose its vote, and stays "
            "stored. Read-only unless --supersede is given; it costs a "
            "fetch, asks no model and reads no score, band or factor"
        ),
    )
    statement_audit_parser.add_argument(
        "symbol",
        nargs="?",
        help="Ticker symbol. Omit to audit every company with stored readings",
    )
    statement_audit_parser.add_argument(
        "--supersede",
        action="store_true",
        help=(
            "Record the withdrawals. Explicit because this is the one "
            "action that removes authority from stored evidence; without "
            "it the audit only reports"
        ),
    )

    statement_import_parser = subparsers.add_parser(
        "statement-import",
        help="Carry statement observations from an isolated store into another",
        description=(
            "Move observations the ordinary acquisition pipeline already "
            "produced — in an isolated evidence root, under this schema — "
            "into another statement store, whole and unaltered, through "
            "the store's ordinary append door. It never observes, never "
            "asks a model, and never rewrites anything: exact duplicates "
            "are skipped and reported, incompatible artifacts are refused "
            "with the reason. Dry-run by default; --apply writes"
        ),
    )
    statement_import_parser.add_argument(
        "source",
        help=(
            "Directory holding statement-store artifacts to import, for "
            "example data/experiments/statement-observations/bq13/statements"
        ),
    )
    statement_import_parser.add_argument(
        "--into",
        help=(
            "Target statements directory. Defaults to this evidence "
            "root's own statement store"
        ),
    )
    statement_import_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Append the new observations. Explicit because this is the "
            "one action that adds evidence without an acquisition; "
            "without it the import only reports"
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

    if args.command == "statement-shape":
        return statement_shape.run(args.symbol)

    if args.command == "statement-audit":
        return statement_audit.run(args.symbol, args.supersede)

    if args.command == "statement-import":
        return statement_import.run(args.source, args.into, args.apply)

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

    if args.command == "crypto-decision":
        return await crypto_decision.run(args.symbol)

    if args.command == "issuance":
        return await issuance.run(args.symbol)

    if args.command == "crypto-intelligence":
        return await intelligence_brief.run(args.symbol, args.evidence)

    if args.command == "crypto-events":
        return await crypto_events.run(args.symbol, args.evidence)

    if args.command == "committee-judgment":
        return await committee_judgment.run(args.symbol, args.evidence)

    if args.command == "assessment":
        return await assessment.run(args.symbol)

    if args.command == "committees":
        return await committees.run(args.symbol, args.evidence)

    if args.command == "considerations":
        return await considerations.run(args.symbol)

    if args.command == "translations":
        return await translations.run(args.markdown)

    if args.command == "judge":
        return await judge.run(args.symbol)

    if args.command == "judgment-history":
        return await judgment_history.run(args.symbol, args.evidence)

    if args.command == "intelligence-journal":
        return await intelligence_journal.run(args.symbol, args.evidence)

    if args.command == "identity-history":
        return await identity_history.run(args.symbol)

    if args.command == "cycle":
        return await cycle.run(candidates=max(0, args.candidates))

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
