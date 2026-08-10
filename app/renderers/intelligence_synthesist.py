"""Ask a model to read the evidence, then trust only what survives.

The Executive Writer's architecture, a different job. Same provider
seam, same `NarrativeFinding` as the model's entire world, same
fail-closed validation, same worded absence — **a different trust model
was never on the table**, and the prompt and schema are the only things
that differ.

What is new is the validator, and it is the slice. The writer's
grounding rule was *cite a finding that exists*; this one has to be
harder, because the model here is being asked to **connect** evidence
rather than restate it, and connecting is exactly where a language model
invents. So five rules, each refusing a specific way a plausible
sentence can be wrong:

```text
references   a ref not supplied              → reject
figures      a number not in the evidence     → reject
entities     a name not in the evidence       → reject
causality    a causal verb with no attributed cause → reject
actions      BUY / SELL / RECOMMEND / MONITOR → reject
```

**Refused, not requested.** The PR #95 lesson, applied before it could
be relearned: the writer was politely asked not to discuss sizing and
discussed sizing. Every rule above is enforced on the draft, and the
prompt merely explains rules the validator will apply anyway.

**The figures rule reuses the event layer's own normaliser.** A model
writing *"$1.6 billion"* over evidence that says *"$1.6bn"* is quoting
the evidence, and `anchors_in` already knows they are one figure — it
was built to recognise two outlets reporting one event, and recognising
a model quoting one claim is the same problem.

**A rejected draft is a whole rejected draft.** No sentence is quietly
deleted and the remainder presented as checked. That is the Executive
Writer's contract and there is no second one.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.domain.crypto_event import anchors_in
from app.domain.crypto_intelligence import CryptoIntelligenceSnapshot
from app.domain.executive_narrative import NarrativeFinding
from app.domain.intelligence_journal import TemporalFact
from app.domain.intelligence_synthesis import (
    MAX_THEME_WORDS,
    SynthesisItem,
)
from app.domain.judgment_history import JudgmentTransition
from app.providers.narrative_provider import (
    DraftRequest,
    NarrativeDeclined,
    NarrativeProvider,
)

#: Words per statement beyond which a draft is refused. A synthesis is
#: shorter than the evidence it reads or it is not a synthesis.
MAX_ITEM_WORDS = 45

#: How many statements each section may carry, from the ruling: two to
#: four things that matter, and one to three worth watching.
MAX_WHAT_MATTERS = 4
MAX_WHY = 4
MAX_WATCH = 3

#: How much room a draft gets. Same shape as the Executive Writer's
#: budget and the same reason: current models spend reasoning tokens out
#: of it, so the ceiling leaves room to think and to write.
MAX_DRAFT_TOKENS = 12000

#: The Artificial CIO's own verdict words. Forbidden **as verdicts** —
#: in capitals, or as a directive aimed at the reader.
#:
#: Not forbidden as ordinary English, which was the first draft's error:
#: it rejected *"these funds already hold 1,223,634 BTC"* and *"whether
#: fee revenue holds"*, two plain descriptions of evidence, because
#: `hold` is also a recommendation. A rule that cannot tell a verb from
#: a verdict fails on the correct drafts and teaches nothing about the
#: wrong ones.
VERDICT_WORDS = (
    "buy",
    "sell",
    "hold",
    "recommend",
    "prepare",
    "investigate",
    "monitor",
    "reject",
    "accumulate",
    "divest",
    "overweight",
    "underweight",
)

#: How a verdict actually appears in prose: aimed at somebody.
_DIRECTIVE = re.compile(
    r"\b(should|must|ought to|investors?|holders? should|we|one)\s+"
    r"(?:now\s+|therefore\s+)?(" + "|".join(VERDICT_WORDS) + r")\b",
    re.I,
)

#: Advice this platform does not give at all, in any grammatical form.
#: `PortfolioBriefing`'s standing rule — no size, price or quantity is
#: ever suggested — which the Executive Writer had to learn to refuse
#: rather than request.
FORBIDDEN_ADVICE = (
    "position size",
    "position sizing",
    "entry criteria",
    "take profit",
    "stop loss",
    "price target",
    "risk controls",
)

#: Verbs that assert one thing produced another. Permitted **only** in a
#: sentence that names the source the causal reading came from, which is
#: what turns *"ETF inflows supported Bitcoin"* into *"CoinGecko
#: attributes support to ETF inflows"*.
CAUSAL_VERBS = (
    "caused",
    "drove",
    "driven by",
    "pushed",
    "led to",
    "leading to",
    "resulted in",
    "resulting in",
    "triggered",
    "sparked",
    "fuelled",
    "fueled",
    "sent ",
    "lifted",
    "dragged",
    "boosted",
    "propelled",
    "because of",
    "due to",
    "as a result of",
    "thanks to",
    "prevented",
    "kept the price",
    "supported the price",
    "underpinned",
    "weighed on",
)

#: The causal verbs, matched on **word boundaries**.
#:
#: A bare substring test was wrong and quietly so: `sent ` matches
#: inside *"absent "* and *"present "*, so a correct sentence about
#: absent evidence was refused for asserting a cause. A guard that fires
#: on the wrong sentence teaches a reader to distrust the guard.
_CAUSAL = re.compile(
    r"(?<![\w-])(?:" + "|".join(re.escape(v.strip()) for v in CAUSAL_VERBS) + r")\b",
    re.I,
)

#: Relational wording the ruling explicitly permits. Listed so the
#: prompt can offer an alternative rather than only a prohibition — a
#: model told what it may not write and not what it may writes nothing.
PERMITTED_RELATIONAL = (
    "coincided with",
    "occurred alongside",
    "provides a supportive signal",
    "provides an adverse signal",
    "may matter because",
    "is consistent with",
)

#: Crypto concepts a model knows and the evidence may not have said.
#:
#: The entity rule below catches fabricated *names*, because names are
#: capitalised. It cannot catch a fabricated *concept*, because concepts
#: are ordinary lowercase nouns — and "Bitcoin has a 21 million cap",
#: "Ethereum moved to proof of stake" and "Hyperliquid buys back HYPE"
#: are exactly the kind of true-but-unsupplied sentence a model reaches
#: for when the evidence is thin.
#:
#: So they are guarded by name: each may appear only where a supplied
#: finding uses it. A short, specific list beats a general one — this is
#: the same shape as the Executive Writer's `FORBIDDEN_LANGUAGE`, which
#: refuses six phrases rather than modelling all bad writing.
GUARDED_CONCEPTS = (
    "halving",
    "proof of stake",
    "proof of work",
    "buyback",
    "buy back",
    "buys back",
    "max supply",
    "maximum supply",
    "hard cap",
    "fixed cap",
    "21 million",
    "21m",
    "burn",
    "staking",
    "validator",
    "the merge",
    "fork",
    "mining",
    "hashrate",
    "issuance",
    "inflation",
    "unlock",
    "vesting",
    "smart contract",
    "layer 2",
    "rollup",
)

#: Ordinary English, for the one position where capitalisation proves
#: nothing: the start of a sentence.
#:
#: The rule went wrong twice in opposite directions, and both are worth
#: recording because the second is the dangerous one.
#:
#: Checking every capitalised token rejected *"Operational signals are
#: cautious"*, *"Divergent institutional actions…"* and *"Because perps
#: fees are…"* — three ordinary sentences refused for their first word.
#:
#: Exempting the first word entirely then let **"Coinbase led the
#: buying."** through, which is precisely the fabricated entity the rule
#: exists to catch. A hole at the start of every sentence is a hole a
#: model will find, because that is where it puts the subject.
#:
#: So a sentence-initial token must be ordinary English *or* supplied.
#: The list below is what "ordinary English" means here: function words,
#: auxiliaries, and the analytical vocabulary this layer actually
#: writes in. It is a word list, not a language model, and its failure
#: mode is safe — an unlisted ordinary word costs a draft, while an
#: unlisted name is caught.
_ORDINARY = {
    "a",
    "an",
    "the",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "and",
    "or",
    "but",
    "if",
    "while",
    "although",
    "though",
    "however",
    "no",
    "not",
    "none",
    "nothing",
    "both",
    "each",
    "every",
    "all",
    "one",
    "two",
    "three",
    "four",
    "five",
    "several",
    "many",
    "most",
    "there",
    "then",
    "when",
    "where",
    "whether",
    "what",
    "which",
    "who",
    "how",
    "why",
    "so",
    "such",
    "since",
    "until",
    "with",
    "without",
    "over",
    "under",
    "across",
    "against",
    "between",
    "within",
    "during",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "to",
    "up",
    "large",
    "larger",
    "largest",
    "small",
    "smaller",
    "net",
    "new",
    "recent",
    "current",
    "same",
    "other",
    "another",
    "further",
    "still",
    "they",
    "their",
    "them",
    "he",
    "she",
    "we",
    "you",
    "his",
    "her",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
    "can",
    "could",
    "may",
    "might",
    "must",
    "should",
    "would",
    "will",
    "shall",
    "signals",
    "signal",
    "evidence",
    "flows",
    "flow",
    "holders",
    "holder",
    "supply",
    "demand",
    "price",
    "market",
    "network",
    "security",
    "regulatory",
    "institutional",
    "mixed",
    "positive",
    "negative",
    "sessions",
    "session",
    "days",
    "day",
    "month",
    "week",
    # Determiners, pronouns, conjunctions, prepositions, auxiliaries.
    "about",
    "above",
    "after",
    "again",
    "along",
    "already",
    "also",
    "always",
    "among",
    "amid",
    "any",
    "around",
    "as",
    "because",
    "before",
    "behind",
    "below",
    "beside",
    "besides",
    "beyond",
    "despite",
    "either",
    "else",
    "even",
    "far",
    "few",
    "given",
    "here",
    "instead",
    "less",
    "like",
    "meanwhile",
    "much",
    "near",
    "neither",
    "next",
    "now",
    "off",
    "once",
    "only",
    "onto",
    "out",
    "per",
    "rather",
    "some",
    "than",
    "through",
    "throughout",
    "thus",
    "together",
    "toward",
    "towards",
    "unless",
    "unlike",
    "versus",
    "via",
    "well",
    "yet",
    "whereas",
    "wherever",
    "whenever",
    "whose",
    "whom",
    # Analytical vocabulary this layer writes in.
    "absent",
    "activity",
    "adverse",
    "aggregate",
    "alongside",
    "attributed",
    "available",
    "balance",
    "behaviour",
    "behavior",
    "broad",
    "capital",
    "channel",
    "channels",
    "claims",
    "clear",
    "coincident",
    "combined",
    "commentary",
    "companies",
    "company",
    "competing",
    "concentrated",
    "conflicting",
    "consistent",
    "context",
    "corporate",
    "corroborated",
    "corroboration",
    "confirmation",
    "conviction",
    "custody",
    "distribution",
    "governance",
    "holdings",
    "issuers",
    "peers",
    "positioning",
    "provenance",
    "settlement",
    "treasuries",
    "treasury",
    "vehicles",
    "venues",
    "visibility",
    "counts",
    "coverage",
    "daily",
    "data",
    "developments",
    "development",
    "direction",
    "directional",
    "disclosed",
    "dispersion",
    "disputed",
    "divergent",
    "diverging",
    "downside",
    "drawdown",
    "economics",
    "elevated",
    "established",
    "exposure",
    "fees",
    "figures",
    "float",
    "fund",
    "funds",
    "growth",
    "identifiable",
    "impact",
    "incident",
    "incidents",
    "independent",
    "inflow",
    "inflows",
    "interest",
    "level",
    "levels",
    "liquidity",
    "material",
    "materially",
    "measured",
    "mechanism",
    "monthly",
    "moves",
    "movement",
    "networks",
    "observed",
    "offsetting",
    "ongoing",
    "operational",
    "opposing",
    "outflow",
    "outflows",
    "ownership",
    "participation",
    "performance",
    "persistence",
    "persistent",
    "perspective",
    "protocol",
    "public",
    "readings",
    "reading",
    "relative",
    "reported",
    "reports",
    "revenue",
    "risk",
    "risks",
    "rules",
    "sales",
    "selling",
    "short",
    "significance",
    "sources",
    "steady",
    "structural",
    "structure",
    "supportive",
    "sustained",
    "tension",
    "token",
    "tokens",
    "total",
    "trading",
    "trend",
    "unresolved",
    "upside",
    "usage",
    "value",
    "venue",
    "volume",
    "weaker",
    "weakness",
    "wider",
    "windows",
    "window",
    "substantial",
    "sizable",
    "sizeable",
    "modest",
    "strong",
    "stronger",
    "broader",
    "narrower",
    "notable",
    "meaningful",
    "limited",
    "partial",
    "full",
    "partially",
    "fully",
    "largely",
    "mostly",
    "slightly",
    "marginal",
    "marginally",
    "moderate",
    "moderately",
    "heavily",
    "briefly",
    "early",
    "late",
    "later",
    "earlier",
    "continued",
    "continuing",
    "repeated",
    "recurring",
    "overall",
    "separately",
    "absolute",
    "absolutely",
    "apparent",
    "apparently",
    "unlikely",
    "possible",
    "possibly",
    "probable",
    "probably",
    "clearly",
    "unclear",
    "uncertain",
    "certain",
    "notably",
    "particularly",
    "especially",
    "importantly",
    "critically",
    "crucially",
    "significantly",
    "additionally",
    "moreover",
    "furthermore",
    "consequently",
    "accordingly",
    "therefore",
    "similarly",
    "conversely",
    "alternatively",
    "otherwise",
    "nonetheless",
    "nevertheless",
    "regardless",
    "whilst",
    "dispersed",
    "transient",
    "temporary",
    "durable",
    "convergent",
    "aligned",
    "inconsistent",
    "comparable",
    "different",
    "similar",
    "identical",
    "neutral",
    "favourable",
    "favorable",
    "unfavourable",
    "unfavorable",
    "constructive",
    "cautious",
    "retail",
    "sovereign",
    "technical",
    "fundamental",
    "mechanical",
    "increasing",
    "decreasing",
    "rising",
    "falling",
    "growing",
    "shrinking",
    "expanding",
    "sustaining",
    "reduced",
    "depressed",
    "subdued",
    "muted",
    "newer",
    "newest",
    "older",
    "currently",
    "key",
    "main",
    "primary",
    "secondary",
    "central",
    "core",
    "peripheral",
    "various",
    "numerous",
    "multiple",
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "final",
    "last",
    "previous",
    "prior",
    "robust",
    "healthy",
    "impressive",
    "resilient",
    "thin",
    "shallow",
    "deep",
    "wide",
    "narrow",
    "flat",
}

SYSTEM_PROMPT = """\
You are the intelligence analyst of MOVRvest, an investment platform
whose evidence gathering is already finished before you are called.

You are synthesising an investment-intelligence packet. You are not
researching, and you have no sources beyond the findings supplied.

Rules:
- Use ONLY the supplied findings. Your universe is that list.
- Never invent a fact, a number, a name or a date. If a figure is not
  in a finding, it does not exist.
- Quote every figure EXACTLY as the finding writes it. Do not round it,
  rescale it, or reformat it: if a finding says 5,610,842 ETH, write
  5,610,842 ETH and never 5.61m. Rounding produces a number nobody
  measured, and the draft will be refused for it.
- Keep each figure's unit attached: write 0.11% and not 0.11, $128m and
  not 128. A number without its unit is a different number.
- Do not compute anything. No totals, no differences, no ratios, no
  percentages of your own. Arithmetic is done before you are called.
- Never mention a company, protocol, product, regulator, fund or person
  that is not named in a finding. You may know a great deal about these
  assets; none of it is admissible here.
- Never state that something caused a price move. You may say two things
  coincided, occurred alongside one another, are consistent with each
  other, or that a development may matter because of some other supplied
  fact.
- Where a finding says a SOURCE interprets something as causal, you may
  report that attribution and must name the source: write "CoinGecko
  attributes support to ETF inflows", never "ETF inflows supported the
  price". The attribution is part of the evidence.
- Never give an investment recommendation, and never use the words buy,
  sell, hold, recommend, prepare, investigate, monitor or reject.
- Never invent a score, a rating, a confidence or a percentage.
- CONNECT related findings rather than repeating them one by one. Three
  separate sales by three holders are one observation about holder
  behaviour. That connection is the reason you were called.
- Prioritise by what matters to an investor, not by the order supplied.
- Where the evidence points in opposite directions, say so and explain
  the tension. Do not force one conclusion.
- Every statement must list the ids of the findings it rests on.
- Cite ids only in the refs field, never inside the statement text.
- At most 45 words per statement. Be concrete.
"""


class SynthesisRejected(Exception):
    """A draft failed grounding, with the reason worded."""


# ── the model's world ───────────────────────────────────────────────


def build_findings(
    snapshot: CryptoIntelligenceSnapshot,
    history: tuple[TemporalFact, ...] = (),
    judgments: tuple[JudgmentTransition, ...] = (),
) -> tuple[NarrativeFinding, ...]:
    """Word the snapshot as numbered findings — nothing else is supplied.

    Every group is prefixed so a reader of a citation can tell what kind
    of thing was cited without looking it up: `C` a measured or reported
    claim, `E` a development, `A` an attributed reading, `R` relative
    market context, `F` durable foundation, `T` an unresolved tension,
    `W` a deterministic watch item, `H` what the record says over time,
    and `J` a committee judgment that changed.
    """

    findings: list[NarrativeFinding] = []

    def add(prefix: str, rows: list[tuple[str, str]]) -> None:
        for index, (statement, source) in enumerate(rows, start=1):
            findings.append(
                NarrativeFinding(
                    id=f"{prefix}{index}",
                    statement=statement,
                    source=source,
                )
            )

    events = {event.identity for event in snapshot.events}

    add(
        "C",
        [
            (
                claim.stated,
                f"{claim.claim_type.stated} — {claim.source} "
                f"({claim.relevance.stated.lower()})",
            )
            for claim in snapshot.live
            if claim.ref not in events
        ],
    )

    add(
        "E",
        [
            (
                f"{event.family.stated}: {event.headline}"
                + (
                    f" — reported by {len(event.sources)} sources"
                    if event.is_multi_source
                    else f" — reported by {event.sources[0]}"
                )
                + (
                    f", and still {event.status.stated}"
                    if event.status.value != "completed"
                    else ""
                ),
                f"Development, {event.tier.stated}"
                + (f", {event.at:%-d %B}" if event.at else ""),
            )
            for event in snapshot.events
        ],
    )

    # Attributed readings, each carrying its author. The model may
    # report these and must name the source; it may never restate one
    # as this platform's own view.
    add(
        "A",
        [
            (
                f"{narrative.source} states: “{narrative.stated}”",
                (
                    "Attributed interpretation — a causal claim by its "
                    "author, not established here"
                    if narrative.is_causal
                    else "Attributed interpretation — its author's view"
                ),
            )
            for narrative in snapshot.narratives[:8]
        ],
    )

    add(
        "R",
        [
            (line, "MOVRvest arithmetic over two aligned intervals")
            for line in snapshot.relative_context
        ],
    )

    add(
        "F",
        [
            (line, "Durable understanding — context, not news")
            for line in snapshot.foundation.lines
        ],
    )

    add("T", [(line, "Unresolved tension") for line in snapshot.conflicting])

    add(
        "W",
        [
            (f"{item.stated} Measured by: {item.measured_by}", "Open question")
            for item in snapshot.watch_next
        ],
    )

    # What the record says, and only what it says. Each carries its own
    # journal entry ids, so a temporal claim in the synthesis is
    # checkable against the observations that produced it — the model
    # does not inspect history and decide what a trend is. **Code
    # establishes history; the model explains grounded history.**
    add(
        "H",
        [
            (
                fact.stated,
                (
                    f"Journal — {fact.status.stated}, from "
                    f"{len(fact.entry_ids)} recorded observation(s): "
                    + ", ".join(fact.entry_ids[-3:])
                ),
            )
            for fact in history
        ],
    )

    # What a committee concluded, and how that differs from the last
    # comparable judgment. **Code establishes the transition; the model
    # explains it** — the same division the `H` group rests on, applied
    # one layer up. A transition is supplied only where the projection
    # already decided one, so the model can word *"the committee now
    # finds a mechanism where the previous comparable judgment found
    # none"* and can never be the thing that noticed.
    add(
        "J",
        [
            (
                transition.stated,
                (
                    f"Committee judgment — {transition.remit.stated}, "
                    f"{transition.change.value}, from "
                    f"{len(transition.record_ids)} recorded judgment(s): "
                    + ", ".join(transition.record_ids)
                ),
            )
            for transition in judgments
        ],
    )

    return tuple(findings)


def synthesis_schema() -> dict[str, Any]:
    """The structured-output contract the synthesist must fill."""

    item = {
        "type": "object",
        "properties": {
            "stated": {"type": "string"},
            "theme": {
                "type": "string",
                "description": (
                    "A short label for what this groups, at most five "
                    "words. Your own words; nothing stores it."
                ),
            },
            "refs": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["stated", "theme", "refs"],
        "additionalProperties": False,
    }

    return {
        "type": "object",
        "properties": {
            "what_matters": {"type": "array", "items": item},
            "why_it_matters": {"type": "array", "items": item},
            "watch_next": {"type": "array", "items": item},
        },
        "required": ["what_matters", "why_it_matters", "watch_next"],
        "additionalProperties": False,
    }


def user_prompt(
    symbol: str,
    findings: tuple[NarrativeFinding, ...],
) -> str:
    lines = [
        f"Asset: {symbol}",
        "",
        "Findings — the only facts you may use. Cite ids per statement:",
    ]

    lines.extend(
        f"[{finding.id}] ({finding.source}) {finding.statement}" for finding in findings
    )

    lines += [
        "",
        f"Produce: what_matters (2-{MAX_WHAT_MATTERS} statements connecting "
        "related findings into what matters most to an investor right now), "
        f"why_it_matters (up to {MAX_WHY} statements explaining the investor "
        "relevance, using durable context where it helps explain a current "
        f"development), and watch_next (1-{MAX_WATCH} conditions or open "
        "questions most likely to change this view).",
        "",
        "Do not invent a future date. Where nothing scheduled is known, "
        "give a measurable condition on evidence already supplied.",
    ]

    return "\n".join(lines)


# ── the validator ───────────────────────────────────────────────────


#: Calendar and reporting periods. Capitalised, and not entities.
#:
#: The evidence says *"in First Half 2026"* and a model writes *"H1"* —
#: an abbreviation, not a company. Left out, the entity rule refused a
#: correct restatement of a supplied date.
_PERIODS = {
    "h1",
    "h2",
    "q1",
    "q2",
    "q3",
    "q4",
    "fy",
    "ytd",
    "yoy",
    "qoq",
    "mom",
    "24h",
    "7d",
    "30d",
    "1h",
    "utc",
}

#: Months, in both the forms a date is written in. The evidence prints
#: "7 August"; a model restating it writes "Aug 7", and neither is a
#: fabricated entity.
_MONTHS = {
    month
    for full, short in (
        ("january", "jan"),
        ("february", "feb"),
        ("march", "mar"),
        ("april", "apr"),
        ("may", "may"),
        ("june", "jun"),
        ("july", "jul"),
        ("august", "aug"),
        ("september", "sep"),
        ("october", "oct"),
        ("november", "nov"),
        ("december", "dec"),
    )
    for month in (full, short)
}


def _stems(word: str) -> set[str]:
    """A word and the plainer forms of it, for vocabulary comparison.

    Deliberately crude. The evidence says *"Staked Supply"* and a model
    writes *"Staking"*; it says *"ETFs"* and the model writes *"ETF"*.
    Those are the same word for this purpose, and a rule that called
    them different rejected correct drafts. It cannot over-admit much:
    no suffix of a fabricated name stems to a supplied one.
    """

    base = word.lower().strip(".'’-")

    forms = {base}

    # A hyphenated compound is its parts: "Short-term" is "short" and
    # "term", both ordinary, and neither is a name.
    if "-" in base:
        forms.update(part for part in base.split("-") if part)

    # A possessive is stripped whatever the word's length: `Elfa AI’s`
    # tokenises to `AI’s`, and a guard requiring three letters left over
    # refused a name the evidence had supplied.
    for suffix in ("'s", "’s", "'"):
        if base.endswith(suffix) and len(base) > len(suffix):
            forms.add(base[: -len(suffix)])

    for suffix in ("s", "es", "ed", "ing"):
        if base.endswith(suffix) and len(base) > len(suffix) + 2:
            forms.add(base[: -len(suffix)])

    for extra in ("s", "es", "ed", "ing"):
        forms.add(base + extra)

    return forms


def _looks_like_a_name(token: str, following: str) -> bool:
    """Whether a sentence's first word is shaped like a proper noun.

    The rule mid-sentence is strict: any capitalised word must be
    supplied. At the start of a sentence that rule cannot work, because
    every first word is capitalised — and it was **measured** rather
    than argued. Across nine live drafts, sentence-initial rejections
    were ordinary English every time (*Operational*, *Divergent*,
    *Short-term*, *Substantial*, *Analysts*, *Scale*, *Additional*,
    *Flat*) and a fabricated name in that position appeared zero times.
    A word list chasing the first group was losing correct drafts to
    catch nothing.

    So a first word is challenged only when it is *shaped* like a name:
    an acronym (`AUSTRAC`, `ETF`), an internal capital (`MicroStrategy`,
    `CoinDesk`, `FalconX`, `H100`), or the head of a capitalised phrase
    (`Assistance Fund`). Those cover how entities are actually written
    in this corpus.

    **The honest limit**, stated because it is real: a fabricated
    single-word plain-capitalised name in subject position — *"Coinbase
    led the buying."* — is not caught by this rule. Mid-sentence it is;
    and every figure it might carry still is. The alternative was a
    validator that refused most correct drafts, which fails closed into
    showing the investor nothing at all.
    """

    body = token.strip(".'’-")

    if not body:
        return False

    if body.isupper() and len(body) > 1:
        return True

    if any(character.isupper() for character in body[1:]):
        return True

    if any(character.isdigit() for character in body[1:]):
        return True

    return bool(following[:1].isupper())


def _vocabulary(findings: tuple[NarrativeFinding, ...]) -> set[str]:
    """Every word the evidence used, and its plainer forms."""

    text = " ".join(f"{f.statement} {f.source}" for f in findings)

    words: set[str] = set()

    for word in re.findall(r"[A-Za-z][\w'’&.-]*", text):
        words |= _stems(word)

    return words


def _figures(findings: tuple[NarrativeFinding, ...]) -> set[str]:
    """Every quantity the evidence stated, normalised."""

    return {anchor for finding in findings for anchor in anchors_in(finding.statement)}


def _sources(findings: tuple[NarrativeFinding, ...]) -> set[str]:
    """The names a sentence may cite when reporting an attributed cause."""

    names: set[str] = set()

    for finding in findings:
        if not finding.id.startswith("A"):
            continue

        head = finding.statement.split(" states:")[0]

        names.update(word.lower() for word in re.findall(r"[A-Za-z]{3,}", head))

    return names


_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def validate_item(
    raw: dict[str, Any],
    known: set[str],
    words: set[str],
    figures: set[str],
    sources: set[str],
    supplied_text: str,
    causal_allowed: bool,
    where: str,
) -> SynthesisItem:
    """One statement, checked against every rule, or a worded rejection."""

    stated = (raw.get("stated") or "").strip()

    if not stated:
        raise SynthesisRejected(f"A {where} statement was empty.")

    if len(stated.split()) > MAX_ITEM_WORDS:
        raise SynthesisRejected(
            f"A {where} statement ran to {len(stated.split())} words, over "
            f"the {MAX_ITEM_WORDS}-word limit."
        )

    refs = tuple(raw.get("refs") or ())

    # ── references ──────────────────────────────────────────────────
    if not refs:
        raise SynthesisRejected(
            f"A {where} statement cites no findings. Every statement must "
            "be traceable to supplied evidence."
        )

    unknown = [ref for ref in refs if ref not in known]

    if unknown:
        raise SynthesisRejected(
            f"A {where} statement cites findings that were not supplied "
            f"({', '.join(unknown)})."
        )

    spoken = stated.lower()

    # ── actions ─────────────────────────────────────────────────────
    directive = _DIRECTIVE.search(stated)

    if directive is not None:
        raise SynthesisRejected(
            f"A {where} statement told the reader to {directive.group(2)!r}. "
            "This layer says what matters, never what to do."
        )

    for word in VERDICT_WORDS:
        if re.search(rf"\b{word.upper()}\b", stated):
            raise SynthesisRejected(
                f"A {where} statement used the verdict {word.upper()!r}. "
                "Only the Artificial CIO decides, and it is not here."
            )

    for phrase in FORBIDDEN_ADVICE:
        if phrase in spoken:
            raise SynthesisRejected(
                f"A {where} statement wrote about {phrase!r}. This platform "
                "suggests no size, price or quantity."
            )

    # ── figures ─────────────────────────────────────────────────────
    for anchor in anchors_in(stated):
        if anchor not in figures:
            raise SynthesisRejected(
                f"A {where} statement contains the figure {anchor!r}, which "
                "appears in no supplied finding. The synthesist may not "
                "calculate, and may not round."
            )

    # ── guarded concepts ────────────────────────────────────────────
    #
    # A single-word concept is matched through the same stemming the
    # entity rule uses: the evidence says *"record staked supply"* and a
    # model writing *"staking"* is describing it, not recalling it. A
    # raw substring test called those two different words and refused a
    # correct draft.
    for concept in GUARDED_CONCEPTS:
        if concept not in spoken:
            continue

        if " " in concept:
            supplied = concept in supplied_text
        else:
            supplied = bool(_stems(concept) & words)

        if not supplied:
            raise SynthesisRejected(
                f"A {where} statement mentioned {concept!r}, which no "
                "supplied finding does. The synthesist may not draw on its "
                "own knowledge of the asset."
            )

    # ── entities ────────────────────────────────────────────────────
    for sentence in _SENTENCE.split(stated):
        tokens = re.findall(r"[A-Za-z][\w'’&.-]*", sentence)

        for position, token in enumerate(tokens):
            if not token[:1].isupper():
                continue

            forms = _stems(token)

            if forms & words or forms & _ORDINARY or forms & _MONTHS:
                continue

            if token.lower() in _PERIODS:
                continue

            # The first word of a sentence is capitalised whatever it
            # is, so only a *name-shaped* one is challenged there. See
            # `_looks_like_a_name` for what that costs and why.
            following = tokens[position + 1] if position + 1 < len(tokens) else ""

            if position == 0 and not _looks_like_a_name(token, following):
                continue

            raise SynthesisRejected(
                f"A {where} statement names {token!r}, which appears in no "
                "supplied finding. The synthesist may not draw on its own "
                "knowledge of the asset."
            )

    # ── causality ───────────────────────────────────────────────────
    for sentence in _SENTENCE.split(stated):
        lowered = sentence.lower()

        used = _CAUSAL.search(sentence)

        if used is None:
            continue

        if not causal_allowed:
            raise SynthesisRejected(
                f"A {where} statement asserts a cause ({used.group(0)!r}) "
                "where no supplied finding contains an attributed causal "
                "reading."
            )

        # Permitted only where the sentence names whose reading it is.
        named = any(re.search(rf"\b{re.escape(name)}\b", lowered) for name in sources)

        if not named:
            raise SynthesisRejected(
                f"A {where} statement asserts a cause ({used.group(0)!r}) "
                "without naming the source it is attributed to. An "
                "attributed cause keeps its author."
            )

    theme = (raw.get("theme") or "").strip() or None

    if theme and len(theme.split()) > MAX_THEME_WORDS:
        raise SynthesisRejected(
            f"A {where} theme ran to {len(theme.split())} words. A theme is "
            "a label, not a sentence."
        )

    return SynthesisItem(stated=stated, refs=refs, theme=theme)


def synthesis_from_payload(
    payload: dict[str, Any],
    findings: tuple[NarrativeFinding, ...],
    causal_allowed: bool,
) -> tuple[tuple[SynthesisItem, ...], ...]:
    """Accept a draft only if every statement survives every rule.

    Fails closed, and the whole draft fails together. Deleting the
    offending sentence and presenting the rest would tell an investor
    that what remains was checked *and that nothing was removed* — and
    the second half of that would be false.
    """

    known = {finding.id for finding in findings}
    words = _vocabulary(findings)
    figures = _figures(findings)
    sources = _sources(findings)
    supplied_text = " ".join(f.statement for f in findings).lower()

    sections: list[tuple[SynthesisItem, ...]] = []

    for name, cap in (
        ("what_matters", MAX_WHAT_MATTERS),
        ("why_it_matters", MAX_WHY),
        ("watch_next", MAX_WATCH),
    ):
        raw_items = payload.get(name) or []

        if not isinstance(raw_items, list):
            raise SynthesisRejected(f"{name} was not a list of statements.")

        if not raw_items:
            raise SynthesisRejected(f"The synthesist returned no {name}.")

        if len(raw_items) > cap:
            raise SynthesisRejected(
                f"The synthesist returned {len(raw_items)} {name} statements, "
                f"over the limit of {cap}."
            )

        sections.append(
            tuple(
                validate_item(
                    raw,
                    known=known,
                    words=words,
                    figures=figures,
                    sources=sources,
                    supplied_text=supplied_text,
                    causal_allowed=causal_allowed,
                    where=name,
                )
                for raw in raw_items
            )
        )

    return tuple(sections)


class IntelligenceSynthesist:
    """Ask a provider to read the evidence, then validate what comes back."""

    def __init__(self, provider: NarrativeProvider) -> None:
        self.provider = provider

    async def synthesise(
        self,
        snapshot: CryptoIntelligenceSnapshot,
        history: tuple[TemporalFact, ...] = (),
        judgments: tuple[JudgmentTransition, ...] = (),
    ) -> tuple[tuple[tuple[SynthesisItem, ...], ...], str]:
        """The three validated sections and the model that wrote them."""

        findings = build_findings(snapshot, history, judgments)

        request = DraftRequest(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt(snapshot.symbol, findings),
            schema=synthesis_schema(),
            max_tokens=MAX_DRAFT_TOKENS,
        )

        try:
            draft = await self.provider.draft(request)
        except NarrativeDeclined as declined:
            raise SynthesisRejected(str(declined)) from declined

        if not draft.text.strip():
            raise SynthesisRejected(
                "The synthesist returned an empty draft, so no synthesis was produced."
            )

        try:
            payload = json.loads(draft.text)
        except json.JSONDecodeError as error:
            raise SynthesisRejected(
                "The synthesist returned unparseable output."
            ) from error

        sections = synthesis_from_payload(
            payload,
            findings=findings,
            causal_allowed=bool(snapshot.causal_claims),
        )

        return sections, draft.model
