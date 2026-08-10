"""Which investment questions apply to a token, and which do not.

The crypto counterpart of `app/domain/financial_question.py`, built to
the same discipline and reusing its hardest-won distinction: *a question
this platform declines to ask* and *a question it cannot answer* are
opposite claims about the same blank space, and only one of them is a
reason to go and acquire evidence.

Three vocabularies, kept apart on purpose, because collapsing any two
of them is how a dashboard starts lying:

```text
applicability   ← this module: does the question apply to this kind
                  of asset at all? Decided from the archetype alone.
evidence        ← EvidenceStanding: is there anything to answer it
                  with, and how far can it be trusted?
verdict         ← nothing yet. S3 asks questions and answers none.
```

The first never depends on the second. Hyperliquid's fee mechanism is a
single provider's uncorroborated claim, and the *question* it speaks to
— does economic value reach this token? — is legitimately HYPE's whether
or not a figure ever establishes. A platform that only admitted a
question once it could answer it would be choosing its questions to
suit its data, which is the failure this whole layer exists to prevent.

**A question is owned by a capability, never by an archetype.** That is
what lets an exchange that runs its own chain be asked the venue's
questions and the network's without either set being written twice, and
what will let a future archetype compose without a new question table.

No thresholds, bands or scores live here. Nothing in this module is an
answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.crypto_archetype import (
    ARCHETYPES,
    AnalyticalCapability,
    TokenArchetype,
)
from app.domain.protocol_fundamentals import ProtocolEntityKind, ProtocolMetric


class CryptoQuestionKey(StrEnum):
    """A stable name for one investment question about a digital asset.

    Named for the *investor's question*, never for the metric that
    happens to answer it today — the rule the financial questions
    already live by. "Economic activity" survives a source that
    measures it with transaction counts instead of fees; "fees per day"
    would not.
    """

    MARKET_ROBUSTNESS = "market_robustness"
    LIQUIDITY = "liquidity"
    SUPPLY_AND_DILUTION = "supply_and_dilution"
    EVIDENCE_MATURITY = "evidence_maturity"

    MONETARY_SCARCITY = "monetary_scarcity"
    MONETARY_ADOPTION = "monetary_adoption"
    NETWORK_SECURITY = "network_security"
    DECENTRALISATION = "decentralisation"

    USAGE = "usage"
    ECONOMIC_ACTIVITY = "economic_activity"
    CAPITAL_COMMITTED = "capital_committed"
    ECOSYSTEM_ADOPTION = "ecosystem_adoption"

    SETTLEMENT_DEPENDENCY = "settlement_dependency"
    SEQUENCER_ECONOMICS = "sequencer_economics"

    VENUE_ACTIVITY = "venue_activity"
    COMPETITIVE_POSITION = "competitive_position"

    PROTOCOL_CAPTURE = "protocol_capture"
    HOLDER_VALUE_ACCRUAL = "holder_value_accrual"
    TOKEN_ECONOMIC_RIGHTS = "token_economic_rights"


@dataclass(frozen=True, slots=True)
class EvidenceDemand:
    """One thing that would answer a question, named rather than assumed.

    Bound where this platform has somewhere to look — a token fact by
    name, a protocol metric on a kind of entity — and unbound where it
    does not. An unbound demand is an acquisition demand: it states what
    is missing in the currency every other demand on this platform is
    stated in, and it is never quietly dropped so that a question can
    look answered.

    A demand names a **fact**, never a verdict. The rule the bank's
    "deposit funding quality" taught: a demand phrased as a conclusion
    asks to be handed the very answer the question exists to produce,
    and the gap could then never close on evidence.
    """

    stated: str

    #: A name from `app.domain.token_facts.TOKEN_FACTS`.
    token_fact: str | None = None

    #: A protocol metric, and the kind of entity expected to supply it.
    #: The entity kind is part of the demand because the same metric
    #: means different things on a chain and on a venue.
    protocol_metric: ProtocolMetric | None = None
    entity_kind: ProtocolEntityKind | None = None

    #: Whether what is wanted is the source's *definition* of the metric
    #: rather than its figure. The two are different evidence: a burn, a
    #: buyback and a distribution can produce the identical number, and
    #: only the wording separates them — so the wording is demanded by
    #: name rather than arriving as a decoration on a value.
    wants_methodology: bool = False

    @property
    def is_bound(self) -> bool:
        """Whether this platform has anywhere at all to read it from."""

        return self.token_fact is not None or self.protocol_metric is not None


@dataclass(frozen=True, slots=True)
class CryptoQuestion:
    """One investment question, and what would answer it."""

    key: CryptoQuestionKey

    #: The question in words, as an investor would ask it.
    asks: str

    #: Why an investor should care about the answer.
    matters_because: str

    demands: tuple[EvidenceDemand, ...]

    @property
    def label(self) -> str:
        return _LABELS[self.key]

    @property
    def acquisition_demands(self) -> tuple[EvidenceDemand, ...]:
        """The demands nothing here can currently be read from."""

        return tuple(demand for demand in self.demands if not demand.is_bound)


_LABELS = {
    CryptoQuestionKey.MARKET_ROBUSTNESS: "Market robustness",
    CryptoQuestionKey.LIQUIDITY: "Liquidity",
    CryptoQuestionKey.SUPPLY_AND_DILUTION: "Supply and dilution",
    CryptoQuestionKey.EVIDENCE_MATURITY: "Evidence maturity",
    CryptoQuestionKey.MONETARY_SCARCITY: "Monetary scarcity",
    CryptoQuestionKey.MONETARY_ADOPTION: "Monetary adoption",
    CryptoQuestionKey.NETWORK_SECURITY: "Network security",
    CryptoQuestionKey.DECENTRALISATION: "Decentralisation",
    CryptoQuestionKey.USAGE: "Usage",
    CryptoQuestionKey.ECONOMIC_ACTIVITY: "Economic activity",
    CryptoQuestionKey.CAPITAL_COMMITTED: "Capital committed",
    CryptoQuestionKey.ECOSYSTEM_ADOPTION: "Ecosystem adoption",
    CryptoQuestionKey.SETTLEMENT_DEPENDENCY: "Settlement dependency",
    CryptoQuestionKey.SEQUENCER_ECONOMICS: "Operator economics",
    CryptoQuestionKey.VENUE_ACTIVITY: "Venue activity",
    CryptoQuestionKey.COMPETITIVE_POSITION: "Competitive position",
    CryptoQuestionKey.PROTOCOL_CAPTURE: "Protocol value capture",
    CryptoQuestionKey.HOLDER_VALUE_ACCRUAL: "Token-holder value accrual",
    CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS: "Token economic rights",
}


#: Every crypto investment question this platform knows how to ask.
QUESTIONS: dict[CryptoQuestionKey, CryptoQuestion] = {
    CryptoQuestionKey.MARKET_ROBUSTNESS: CryptoQuestion(
        key=CryptoQuestionKey.MARKET_ROBUSTNESS,
        asks=(
            "Is the market in this asset large enough for its price to mean something?"
        ),
        matters_because=(
            "A price set by a thin market is a quotation rather than a "
            "valuation, and everything computed from it inherits that."
        ),
        demands=(
            EvidenceDemand(
                stated="the market value of the circulating supply",
                token_fact="market_cap",
            ),
            EvidenceDemand(
                stated=(
                    "its rank among tracked assets — vendor-relative by "
                    "nature, and only ever read beside the universe it "
                    "was ranked in"
                ),
                token_fact="rank",
            ),
            EvidenceDemand(
                stated="the value traded across all venues in a day",
                token_fact="market_volume_24h",
            ),
        ),
    ),
    CryptoQuestionKey.LIQUIDITY: CryptoQuestion(
        key=CryptoQuestionKey.LIQUIDITY,
        asks="Could a position be left without moving the price against it?",
        matters_because=(
            "For an asset with no earnings, whether a holding can be "
            "exited is most of what quality can honestly mean."
        ),
        demands=(
            EvidenceDemand(
                stated="a day's value traded on tracked spot venues",
                token_fact="spot_volume_24h",
            ),
            EvidenceDemand(
                stated="a day's value traded across the wider market",
                token_fact="market_volume_24h",
            ),
            EvidenceDemand(
                stated=(
                    "order-book depth at the venues this investor could "
                    "actually trade on — volume says how much changed "
                    "hands, not what it would cost to sell"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.SUPPLY_AND_DILUTION: CryptoQuestion(
        key=CryptoQuestionKey.SUPPLY_AND_DILUTION,
        asks="How much of the eventual supply exists, and what is still to come?",
        matters_because=(
            "A holder of a partly issued token is diluted by a schedule "
            "rather than by a decision, and the schedule was set before "
            "they arrived."
        ),
        demands=(
            EvidenceDemand(
                stated="the supply in circulation now",
                token_fact="circulating_supply",
            ),
            EvidenceDemand(
                stated="the supply issued in total",
                token_fact="total_supply",
            ),
            EvidenceDemand(
                stated="the maximum supply that will ever exist",
                token_fact="max_supply",
            ),
            EvidenceDemand(
                stated="what the whole eventual supply would be worth today",
                token_fact="fully_diluted_valuation",
            ),
            EvidenceDemand(
                stated=(
                    "the vesting and unlock schedule for the supply not "
                    "yet issued — when it arrives, and to whom"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.EVIDENCE_MATURITY: CryptoQuestion(
        key=CryptoQuestionKey.EVIDENCE_MATURITY,
        asks=(
            "How much observed evidence is there that this asset and its "
            "network survive materially different conditions?"
        ),
        matters_because=(
            "Every other question here is answered from a market that "
            "has been one way. What an asset does when conditions change "
            "is not visible in any of them, and is not the same claim as "
            "how long it has existed."
        ),
        demands=(
            EvidenceDemand(
                stated=(
                    "observed price history through at least one full "
                    "market cycle, held by this platform rather than "
                    "asserted about the world"
                ),
            ),
            EvidenceDemand(
                stated=("the drawdowns observed here, and what recovery followed each"),
            ),
            EvidenceDemand(
                stated=(
                    "the network's operating history — outages, halts, "
                    "and how long each lasted"
                ),
            ),
            EvidenceDemand(
                stated=(
                    "security incidents, what was lost, and how the "
                    "system behaved afterwards"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.MONETARY_SCARCITY: CryptoQuestion(
        key=CryptoQuestionKey.MONETARY_SCARCITY,
        asks="Is issuance fixed, terminal, and beyond anyone's discretion to change?",
        matters_because=(
            "A monetary asset's case is that nobody can make more of it. "
            "A stated cap is not that claim: the claim is about the rule "
            "and about who could rewrite it."
        ),
        demands=(
            EvidenceDemand(
                stated="the stated maximum supply",
                token_fact="max_supply",
            ),
            EvidenceDemand(
                stated="how much of it already exists",
                token_fact="circulating_supply",
            ),
            EvidenceDemand(
                stated=(
                    "the issuance schedule itself — the rate today and "
                    "the rate it falls to"
                ),
            ),
            EvidenceDemand(
                stated=("who is able to change that schedule, and by what process"),
            ),
        ),
    ),
    CryptoQuestionKey.MONETARY_ADOPTION: CryptoQuestion(
        key=CryptoQuestionKey.MONETARY_ADOPTION,
        asks="Is the asset actually held and used as money?",
        matters_because=(
            "Scarcity without holders is a property of a spreadsheet. "
            "The monetary case needs someone to be treating it as money."
        ),
        demands=(
            EvidenceDemand(
                stated=(
                    "holdings by identifiable long-term holders, and how "
                    "those have changed"
                ),
            ),
            EvidenceDemand(
                stated="the value actually settled on the network over a period",
            ),
            EvidenceDemand(
                stated=(
                    "acceptance as a unit of account or as a reserve by "
                    "entities that publish their holdings"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.NETWORK_SECURITY: CryptoQuestion(
        key=CryptoQuestionKey.NETWORK_SECURITY,
        asks="What does it cost to attack this network, and who pays for the defence?",
        matters_because=(
            "Everything else about a network assumes its ledger holds. "
            "What makes it hold is paid for, and by whom is an "
            "investment question rather than a technical one."
        ),
        demands=(
            EvidenceDemand(
                stated=(
                    "the fees users pay, which are one half of what the "
                    "network's security is paid with"
                ),
                protocol_metric=ProtocolMetric.FEES,
                entity_kind=ProtocolEntityKind.CHAIN,
            ),
            EvidenceDemand(
                stated=(
                    "the issuance paid to whoever produces blocks — the "
                    "other half, and today the larger one"
                ),
            ),
            EvidenceDemand(
                stated=(
                    "who receives those payments; the source records "
                    "what users pay and not where it goes"
                ),
            ),
            EvidenceDemand(
                stated=(
                    "what it would cost to acquire enough of the "
                    "network's production to rewrite its ledger"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.DECENTRALISATION: CryptoQuestion(
        key=CryptoQuestionKey.DECENTRALISATION,
        asks="How concentrated is control of this network?",
        matters_because=(
            "A network few parties control can be changed, censored or "
            "stopped by those parties, and every property an investor is "
            "buying rests on it not being."
        ),
        demands=(
            EvidenceDemand(
                stated="how block production or validation is distributed",
            ),
            EvidenceDemand(
                stated="how concentrated the holdings are",
            ),
            EvidenceDemand(
                stated=(
                    "who may change the protocol's rules, and what it takes to do so"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.USAGE: CryptoQuestion(
        key=CryptoQuestionKey.USAGE,
        asks="Is this system actually being used?",
        matters_because=(
            "The first of four questions that are routinely collapsed "
            "into one. A system can be heavily used and generate "
            "nothing; usage is the precondition, not the case."
        ),
        demands=(
            EvidenceDemand(
                stated="the value traded through the venue's own book",
                protocol_metric=ProtocolMetric.DEX_VOLUME,
                entity_kind=ProtocolEntityKind.PROTOCOL,
            ),
            EvidenceDemand(
                stated=(
                    "the count and value of transactions the network "
                    "settles over a period"
                ),
            ),
            EvidenceDemand(
                stated="distinct users or accounts active over a period",
            ),
        ),
    ),
    CryptoQuestionKey.ECONOMIC_ACTIVITY: CryptoQuestion(
        key=CryptoQuestionKey.ECONOMIC_ACTIVITY,
        asks="Does that use generate economic value?",
        matters_because=(
            "The second question. Fees are what use is worth to the "
            "system — and the same word means a different thing "
            "depending on where the fees then go, which is the third and "
            "fourth questions and not this one."
        ),
        demands=(
            EvidenceDemand(
                stated="the fees users pay to use the system",
                protocol_metric=ProtocolMetric.FEES,
            ),
            EvidenceDemand(
                stated=(
                    "the same figure over a longer window than a day — "
                    "one day is a reading, not a trend"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.CAPITAL_COMMITTED: CryptoQuestion(
        key=CryptoQuestionKey.CAPITAL_COMMITTED,
        asks="How much capital is committed to this system?",
        matters_because=(
            "Capital left in a system is a revealed judgment about it by "
            "people with money at stake — and it can leave in a day, so "
            "it is a level rather than a foundation."
        ),
        demands=(
            EvidenceDemand(
                stated="the value of assets held in the system",
                protocol_metric=ProtocolMetric.TVL,
            ),
        ),
    ),
    CryptoQuestionKey.ECOSYSTEM_ADOPTION: CryptoQuestion(
        key=CryptoQuestionKey.ECOSYSTEM_ADOPTION,
        asks="What is built on this network, and is that growing?",
        matters_because=(
            "A settlement layer is worth what needs settling on it. One "
            "large application is a different asset from a hundred small "
            "ones, and the aggregate figure hides which it is."
        ),
        demands=(
            EvidenceDemand(
                stated=("the applications deployed on the network and what each holds"),
            ),
            EvidenceDemand(
                stated="how that composition has changed over a period",
            ),
        ),
    ),
    CryptoQuestionKey.SETTLEMENT_DEPENDENCY: CryptoQuestion(
        key=CryptoQuestionKey.SETTLEMENT_DEPENDENCY,
        asks="What does this network depend on to settle, and what does that cost?",
        matters_because=(
            "A network that settles elsewhere has an owner of last "
            "resort that is not itself. Its security, its costs and its "
            "continued existence are partly another network's."
        ),
        demands=(
            EvidenceDemand(
                stated="which network it settles to",
            ),
            EvidenceDemand(
                stated=(
                    "what settlement costs it, and in whose asset that cost is paid"
                ),
            ),
            EvidenceDemand(
                stated=(
                    "what becomes of it if the network beneath is "
                    "unavailable or unaffordable"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.SEQUENCER_ECONOMICS: CryptoQuestion(
        key=CryptoQuestionKey.SEQUENCER_ECONOMICS,
        asks="Who operates this network, what do they earn, and can that change hands?",
        matters_because=(
            "Where one operator orders the transactions, the difference "
            "between what users pay and what settlement costs is theirs "
            "— and whether any of it is the token's is a separate "
            "question with a separate answer."
        ),
        demands=(
            EvidenceDemand(
                stated="who operates the sequencer today",
            ),
            EvidenceDemand(
                stated=(
                    "what it earns — the margin between fees collected "
                    "and settlement paid"
                ),
            ),
            EvidenceDemand(
                stated=(
                    "the process by which operation could pass to "
                    "someone else, and who decides"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.VENUE_ACTIVITY: CryptoQuestion(
        key=CryptoQuestionKey.VENUE_ACTIVITY,
        asks="How much flows through this venue's book?",
        matters_because=(
            "A venue earns on flow. This is the measure of the business "
            "itself, and it is a different measurement from the token's "
            "own trading volume."
        ),
        demands=(
            EvidenceDemand(
                stated="the value traded through its spot book in a day",
                protocol_metric=ProtocolMetric.DEX_VOLUME,
                entity_kind=ProtocolEntityKind.PROTOCOL,
            ),
            EvidenceDemand(
                stated="the notional value of derivative positions open on it",
                protocol_metric=ProtocolMetric.OPEN_INTEREST,
                entity_kind=ProtocolEntityKind.PROTOCOL,
            ),
            EvidenceDemand(
                stated=(
                    "derivatives volume, which the source this platform "
                    "reads publishes only behind payment"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.COMPETITIVE_POSITION: CryptoQuestion(
        key=CryptoQuestionKey.COMPETITIVE_POSITION,
        asks="Is this venue's share of the flow durable?",
        matters_because=(
            "Flow moves to whoever is cheapest and deepest this quarter. "
            "A venue's volume says it won; it does not say it will keep "
            "winning."
        ),
        demands=(
            EvidenceDemand(
                stated="the same volume measure for the venues it competes with",
            ),
            EvidenceDemand(
                stated="how its share of the total has moved over a period",
            ),
        ),
    ),
    CryptoQuestionKey.PROTOCOL_CAPTURE: CryptoQuestion(
        key=CryptoQuestionKey.PROTOCOL_CAPTURE,
        asks="Does the protocol itself retain any of what it charges?",
        matters_because=(
            "The third question. What the protocol keeps and what "
            "reaches its token are different amounts with different "
            "owners — Hyperliquid keeps nothing and directs almost "
            "everything to buying its token, which no single 'revenue' "
            "figure could express."
        ),
        demands=(
            EvidenceDemand(
                stated="the share of fees the protocol retains",
                protocol_metric=ProtocolMetric.PROTOCOL_REVENUE,
            ),
            EvidenceDemand(
                stated=("what the retained share is spent on, and who decides"),
            ),
        ),
    ),
    CryptoQuestionKey.HOLDER_VALUE_ACCRUAL: CryptoQuestion(
        key=CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
        asks="Does any economic value reach the token, and by what mechanism?",
        matters_because=(
            "The fourth question, and the one that decides whether a "
            "successful system is a valuable token. They are not the "
            "same claim: a protocol can earn enormously and pass its "
            "holders nothing."
        ),
        demands=(
            EvidenceDemand(
                stated="the share of fees that reaches holders",
                protocol_metric=ProtocolMetric.HOLDER_REVENUE,
            ),
            EvidenceDemand(
                stated=(
                    "the mechanism in the source's own words — a burn, "
                    "a buyback and a distribution are three different "
                    "things and only the wording separates them"
                ),
                protocol_metric=ProtocolMetric.HOLDER_REVENUE,
                wants_methodology=True,
            ),
            EvidenceDemand(
                stated=(
                    "whether the mechanism is fixed or discretionary, "
                    "and who is able to end it"
                ),
            ),
        ),
    ),
    CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS: CryptoQuestion(
        key=CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS,
        asks="What does holding this token entitle its holder to?",
        matters_because=(
            "An equity carries a defined claim. A token carries whatever "
            "its system says it carries, which may be nothing at all — "
            "and 'nothing' is a finding an investor is owed explicitly."
        ),
        demands=(
            EvidenceDemand(
                stated="the governance rights the token carries, if any",
            ),
            EvidenceDemand(
                stated="any claim on fees, reserves or assets",
            ),
            EvidenceDemand(
                stated="whether those rights can be changed, and by whom",
            ),
        ),
    ),
}


#: Which questions each analytical lens asks.
#:
#: The union over an archetype's capabilities is what that security is
#: asked. Overlap is deliberate and harmless: a monetary network and a
#: smart-contract network both ask about security and about
#: concentration, because both genuinely need the answer.
ASKED_BY: dict[AnalyticalCapability, tuple[CryptoQuestionKey, ...]] = {
    AnalyticalCapability.MARKET_ASSET: (
        CryptoQuestionKey.MARKET_ROBUSTNESS,
        CryptoQuestionKey.LIQUIDITY,
        CryptoQuestionKey.SUPPLY_AND_DILUTION,
        CryptoQuestionKey.EVIDENCE_MATURITY,
    ),
    AnalyticalCapability.MONETARY_NETWORK: (
        CryptoQuestionKey.MONETARY_SCARCITY,
        CryptoQuestionKey.MONETARY_ADOPTION,
        CryptoQuestionKey.USAGE,
        CryptoQuestionKey.NETWORK_SECURITY,
        CryptoQuestionKey.DECENTRALISATION,
    ),
    AnalyticalCapability.SMART_CONTRACT_NETWORK: (
        CryptoQuestionKey.USAGE,
        CryptoQuestionKey.ECONOMIC_ACTIVITY,
        CryptoQuestionKey.CAPITAL_COMMITTED,
        CryptoQuestionKey.ECOSYSTEM_ADOPTION,
        CryptoQuestionKey.NETWORK_SECURITY,
        CryptoQuestionKey.DECENTRALISATION,
    ),
    AnalyticalCapability.SCALING_INFRASTRUCTURE: (
        CryptoQuestionKey.SETTLEMENT_DEPENDENCY,
        CryptoQuestionKey.SEQUENCER_ECONOMICS,
    ),
    AnalyticalCapability.VENUE_ECONOMICS: (
        CryptoQuestionKey.VENUE_ACTIVITY,
        CryptoQuestionKey.COMPETITIVE_POSITION,
    ),
    AnalyticalCapability.PROTOCOL_ECONOMICS: (
        CryptoQuestionKey.USAGE,
        CryptoQuestionKey.ECONOMIC_ACTIVITY,
        CryptoQuestionKey.PROTOCOL_CAPTURE,
    ),
    AnalyticalCapability.TOKEN_VALUE_CAPTURE: (
        CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
        CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS,
    ),
}


@dataclass(frozen=True, slots=True)
class QuestionDecline:
    """A question an archetype holds to be the wrong question, and why.

    The sibling of `app.domain.financial_question.QuestionDecline`, one
    evidence family over. Written by hand only where the archetype has
    something specific to say; otherwise the refusal is worded from the
    lens that would have asked it, which is already an accurate account.
    """

    question: CryptoQuestionKey
    reason: str


#: What each archetype refuses in its own words.
#:
#: Keyed by archetype rather than by capability, because a refusal is a
#: claim about a kind of asset — "a monetary network is not asked what
#: it earns" — and no lens can make that claim, only the composition
#: can.
DECLINED: dict[TokenArchetype, tuple[QuestionDecline, ...]] = {
    TokenArchetype.MONETARY_NETWORK: (
        QuestionDecline(
            question=CryptoQuestionKey.ECONOMIC_ACTIVITY,
            reason=(
                "The fee figure exists and is not revenue here. What "
                "users pay a monetary network is part of what its "
                "security is paid with, so it answers the security "
                "question and is read there. Scoring it as economic "
                "value generated would treat a cost of defence as an "
                "earning."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.PROTOCOL_CAPTURE,
            reason=(
                "There is no protocol here that retains anything. The "
                "network has no treasury on this platform's evidence, "
                "and asking what it keeps would invent an entity to "
                "keep it."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
            reason=(
                "A monetary asset's return is not a distribution, and "
                "asking whether one arrives would mark it down for "
                "being what it is. This is the same error as judging a "
                "bank on the industrial leverage threshold: the answer "
                "would be *none*, the number would be real, and the "
                "question would be the wrong instrument. The fee source "
                "confirms the shape of it — DefiLlama defines fees and "
                "protocol revenue for Bitcoin and defines no holder "
                "mechanism at all."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.TOKEN_ECONOMIC_RIGHTS,
            reason=(
                "The asset is the entitlement. A monetary network's "
                "unit carries no claim on anything else, and reporting "
                "that as an absent right would read as a deficiency "
                "rather than as the design."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.CAPITAL_COMMITTED,
            reason=(
                "Capital held in applications measures a smart-contract "
                "ecosystem. Bitcoin's carries $3.56bn — 0.3% of the "
                "asset's market value — and a monetary case does not "
                "rest on what has been built on the chain."
            ),
        ),
    ),
    TokenArchetype.SMART_CONTRACT_NETWORK: (
        QuestionDecline(
            question=CryptoQuestionKey.PROTOCOL_CAPTURE,
            reason=(
                "A chain has no treasury that retains what its users "
                "pay. Where fees are removed from supply instead — "
                "which is what Ethereum's and Solana's own methodologies "
                "describe — nothing is retained by anyone, and the "
                "removal is read at the accrual question rather than "
                "here. Asking what the protocol keeps would invent an "
                "entity to keep it."
            ),
        ),
    ),
    TokenArchetype.SCALING_NETWORK: (
        QuestionDecline(
            question=CryptoQuestionKey.PROTOCOL_CAPTURE,
            reason=(
                "The same as any chain: there is no protocol treasury "
                "on this platform's evidence. What the operator retains "
                "between fees collected and settlement paid is a real "
                "question and a different one, and it is asked as "
                "operator economics."
            ),
        ),
    ),
    TokenArchetype.APPLICATION_PROTOCOL: (
        QuestionDecline(
            question=CryptoQuestionKey.DECENTRALISATION,
            reason=(
                "Concentration of block production and of protocol rule "
                "changes is a property of the network it runs on, not of "
                "an application deployed to it. What can be changed "
                "about this protocol, and by whom, is asked as token "
                "economic rights."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.VENUE_ACTIVITY,
            reason=(
                "An aggregator routes trades to other venues and runs "
                "no book of its own, so there is no flow of its own to "
                "measure. The provider's DEX list does hold a "
                "similarly-named product; reading that as this "
                "protocol's activity would attribute another business's "
                "volume on the strength of a shared name."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.CAPITAL_COMMITTED,
            reason=(
                "It holds little capital of its own by design, so the "
                "figure would measure something other than the "
                "business."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.NETWORK_SECURITY,
            reason=(
                "It runs on infrastructure it does not own. What "
                "secures that infrastructure is a question about the "
                "network, and is asked of the network."
            ),
        ),
    ),
    TokenArchetype.STABLECOIN: (
        QuestionDecline(
            question=CryptoQuestionKey.MONETARY_SCARCITY,
            reason=(
                "A stablecoin is supposed to be issued and redeemed "
                "freely against what it tracks. Scarcity is not a "
                "virtue here and a fixed cap would be a defect, so the "
                "monetary question is not merely unanswerable — it is "
                "inverted."
            ),
        ),
        QuestionDecline(
            question=CryptoQuestionKey.HOLDER_VALUE_ACCRUAL,
            reason=(
                "What a reserve earns belongs to the issuer unless the "
                "instrument says otherwise, and that is a question "
                "about the issuer's terms rather than about a fee "
                "mechanism. Answering it from protocol economics would "
                "read an unrelated system's accrual onto a claim on "
                "reserves."
            ),
        ),
    ),
}


class QuestionApplicability(StrEnum):
    """Whether a question applies — and never whether it can be answered.

    Three states, mirroring the discipline `AnswerState` already
    enforces on the equity side: a statement about the question, a
    statement about the asset, and a statement about this platform's
    knowledge are three different things.

    What is deliberately *not* here is an evidence state.
    `EvidenceStanding` already carries that for every family, and
    joining the two vocabularies is the caller's job — so that
    "this question does not apply to BTC" can never be produced by an
    absence of data.
    """

    #: The question applies to this kind of asset.
    ASK = "ask"

    #: It is the wrong question for this kind of asset. A claim about
    #: the asset, and a reason not to go looking for evidence.
    NOT_APPLICABLE_FOR_ARCHETYPE = "not_applicable_for_archetype"

    #: No archetype was established, so whether it applies is unknown.
    #: A claim about this platform, and never about the asset.
    UNDETERMINED = "undetermined"

    @property
    def stated(self) -> str:
        return _APPLICABILITY[self]


_APPLICABILITY = {
    QuestionApplicability.ASK: "Ask",
    QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE: "Not applicable",
    QuestionApplicability.UNDETERMINED: "Undetermined",
}


@dataclass(frozen=True, slots=True)
class Applicability:
    """Whether one question applies to one archetype, and the account of it."""

    question: CryptoQuestionKey
    state: QuestionApplicability
    because: str

    #: The lens that asks it, where it is asked. None otherwise.
    asked_by: AnalyticalCapability | None = None

    @property
    def is_asked(self) -> bool:
        return self.state is QuestionApplicability.ASK


def questions_for(archetype: TokenArchetype) -> tuple[CryptoQuestionKey, ...]:
    """The questions this archetype asks — the union of its lenses'.

    In `CryptoQuestionKey` declaration order rather than in the order
    the lenses happened to be listed, so two archetypes sharing a
    question present it in the same place.
    """

    definition = ARCHETYPES[archetype]

    asked = {
        key for capability in definition.capabilities for key in ASKED_BY[capability]
    }

    return tuple(key for key in CryptoQuestionKey if key in asked)


def _asks(
    archetype: TokenArchetype,
    question: CryptoQuestionKey,
) -> AnalyticalCapability | None:
    """The first lens of this archetype that asks the question."""

    for capability in ARCHETYPES[archetype].capabilities:
        if question in ASKED_BY[capability]:
            return capability

    return None


def _would_ask(question: CryptoQuestionKey) -> tuple[AnalyticalCapability, ...]:
    """Every lens that asks this question, whoever composes it."""

    return tuple(
        capability
        for capability in AnalyticalCapability
        if question in ASKED_BY[capability]
    )


def applicability_for(
    archetype: TokenArchetype,
    question: CryptoQuestionKey,
) -> Applicability:
    """Whether this question applies to this archetype.

    **Takes the archetype and nothing else.** Not a convenience: it is
    the structural guarantee behind the ruling's sixth section. A
    function that could see the evidence could let a missing figure
    turn a legitimate question into an inapplicable one, and the
    difference between "we do not ask this of Bitcoin" and "nobody
    publishes this for Bitcoin" would quietly disappear.
    """

    capability = _asks(archetype, question)

    if capability is not None:
        return Applicability(
            question=question,
            state=QuestionApplicability.ASK,
            because=(
                f"{ARCHETYPES[archetype].name} is read through the "
                f"{capability.label.lower()} lens, which reads "
                f"{capability.reads}."
            ),
            asked_by=capability,
        )

    if archetype is TokenArchetype.UNKNOWN:
        return Applicability(
            question=question,
            state=QuestionApplicability.UNDETERMINED,
            because=(
                "No archetype was established for this security, so "
                "this platform cannot say whether the question applies. "
                "That is a statement about what has been read here, not "
                "about the asset."
            ),
        )

    for decline in DECLINED.get(archetype, ()):
        if decline.question is question:
            return Applicability(
                question=question,
                state=QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE,
                because=decline.reason,
            )

    lenses = ", ".join(capability.label.lower() for capability in _would_ask(question))

    return Applicability(
        question=question,
        state=QuestionApplicability.NOT_APPLICABLE_FOR_ARCHETYPE,
        because=(
            f"This question belongs to the {lenses} lens, and "
            f"{ARCHETYPES[archetype].name.lower()} is not read through "
            "it."
        ),
    )
