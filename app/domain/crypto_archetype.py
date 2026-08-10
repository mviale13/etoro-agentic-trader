"""What kind of economic object a token is, and which lenses read it.

The crypto half of the classification the equity side already draws
twice — `PlaybookKind` for what a company is, `FinancialModel` for which
financial language reads it. A token needs the same separation and one
thing more, which the corpus forced rather than a designer choosing it:

```text
what the asset is        → TokenArchetype        ← this module
which lenses read it     → AnalyticalCapability  ← a *set*, not one member
which questions apply    → app/domain/crypto_questions.py
```

**The set is the finding.** JPMorgan is a bank or an industrial and never
both, so one enum member could carry its whole reading. HYPE is a
trading venue *and* a layer-1 chain, and S2 proved it with two separate
economic entities whose fees differ by a factor of 224. An archetype
that had to name that combination as one word would need a new word for
every future combination; an archetype that *composes* it needs none.
So an archetype here is a **name for a set of capabilities**, and every
question is owned by a capability rather than by an archetype.

Three disciplines carried in from S1 and S2.

**No asset is classified from a vendor's category label.** This platform
holds TokenInsight's grade and its six dimension labels, and holds no
category field at all. Neither decides anything here. What decides is
the structural evidence the platform can re-check: which economic
entities are mapped to the security and what kind each is, what the
provider's own methodology defines for them, and the token's own supply
facts. Each assignment states that basis so it can be argued with,
exactly as `PROTOCOL_ENTITIES` states its mapping basis.

**A classification that changes no question is metadata.** Every
capability below exists because it changes which questions are asked,
which are declined, or which evidence answers them. `SPECIALISED_NETWORK`
was drafted for TAO and deleted: it would have renamed an absence.

**Not knowing is a first-class answer.** `UNKNOWN` is not a failure
state and not a default that quietly gets the generic set. It composes
the market lens alone, and every other question about that security
reads as *undetermined* rather than as inapplicable — a statement about
this platform's knowledge, never about the asset.

Nothing here scores, bands or ranks. No factor consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.protocol_fundamentals import ProtocolEntity, ProtocolEntityKind


class AnalyticalCapability(StrEnum):
    """One analytical lens: a reason to ask a particular set of questions.

    Capabilities compose. An archetype is the name of a set of them, and
    the questions a security is asked are the union of its capabilities'
    questions — which is what lets an exchange that runs its own chain
    be read as both without inventing a bespoke playbook for it.
    """

    #: Every token that trades. Says nothing about design: an asset can
    #: be liquid and worthless, and this lens only asks whether the
    #: market in it is deep enough for its price to mean anything.
    MARKET_ASSET = "market_asset"

    #: The asset is proposed as money. Its case rests on scarcity, on
    #: what secures it, and on being held — never on what it earns.
    MONETARY_NETWORK = "monetary_network"

    #: A programmable settlement layer. Its case rests on being used,
    #: on the capital committed to it, and on what that use pays.
    SMART_CONTRACT_NETWORK = "smart_contract_network"

    #: A network that settles on another network. It inherits a
    #: dependency the network beneath it does not have, and the
    #: dependency is an investment question of its own.
    SCALING_INFRASTRUCTURE = "scaling_infrastructure"

    #: A trading venue with its own book. Volume and open positions
    #: measure it; a chain has neither.
    VENUE_ECONOMICS = "venue_economics"

    #: An application that charges for a service, and may keep some of
    #: what it charges.
    PROTOCOL_ECONOMICS = "protocol_economics"

    #: Whether any of the economic value reaches the token. The lens
    #: that keeps *successful protocol* and *valuable token* apart —
    #: they are different claims and a system can satisfy one and not
    #: the other.
    TOKEN_VALUE_CAPTURE = "token_value_capture"

    @property
    def label(self) -> str:
        return _CAPABILITY_LABELS[self]

    @property
    def reads(self) -> str:
        """What this lens looks at, in one sentence."""

        return _CAPABILITY_READS[self]


_CAPABILITY_LABELS = {
    AnalyticalCapability.MARKET_ASSET: "Market asset",
    AnalyticalCapability.MONETARY_NETWORK: "Monetary network",
    AnalyticalCapability.SMART_CONTRACT_NETWORK: "Smart-contract network",
    AnalyticalCapability.SCALING_INFRASTRUCTURE: "Scaling infrastructure",
    AnalyticalCapability.VENUE_ECONOMICS: "Venue economics",
    AnalyticalCapability.PROTOCOL_ECONOMICS: "Protocol economics",
    AnalyticalCapability.TOKEN_VALUE_CAPTURE: "Token value capture",
}


_CAPABILITY_READS = {
    AnalyticalCapability.MARKET_ASSET: (
        "the market in the token itself — its size, how much of it "
        "trades, and how much of the eventual supply exists"
    ),
    AnalyticalCapability.MONETARY_NETWORK: (
        "the case for holding the asset as money — whether issuance is "
        "fixed and terminal, what secures it, and who holds it"
    ),
    AnalyticalCapability.SMART_CONTRACT_NETWORK: (
        "the network as a place things are built and settled — usage, "
        "the capital committed to it, and what that use pays"
    ),
    AnalyticalCapability.SCALING_INFRASTRUCTURE: (
        "what the network depends on to settle, and who operates it"
    ),
    AnalyticalCapability.VENUE_ECONOMICS: (
        "the trading venue — what flows through its book, and whether "
        "its position in that flow is durable"
    ),
    AnalyticalCapability.PROTOCOL_ECONOMICS: (
        "the service the protocol sells — whether it is used, what it "
        "charges, and how much of the charge it keeps"
    ),
    AnalyticalCapability.TOKEN_VALUE_CAPTURE: (
        "whether economic value reaches the token, by what mechanism, "
        "and what the token entitles its holder to"
    ),
}


#: What each capability needs a mapped economic entity to look at.
#:
#: The consistency rule between this module and S2's entity table: a
#: security cannot be read through the venue lens if no venue was ever
#: mapped to it. It makes the assignments below falsifiable against
#: stored evidence rather than merely asserted, and it is checked by
#: test over the whole corpus.
_REQUIRES_ENTITY: dict[AnalyticalCapability, ProtocolEntityKind | None] = {
    AnalyticalCapability.MARKET_ASSET: None,
    AnalyticalCapability.MONETARY_NETWORK: ProtocolEntityKind.CHAIN,
    AnalyticalCapability.SMART_CONTRACT_NETWORK: ProtocolEntityKind.CHAIN,
    AnalyticalCapability.SCALING_INFRASTRUCTURE: ProtocolEntityKind.CHAIN,
    AnalyticalCapability.VENUE_ECONOMICS: ProtocolEntityKind.PROTOCOL,
    AnalyticalCapability.PROTOCOL_ECONOMICS: ProtocolEntityKind.PROTOCOL,
    AnalyticalCapability.TOKEN_VALUE_CAPTURE: None,
}


class TokenArchetype(StrEnum):
    """What kind of economic object this token is.

    A name over a capability set, never a bucket of its own. Two
    securities share an archetype exactly when the same lenses read
    them, which is the only sense in which they are the same kind of
    thing for an investor.
    """

    MONETARY_NETWORK = "monetary_network"
    SMART_CONTRACT_NETWORK = "smart_contract_network"
    SCALING_NETWORK = "scaling_network"
    APPLICATION_PROTOCOL = "application_protocol"
    EXCHANGE_NETWORK = "exchange_network"

    #: Declared for the boundary, not for a corpus case. See
    #: `ArchetypeDefinition.unmodelled` — a stablecoin must never be
    #: read through the scarcity or accrual questions, and its own
    #: questions are named and admitted to be unbuilt.
    STABLECOIN = "stablecoin"

    #: No archetype was established. Not a default and not a failure.
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ArchetypeDefinition:
    """One archetype: what it is called, and which lenses it composes."""

    archetype: TokenArchetype

    #: What this is called where an investor reads it.
    name: str

    #: What kind of object this is, in one sentence.
    explanation: str

    capabilities: tuple[AnalyticalCapability, ...]

    #: Questions this archetype is known to need and this platform has
    #: not modelled. An acquisition demand at the level of the question
    #: set itself, and the reason a stablecoin can be declared here
    #: without a stablecoin model being invented for it.
    unmodelled: tuple[str, ...] = ()

    def composes(self, capability: AnalyticalCapability) -> bool:
        return capability in self.capabilities

    def unsupported_by(
        self,
        entities: tuple[ProtocolEntity, ...],
    ) -> tuple[AnalyticalCapability, ...]:
        """Capabilities no mapped entity can supply evidence for.

        Empty is the healthy state. A non-empty answer means this
        archetype claims a lens the security's own entity mapping does
        not support — the venue lens with no venue — and that is a
        defect in the table rather than a property of the security.
        """

        kinds = {entity.kind for entity in entities}

        return tuple(
            capability
            for capability in self.capabilities
            if (needed := _REQUIRES_ENTITY[capability]) is not None
            and needed not in kinds
        )


ARCHETYPES: dict[TokenArchetype, ArchetypeDefinition] = {
    TokenArchetype.MONETARY_NETWORK: ArchetypeDefinition(
        archetype=TokenArchetype.MONETARY_NETWORK,
        name="Monetary network",
        explanation=(
            "Read as a monetary asset on its own chain. Its case rests "
            "on a fixed and terminal issuance, on what it costs to "
            "attack the network, and on being held — not on what the "
            "network earns. It is not asked a protocol's revenue "
            "questions, and the absence of them is not a gap."
        ),
        capabilities=(
            AnalyticalCapability.MARKET_ASSET,
            AnalyticalCapability.MONETARY_NETWORK,
        ),
    ),
    TokenArchetype.SMART_CONTRACT_NETWORK: ArchetypeDefinition(
        archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
        name="Smart-contract network",
        explanation=(
            "Read as a programmable settlement layer: whether it is "
            "used, what capital is committed to it, what that use pays, "
            "and whether any of it reaches the token."
        ),
        capabilities=(
            AnalyticalCapability.MARKET_ASSET,
            AnalyticalCapability.SMART_CONTRACT_NETWORK,
            AnalyticalCapability.TOKEN_VALUE_CAPTURE,
        ),
    ),
    TokenArchetype.SCALING_NETWORK: ArchetypeDefinition(
        archetype=TokenArchetype.SCALING_NETWORK,
        name="Scaling network",
        explanation=(
            "Read as a network that settles on another network. It is "
            "asked everything a settlement layer is asked, and two "
            "things more: what it depends on to settle, and who "
            "operates it — because both sit between its usage and its "
            "token."
        ),
        capabilities=(
            AnalyticalCapability.MARKET_ASSET,
            AnalyticalCapability.SMART_CONTRACT_NETWORK,
            AnalyticalCapability.SCALING_INFRASTRUCTURE,
            AnalyticalCapability.TOKEN_VALUE_CAPTURE,
        ),
    ),
    TokenArchetype.APPLICATION_PROTOCOL: ArchetypeDefinition(
        archetype=TokenArchetype.APPLICATION_PROTOCOL,
        name="Application protocol",
        explanation=(
            "Read as an application that charges for a service and runs "
            "on infrastructure it does not own. Its network's questions "
            "are not its own, and the question that decides its case is "
            "whether what it charges reaches its token."
        ),
        capabilities=(
            AnalyticalCapability.MARKET_ASSET,
            AnalyticalCapability.PROTOCOL_ECONOMICS,
            AnalyticalCapability.TOKEN_VALUE_CAPTURE,
        ),
    ),
    TokenArchetype.EXCHANGE_NETWORK: ArchetypeDefinition(
        archetype=TokenArchetype.EXCHANGE_NETWORK,
        name="Exchange network",
        explanation=(
            "Read as a trading venue that runs its own settlement "
            "layer. Not a special case: it composes the network lens "
            "and the venue lens because both are real for it, and its "
            "two economic entities are measured apart."
        ),
        capabilities=(
            AnalyticalCapability.MARKET_ASSET,
            AnalyticalCapability.SMART_CONTRACT_NETWORK,
            AnalyticalCapability.VENUE_ECONOMICS,
            AnalyticalCapability.PROTOCOL_ECONOMICS,
            AnalyticalCapability.TOKEN_VALUE_CAPTURE,
        ),
    ),
    TokenArchetype.STABLECOIN: ArchetypeDefinition(
        archetype=TokenArchetype.STABLECOIN,
        name="Stablecoin",
        explanation=(
            "Read as a claim on a reserve rather than as a network "
            "asset. Nothing in this platform's crypto question set "
            "answers it yet, and the boundary is declared so that it "
            "can never be read through a monetary asset's scarcity "
            "questions or a protocol's accrual questions — for a "
            "stablecoin, both are the wrong instrument."
        ),
        capabilities=(AnalyticalCapability.MARKET_ASSET,),
        unmodelled=(
            "the quality and composition of the reserve",
            "peg stability against the asset it tracks",
            "redemption — who may redeem, at what size, and how quickly",
            "the issuer and the counterparty risk it carries",
            "liquidity across venues under stress",
            "concentration of holdings and of redemption rights",
        ),
    ),
    TokenArchetype.UNKNOWN: ArchetypeDefinition(
        archetype=TokenArchetype.UNKNOWN,
        name="Not classified",
        explanation=(
            "No archetype was established for this security on evidence "
            "this platform holds. It is read only as a traded asset, "
            "and every question that depends on what kind of system it "
            "is reads as undetermined rather than as inapplicable — "
            "this platform does not know, which is a different thing "
            "from the question not applying."
        ),
        capabilities=(AnalyticalCapability.MARKET_ASSET,),
    ),
}


class ArchetypeConfidence(StrEnum):
    """How firmly the archetype itself is held."""

    #: Decided by facts this platform holds and can re-check: the kind
    #: of the mapped entities, what the provider's methodology defines
    #: for them, the token's own supply facts.
    STRUCTURAL = "structural"

    #: Verified by hand against the sources and argued from them. Real
    #: evidence, and a reading of it — stated so it can be contested.
    REASONED = "reasoned"

    #: Nothing established it.
    UNESTABLISHED = "unestablished"

    @property
    def stated(self) -> str:
        return _CONFIDENCE[self]


_CONFIDENCE = {
    ArchetypeConfidence.STRUCTURAL: "Structural — from facts held here",
    ArchetypeConfidence.REASONED: "Reasoned — argued from the sources",
    ArchetypeConfidence.UNESTABLISHED: "Not established",
}


@dataclass(frozen=True, slots=True)
class ConsideredArchetype:
    """An archetype weighed and not chosen, with the reason it was not.

    The same courtesy `NotSelected` pays on the equity side. A reader
    who is told an asset is a scaling network is owed the answer to
    "why not simply a smart-contract network?", and the answer is a
    fact rather than a preference.
    """

    archetype: TokenArchetype
    not_chosen_because: str


@dataclass(frozen=True, slots=True)
class ArchetypeAssignment:
    """One security's archetype, and the whole account of it."""

    symbol: str
    archetype: TokenArchetype
    confidence: ArchetypeConfidence

    #: Why this archetype, in one sentence.
    because: str

    #: The evidence consulted, worded — each line a fact this platform
    #: holds and a reader can go and check.
    rests_on: tuple[str, ...]

    #: What this assignment does *not* establish. Carried because an
    #: archetype names a kind, and a kind is not a verdict: an exchange
    #: network is not thereby a good one.
    does_not_establish: tuple[str, ...] = ()

    alternatives: tuple[ConsideredArchetype, ...] = ()

    #: Evidence this platform holds and deliberately did not classify
    #: from. Stated rather than omitted: a reader cannot otherwise tell
    #: a label that was refused from one that was never available.
    not_classified_from: tuple[str, ...] = ()

    @property
    def definition(self) -> ArchetypeDefinition:
        return ARCHETYPES[self.archetype]

    @property
    def capabilities(self) -> tuple[AnalyticalCapability, ...]:
        return self.definition.capabilities

    @property
    def is_established(self) -> bool:
        return self.archetype is not TokenArchetype.UNKNOWN


#: Evidence held about every token and never used to classify one.
#:
#: TokenInsight grades all five rated corpus members and scores six
#: named dimensions for each — "Token economics", "Ecosystem
#: development" — and a dimension label is not a description of an
#: economic design. It is another party's opinion, kept under their
#: name (PR #94) and consumed by nothing, here included.
_REFUSED_BASES = (
    "TokenInsight's letter grade and its six dimension scores — another "
    "party's opinion, not evidence of what the system is",
)


#: The archetype of each security in the corpus, with its basis.
#:
#: Hand-assigned and hand-verified, exactly as `PROTOCOL_ENTITIES` is,
#: and for the same reason: this platform reads market data and filings,
#: not whitepapers, so the honest form of a classification is a stated
#: claim with the evidence beside it rather than a derivation that
#: pretends more was read than was. Every `rests_on` line names
#: something in the stores.
#:
#: A security absent from this table is `UNKNOWN`. It is never assigned
#: an archetype by resemblance to one that is here.
ASSIGNMENTS: dict[str, ArchetypeAssignment] = {
    "BTC": ArchetypeAssignment(
        symbol="BTC",
        archetype=TokenArchetype.MONETARY_NETWORK,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "A chain whose asset is capped and nearly fully issued, and "
            "for which the fee source defines no mechanism reaching "
            "holders at all. Both halves are facts held here, and "
            "together they describe an asset held for scarcity rather "
            "than for what the network pays."
        ),
        rests_on=(
            "one mapped entity, and it is a chain (Bitcoin)",
            "a stated maximum supply of 21,000,000 with 95.6% already "
            "issued — established across three sources",
            "DefiLlama defines fees and protocol revenue for Bitcoin "
            "and defines no holder-revenue mechanism, which under S2's "
            "sibling rule is evidence that no such mechanism exists "
            "rather than that a figure is missing",
        ),
        does_not_establish=(
            "that the issuance schedule cannot be changed, or by whom — "
            "this platform holds the cap, not the rule that sets it",
            "who receives the fees users pay; the source records what "
            "is paid and not where it goes",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
                not_chosen_because=(
                    "the chain does carry $3.56bn of capital in "
                    "applications, and reading it as a settlement layer "
                    "would make that figure the case. It is 0.3% of the "
                    "asset's market value, and the monetary lens does "
                    "not rest on what is built on the chain."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "ETH": ArchetypeAssignment(
        symbol="ETH",
        archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "A chain that charges for computation and burns part of "
            "what it charges. The provider's own methodology names both "
            "halves, so usage, what usage pays, and what reaches the "
            "token are three questions with evidence behind each."
        ),
        rests_on=(
            "one mapped entity, and it is a chain (Ethereum)",
            "DefiLlama defines fees, protocol revenue and holder "
            "revenue for it — the fee family is complete",
            'its holder-revenue methodology reads "Amount of ETH burned '
            '— base fees plus blob fees", a mechanism naming the asset',
            "$41.99bn of capital committed in applications on the chain",
        ),
        does_not_establish=(
            "that burning is worth more or less to a holder than a "
            "distribution would be — that is an interpretation, and S3 "
            "makes none",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.MONETARY_NETWORK,
                not_chosen_because=(
                    "it has no stated maximum supply, so the scarcity "
                    "question a monetary asset turns on cannot even be "
                    "asked of it, and its fee economy is real enough to "
                    "be the case rather than a footnote."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "SOL": ArchetypeAssignment(
        symbol="SOL",
        archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "The same shape as Ethereum's, established the same way: a "
            "chain with a complete fee family and a burn mechanism the "
            "source states in its own words."
        ),
        rests_on=(
            "one mapped entity, and it is a chain (Solana)",
            "DefiLlama defines fees, protocol revenue and holder revenue for it",
            'its holder-revenue methodology reads "Transaction base '
            'fees paid by users were burned"',
            "$4.86bn of capital committed in applications on the chain",
        ),
        does_not_establish=(
            "how the burned share compares with what the network issues "
            "— this platform holds neither an issuance rate nor a net "
            "supply change",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.MONETARY_NETWORK,
                not_chosen_because=(
                    "no stated maximum supply, and a fee economy an "
                    "order of magnitude larger than Bitcoin's on the "
                    "same day."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "ADA": ArchetypeAssignment(
        symbol="ADA",
        archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "A chain that charges for use and carries capital in "
            "applications, at a far smaller scale than its peers. Scale "
            "is not a different kind of thing, and no archetype here is "
            "chosen by size."
        ),
        rests_on=(
            "one mapped entity, and it is a chain (Cardano)",
            "DefiLlama defines fees and protocol revenue for it",
            "$70.4m of capital committed in applications on the chain",
            "a stated maximum supply of 45bn, 86.2% issued",
        ),
        does_not_establish=(
            "any mechanism reaching holders: the source defines fees "
            'and protocol revenue for it — the latter as "Burned '
            'coins" — and defines no holder revenue, while defining one '
            "for Ethereum and Solana on identical burn wording. The "
            "question stands open on a provider inconsistency, not on a "
            "property of the chain",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.MONETARY_NETWORK,
                not_chosen_because=(
                    "it has a stated cap, which is the one monetary "
                    "signal it shows — and a chain that charges for "
                    "computation and hosts applications is read as what "
                    "it does, not as what its supply schedule "
                    "resembles."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "ARB": ArchetypeAssignment(
        symbol="ARB",
        archetype=TokenArchetype.SCALING_NETWORK,
        confidence=ArchetypeConfidence.REASONED,
        because=(
            "A settlement layer that does not settle on itself. Its "
            "users pay gas in another network's asset, which puts a "
            "dependency and an operator between the network's usage and "
            "its token — two questions no unlayered chain is asked."
        ),
        rests_on=(
            "one mapped entity, and it is a chain (Arbitrum)",
            "the S2 entity mapping records that the rollup's gas is "
            "paid in ETH, and flags the mapping unsettled for exactly "
            "that reason",
            "DefiLlama defines fees and protocol revenue for it and "
            "defines no holder revenue",
            "$1.20bn of capital committed in applications on the chain",
        ),
        does_not_establish=(
            "who operates the sequencer, what it earns, or where that "
            "goes — none of it is held here",
            "any mechanism by which the network's fees reach ARB. The "
            'source records protocol revenue as "Burned coins" without '
            "saying whose, and burning another network's asset is not "
            "accrual to this one",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
                not_chosen_because=(
                    "it is one, and it is not only one. Reading it as "
                    "an unlayered chain would drop the settlement "
                    "dependency and the operator question, and those "
                    "are where its token's case is decided."
                ),
            ),
            ConsideredArchetype(
                archetype=TokenArchetype.APPLICATION_PROTOCOL,
                not_chosen_because=(
                    "an application runs on infrastructure it does not "
                    "own; this is infrastructure, with its own capital "
                    "committed and its own fee line."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "HYPE": ArchetypeAssignment(
        symbol="HYPE",
        archetype=TokenArchetype.EXCHANGE_NETWORK,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "Two economic entities are mapped to this one security and "
            "both are real: a trading venue with a book, and the chain "
            "it settles on. The venue lens and the network lens are "
            "composed rather than one of them being chosen, because "
            "choosing would discard evidence."
        ),
        rests_on=(
            "two mapped entities — Hyperliquid the venue (a protocol) "
            "and Hyperliquid L1 (a chain) — measured 224x apart on fees "
            "and 5.2x apart on capital",
            "the venue publishes DEX volume and open interest, which only a book has",
            "the venue's fee methodology names the token: 99% of perp "
            "and spot fees buy HYPE through an Assistance Fund",
            "the chain carries $1.20bn of capital and its own gas line",
        ),
        does_not_establish=(
            "that the accrual is large, durable or worth what it costs "
            "— the mechanism is evidenced, the judgment is not made",
            "which entity's economics should weigh more; they are shown "
            "apart and never summed",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.APPLICATION_PROTOCOL,
                not_chosen_because=(
                    "it would drop the chain entirely, and the chain is "
                    "a separately measured entity holding $1.20bn — an "
                    "application protocol is one that runs on "
                    "infrastructure it does not own."
                ),
            ),
            ConsideredArchetype(
                archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
                not_chosen_because=(
                    "it would drop the venue, which is where 99.6% of "
                    "the fees are earned and where the mechanism that "
                    "names the token lives."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "1INCH": ArchetypeAssignment(
        symbol="1INCH",
        archetype=TokenArchetype.APPLICATION_PROTOCOL,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because=(
            "An application with a fee line and no infrastructure of "
            "its own. It routes trades to other venues, so it holds no "
            "capital and runs no book — and the questions those would "
            "answer are not thin evidence about it, they are not "
            "questions about it."
        ),
        rests_on=(
            "one mapped entity, and it is a protocol (1inch)",
            "S2 declined TVL, DEX volume and open interest for it, each "
            "with a stated reason about what an aggregator is",
            "DefiLlama reports fees and protocol revenue for it and "
            "publishes no methodology for either",
        ),
        does_not_establish=(
            "where the fees go: the source states no methodology at "
            "all for this protocol, so the accrual question has no "
            "evidence rather than a negative answer",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.EXCHANGE_NETWORK,
                not_chosen_because=(
                    "the provider's DEX list holds *1inch Aqua*, a "
                    "different product. Mapping it here would have "
                    "given the aggregator another business's book, and "
                    "a shared name is not an identity."
                ),
            ),
        ),
        not_classified_from=_REFUSED_BASES,
    ),
    "TAO": ArchetypeAssignment(
        symbol="TAO",
        archetype=TokenArchetype.UNKNOWN,
        confidence=ArchetypeConfidence.UNESTABLISHED,
        because=(
            "The only economic evidence held for this network is a "
            "capital figure. No source this platform reads publishes "
            "what the network charges for, or what it does with the "
            "charge, so nothing here distinguishes one kind of network "
            "from another. It is read as a traded asset and no further."
        ),
        rests_on=(
            "one mapped entity, a chain (Bittensor), whose economic "
            "link to the token S2 flagged unsettled",
            "DefiLlama defines capital held and nothing else for it — "
            "no fee methodology, so its silence about fees is a gap and "
            "not a finding",
            "a stated maximum supply of 21,000,000 with 41.2% issued, "
            "and the two sources 11.3% apart on the count",
        ),
        does_not_establish=(
            "anything about the network's design. A capped supply is "
            "shared with Bitcoin and says nothing on its own",
        ),
        alternatives=(
            ConsideredArchetype(
                archetype=TokenArchetype.SMART_CONTRACT_NETWORK,
                not_chosen_because=(
                    "no fee evidence and $45.0m of capital, three "
                    "orders of magnitude below Ethereum's. Assigning it "
                    "would give the security five questions this "
                    "platform has no evidence even applies to it."
                ),
            ),
            ConsideredArchetype(
                archetype=TokenArchetype.MONETARY_NETWORK,
                not_chosen_because=(
                    "the capped supply is the only monetary signal, and "
                    "a cap alone would classify every capped token as "
                    "money."
                ),
            ),
        ),
        not_classified_from=(
            *_REFUSED_BASES,
            "the asset's popular description as an AI network — this "
            "platform holds no category field for it, and a category "
            "would not be evidence of an economic design if it did",
        ),
    ),
}


def archetype_for(symbol: str) -> ArchetypeAssignment:
    """This security's archetype, or the honest absence of one."""

    normalized = symbol.upper().strip()

    assignment = ASSIGNMENTS.get(normalized)

    if assignment is not None:
        return assignment

    return ArchetypeAssignment(
        symbol=normalized,
        archetype=TokenArchetype.UNKNOWN,
        confidence=ArchetypeConfidence.UNESTABLISHED,
        because=(
            f"No archetype has been established for {normalized}. It is "
            "not in the corpus this platform has read, and resembling "
            "one that is would not be evidence about it."
        ),
        rests_on=(),
    )
