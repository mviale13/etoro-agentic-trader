"""Where a system's economic value goes — and why "fees" is four words.

The measurement that makes the S2 corpus analytically usable. Three
entities in it report a fee figure and mean three different things by
it:

```text
Bitcoin     users pay $139.0k/day   → the source records who pays and
                                      not who receives, and defines no
                                      holder mechanism at all
Ethereum    users pay $175.2k/day   → "Amount of ETH burned — base fees
                                      plus blob fees"
Hyperliquid users pay $842.7k/day   → "99% of fees go to Assistance Fund
                                      for buying HYPE tokens"
```

Scoring those three figures on one scale would rank Bitcoin's security
budget against Hyperliquid's buyback as though they were the same
quantity. They are not comparable, and what separates them is not a
number — it is the sentence the source publishes beside it.

So the chain is modelled as four stages, and the mechanism at the last
one is **recognised from the provider's own wording**, never declared
here. Where the source publishes no wording, the mechanism is *not
recorded*, which is different again from a source that publishes a fee
family and pointedly omits the holder half — the absence S2 already
reads as evidence.

The verbatim sentence always travels with the label. The label is a
convenience for a test and a surface; the sentence is the evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import (
    MetricAvailability,
    ProtocolEntity,
    ProtocolEntityKind,
    ProtocolFundamentals,
    ProtocolMetric,
)


class ValueStage(StrEnum):
    """The four questions the word "revenue" routinely collapses."""

    #: Is the system used?
    USAGE = "usage"

    #: Does that use pay anything?
    FEES = "fees"

    #: Does the system itself keep any of it?
    PROTOCOL_CAPTURE = "protocol_capture"

    #: Does any of it reach the token?
    HOLDER_ACCRUAL = "holder_accrual"

    @property
    def label(self) -> str:
        return _STAGES[self]


_STAGES = {
    ValueStage.USAGE: "Used",
    ValueStage.FEES: "Paid for",
    ValueStage.PROTOCOL_CAPTURE: "Kept by the system",
    ValueStage.HOLDER_ACCRUAL: "Reaching the token",
}


class ValueFlowKind(StrEnum):
    """How value reaches the token, where a source says that it does.

    Every member below is earned by a sentence in the corpus. A
    mechanism nobody has published wording for does not get a name here
    — it would be a category waiting for evidence, which is the shape
    of every taxonomy this platform refuses to build.
    """

    #: The asset is destroyed, so every remaining unit is a larger
    #: share of the whole. Ethereum and Solana.
    BURNED = "burned"

    #: The asset is bought on the market with the proceeds. Hyperliquid,
    #: whose source names the token in the mechanism.
    TOKEN_BUYBACK = "token_buyback"

    #: The proceeds are paid to holders as holders.
    DISTRIBUTED_TO_HOLDERS = "distributed_to_holders"

    #: A figure exists and the source publishes no mechanism for it. The
    #: amount is known and what it means is not.
    NOT_RECORDED = "not_recorded"

    #: The source defines the rest of the fee family for this entity and
    #: defines no holder mechanism. Under S2's sibling rule that is
    #: evidence the mechanism does not exist here, rather than a figure
    #: missing today.
    NOT_PRESENT = "not_present"

    #: Nothing has been read for this entity at all.
    UNREAD = "unread"

    @property
    def stated(self) -> str:
        return _MECHANISMS[self]


_MECHANISMS = {
    ValueFlowKind.BURNED: "Burned",
    ValueFlowKind.TOKEN_BUYBACK: "Buys the token",
    ValueFlowKind.DISTRIBUTED_TO_HOLDERS: "Paid to holders",
    ValueFlowKind.NOT_RECORDED: "Mechanism not recorded",
    ValueFlowKind.NOT_PRESENT: "No mechanism here",
    ValueFlowKind.UNREAD: "Nothing read",
}


#: Wording that identifies a mechanism, most specific first.
#:
#: Order is load-bearing. Hyperliquid's methodology describes three
#: child protocols in one sentence and contains both "buying HYPE
#: tokens" and "going to governance token holders"; the buyback clause
#: covers 99% of the fees and names the asset, so it is recognised
#: first. The full sentence is retained either way, which is what an
#: investor actually reads.
_PATTERNS: tuple[tuple[ValueFlowKind, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ValueFlowKind.TOKEN_BUYBACK,
        ("buying", "buy back", "buyback", "repurchas"),
        ("token", "coin"),
    ),
    (ValueFlowKind.BURNED, ("burn",), ()),
    (ValueFlowKind.DISTRIBUTED_TO_HOLDERS, ("holder",), ()),
)


def recognise(methodology: str | None) -> ValueFlowKind | None:
    """The mechanism a source's own wording describes, or nothing.

    Deliberately conservative. An unrecognised sentence returns None and
    is shown verbatim rather than being forced into the nearest member —
    a mechanism this platform has not learned to read is a gap in the
    reader, and labelling it anyway would put a wrong word beside a real
    quotation.
    """

    if not methodology:
        return None

    text = methodology.casefold()

    for kind, verbs, qualifiers in _PATTERNS:
        if not any(verb in text for verb in verbs):
            continue

        if qualifiers and not any(word in text for word in qualifiers):
            continue

        return kind

    return None


@dataclass(frozen=True, slots=True)
class ValueChainLink:
    """One stage of one entity's value chain, with its evidence."""

    stage: ValueStage

    #: The metric that measures this stage, where one does.
    metric: ProtocolMetric | None

    #: The figure, where the standing permits one to be shown at all.
    value: float | None

    window: str | None

    standing: EvidenceStanding
    availability: MetricAvailability

    #: The source's own definition of this figure for this entity,
    #: verbatim. The evidence, as opposed to the label above it.
    methodology: str | None

    #: This platform's account of the standing or the absence.
    because: str | None


@dataclass(frozen=True, slots=True)
class ValueChain:
    """How one entity's economics move, from use to the token."""

    entity: ProtocolEntity
    links: tuple[ValueChainLink, ...]

    #: What the source's wording says happens at the last stage.
    mechanism: ValueFlowKind

    #: The mechanism in the source's own words, where it published any.
    mechanism_stated: str | None

    #: This platform's account of the mechanism — what it is, whose
    #: sentence established it, and what it does not establish.
    because: str

    def link(self, stage: ValueStage) -> ValueChainLink | None:
        for link in self.links:
            if link.stage is stage:
                return link

        return None

    @property
    def reaches_the_token(self) -> bool:
        """Whether a source describes value reaching the token at all.

        Not a judgment about how much, and never a verdict: a
        mechanism can be evidenced and worthless. It answers only
        whether the accrual question has a mechanism behind it.
        """

        return self.mechanism in (
            ValueFlowKind.BURNED,
            ValueFlowKind.TOKEN_BUYBACK,
            ValueFlowKind.DISTRIBUTED_TO_HOLDERS,
        )


#: Which metric measures usage, by the kind of thing being used. A
#: chain's usage is transaction activity, which no source this platform
#: reads publishes — so the stage exists, holds no metric, and says so.
_USAGE_METRIC: dict[ProtocolEntityKind, ProtocolMetric | None] = {
    ProtocolEntityKind.CHAIN: None,
    ProtocolEntityKind.PROTOCOL: ProtocolMetric.DEX_VOLUME,
}


def value_chains(fundamentals: ProtocolFundamentals) -> tuple[ValueChain, ...]:
    """One chain per mapped entity — never one chain per security.

    The discipline S2 established, carried into interpretation: a
    security with a venue and a chain has two value chains that are
    read apart, because a figure from one substituted for the other
    misstates the business by whatever factor separates them.
    """

    return tuple(_chain(fundamentals, entity) for entity in fundamentals.entities)


def _chain(
    fundamentals: ProtocolFundamentals,
    entity: ProtocolEntity,
) -> ValueChain:
    usage_metric = _USAGE_METRIC[entity.kind]

    links = (
        _link(fundamentals, entity, ValueStage.USAGE, usage_metric),
        _link(fundamentals, entity, ValueStage.FEES, ProtocolMetric.FEES),
        _link(
            fundamentals,
            entity,
            ValueStage.PROTOCOL_CAPTURE,
            ProtocolMetric.PROTOCOL_REVENUE,
        ),
        _link(
            fundamentals,
            entity,
            ValueStage.HOLDER_ACCRUAL,
            ProtocolMetric.HOLDER_REVENUE,
        ),
    )

    accrual = links[-1]

    mechanism, because = _mechanism(entity, accrual)

    return ValueChain(
        entity=entity,
        links=links,
        mechanism=mechanism,
        mechanism_stated=accrual.methodology,
        because=because,
    )


def _link(
    fundamentals: ProtocolFundamentals,
    entity: ProtocolEntity,
    stage: ValueStage,
    metric: ProtocolMetric | None,
) -> ValueChainLink:
    if metric is None:
        return ValueChainLink(
            stage=stage,
            metric=None,
            value=None,
            window=None,
            standing=EvidenceStanding.ABSENT,
            availability=MetricAvailability.UNAVAILABLE_FREE,
            methodology=None,
            because=(
                f"No source this platform reads publishes a usage "
                f"measure for a {entity.kind.stated}. What it charges is "
                "read at the next stage, and charging is not using."
            ),
        )

    fact = fundamentals.fact(metric, entity.key)

    if fact is None:
        return ValueChainLink(
            stage=stage,
            metric=metric,
            value=None,
            window=None,
            standing=EvidenceStanding.ABSENT,
            availability=MetricAvailability.UNAVAILABLE_FREE,
            methodology=None,
            because=f"Nothing has been read for {entity.name}.",
        )

    return ValueChainLink(
        stage=stage,
        metric=metric,
        value=fact.value if fact.standing.serves_value else None,
        window=fact.window,
        standing=fact.standing,
        availability=fact.availability,
        methodology=fact.provider_methodology,
        because=fact.because,
    )


def _mechanism(
    entity: ProtocolEntity,
    accrual: ValueChainLink,
) -> tuple[ValueFlowKind, str]:
    """What the last link's own wording establishes, and what it does not."""

    unsettled = (
        ""
        if entity.mapping_settled
        else (
            " The entity is mapped and what its economics mean for this "
            "token is not settled, so nothing here may be read as the "
            "token's own."
        )
    )

    if accrual.availability is MetricAvailability.NOT_APPLICABLE:
        return (
            ValueFlowKind.NOT_PRESENT,
            (
                f"The source defines the rest of the fee family for "
                f"{entity.name} and defines no mechanism reaching "
                "holders. Under the sibling rule that is evidence there "
                "is none, rather than a figure missing today." + unsettled
            ),
        )

    recognised = recognise(accrual.methodology)

    if recognised is not None:
        return (
            recognised,
            (
                f"The source's own definition for {entity.name} "
                f"describes this: {accrual.methodology!r}. It "
                "establishes that the question applies and that a "
                "mechanism exists. It establishes nothing about how "
                "much this is worth to a holder, and no figure here is "
                "corroborated." + unsettled
            ),
        )

    if accrual.methodology:
        return (
            ValueFlowKind.NOT_RECORDED,
            (
                f"The source publishes a definition for {entity.name} "
                "that this platform does not recognise as any mechanism "
                f"it has learned to read: {accrual.methodology!r}. It is "
                "shown as written and interpreted no further." + unsettled
            ),
        )

    if accrual.value is not None:
        return (
            ValueFlowKind.NOT_RECORDED,
            (
                f"The source reports a figure for {entity.name} and "
                "publishes no definition of it. The amount is known and "
                "what it means is not, so it cannot be read as evidence "
                "of any particular mechanism." + unsettled
            ),
        )

    if accrual.availability is MetricAvailability.UNAVAILABLE_FREE:
        return (
            ValueFlowKind.UNREAD,
            (
                f"Nothing this platform reads publishes a holder "
                f"mechanism for {entity.name}, and nothing rules one "
                "out either. The question stands open on absent "
                "evidence." + unsettled
            ),
        )

    return (
        ValueFlowKind.UNREAD,
        (
            f"No usable reading of a holder mechanism exists for "
            f"{entity.name}." + unsettled
        ),
    )
