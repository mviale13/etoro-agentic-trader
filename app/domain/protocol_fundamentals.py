"""What the economic system behind a token earns, and who receives it.

The second canonical evidence family, kept apart from token market
facts on purpose. They answer different questions about different
subjects and fail independently: a token's market value can be
CONFLICTED while its protocol's fees are perfectly well evidenced, and
neither state says anything about the other.

Three disciplines this module exists to enforce.

**Identity before economics.** A security is not a protocol. DefiLlama
measures *Hyperliquid the protocol* — the perpetuals and spot books,
$842k of fees a day — and separately *Hyperliquid L1 the chain*, whose
gas fees are $3.8k a day. Same name, same token, two entities, a factor
of 224 apart; their TVL differs by 5x. Which entity generated a figure
is part of the figure, so a security maps to named entities with a
stated basis, and a fact always names the entity it measures.

**Fees, protocol revenue and holder revenue are three concepts.** The
difference between them *is* the investment question. A protocol can
earn enormously and pass its token holders nothing; DefiLlama's own
methodology for Hyperliquid Perps says the protocol keeps no fees and
99% goes to an Assistance Fund that buys HYPE. That sentence is
evidence, carried verbatim, and it is why value generation and holder
accrual are separate families here rather than one "revenue".

**Observation and arithmetic are different claims.** A day's holder
revenue is something a source observed. A year's run rate is this
platform multiplying it by 365 — a derivation, labelled as one, with
the observation it rests on named. A one-day annualisation must never
read as a historical annual figure.

Nothing here scores, bands or interprets. No factor consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.evidence_standing import EvidenceStanding


class ProtocolEntityKind(StrEnum):
    """What kind of thing the economics are measured over."""

    #: A blockchain. Its fees are what users pay to transact on it.
    CHAIN = "chain"

    #: An application or venue. Its fees are what users pay to use it,
    #: and it may run on a chain it does not own.
    PROTOCOL = "protocol"

    @property
    def stated(self) -> str:
        return "chain" if self is ProtocolEntityKind.CHAIN else "protocol"


@dataclass(frozen=True, slots=True)
class ProtocolEntity:
    """One economic system, named independently of any provider.

    `key` is this platform's own stable identifier; provider slugs live
    in the adapters and never reach here. `measures` says in plain
    words what generated the figures, because a reader comparing $842k
    a day with $3.8k a day needs to know they are not two readings of
    one thing.
    """

    key: str
    name: str
    kind: ProtocolEntityKind

    #: What this entity's economics actually are, in one sentence.
    measures: str

    #: Why this platform believes the security and the entity belong
    #: together — the mapping's own evidence, stated so it can be
    #: challenged. Symbol equality is never a basis on its own.
    mapping_basis: str

    #: False where the mapping is real but the economic relationship to
    #: the token is not settled — the fact is acquired and shown, and
    #: nothing may reason from it as though the link were established.
    mapping_settled: bool = True


class ProtocolMetric(StrEnum):
    """The protocol facts this platform knows how to hold."""

    TVL = "tvl"
    FEES = "fees"
    PROTOCOL_REVENUE = "protocol_revenue"
    HOLDER_REVENUE = "holder_revenue"
    DEX_VOLUME = "dex_volume"
    OPEN_INTEREST = "open_interest"


class MetricFamily(StrEnum):
    """What a metric is evidence *about* — never collapsed together."""

    #: How much capital the system holds.
    CAPITAL = "capital"

    #: How much the system is used.
    ACTIVITY = "activity"

    #: What the system earns from that use.
    VALUE_GENERATION = "value_generation"

    #: What reaches the token's holders. The question a protocol's
    #: earnings cannot answer on their own.
    HOLDER_ACCRUAL = "holder_accrual"


class Periodicity(StrEnum):
    """What the number covers in time — never assumed from its size."""

    #: A level at a moment: TVL, open interest. Summing these over days
    #: produces a figure that means nothing.
    INSTANT = "instant"

    #: An amount accumulated over the stated window.
    FLOW = "flow"


@dataclass(frozen=True, slots=True)
class MetricSemantics:
    """Exactly what one metric means, before any value is attached."""

    metric: ProtocolMetric
    label: str
    family: MetricFamily
    periodicity: Periodicity

    #: This platform's own definition, independent of any provider.
    definition: str

    unit: str = "usd"


SEMANTICS: dict[ProtocolMetric, MetricSemantics] = {
    ProtocolMetric.TVL: MetricSemantics(
        metric=ProtocolMetric.TVL,
        label="Total value locked",
        family=MetricFamily.CAPITAL,
        periodicity=Periodicity.INSTANT,
        definition=(
            "The value of assets held in the entity at the moment of "
            "reading, as the provider computes it. A level, not a flow: "
            "it is never summed across days."
        ),
    ),
    ProtocolMetric.FEES: MetricSemantics(
        metric=ProtocolMetric.FEES,
        label="Fees paid by users",
        family=MetricFamily.VALUE_GENERATION,
        periodicity=Periodicity.FLOW,
        definition=(
            "What users paid to use the entity over the window. The "
            "gross figure, before any split between the protocol, its "
            "suppliers and its token holders."
        ),
    ),
    ProtocolMetric.PROTOCOL_REVENUE: MetricSemantics(
        metric=ProtocolMetric.PROTOCOL_REVENUE,
        label="Protocol revenue",
        family=MetricFamily.VALUE_GENERATION,
        periodicity=Periodicity.FLOW,
        definition=(
            "The share of fees the protocol itself retains over the "
            "window. Distinct from fees, and distinct again from what "
            "reaches token holders — a protocol can retain nothing and "
            "still direct everything to its holders, or the reverse."
        ),
    ),
    ProtocolMetric.HOLDER_REVENUE: MetricSemantics(
        metric=ProtocolMetric.HOLDER_REVENUE,
        label="Holder revenue",
        family=MetricFamily.HOLDER_ACCRUAL,
        periodicity=Periodicity.FLOW,
        definition=(
            "The share of fees that reaches the token's holders over "
            "the window, by the mechanism the provider's methodology "
            "describes. It is the only metric here that is evidence "
            "about the token rather than about the system."
        ),
    ),
    ProtocolMetric.DEX_VOLUME: MetricSemantics(
        metric=ProtocolMetric.DEX_VOLUME,
        label="DEX volume",
        family=MetricFamily.ACTIVITY,
        periodicity=Periodicity.FLOW,
        definition=(
            "Value traded through the entity's spot venue over the "
            "window. Activity on one venue — not the token's market "
            "volume, and not comparable with a vendor's tracked "
            "exchange aggregate."
        ),
    ),
    ProtocolMetric.OPEN_INTEREST: MetricSemantics(
        metric=ProtocolMetric.OPEN_INTEREST,
        label="Open interest",
        family=MetricFamily.ACTIVITY,
        periodicity=Periodicity.INSTANT,
        definition=(
            "The notional value of derivative positions open on the "
            "entity at the moment of reading. A level, not a flow: the "
            "provider also publishes cumulative fields for it, and "
            "those are sums of daily levels that mean nothing."
        ),
    ),
}


class MetricAvailability(StrEnum):
    """Why a metric has no value here — five different situations.

    Confusing these is how a dossier shows Bitcoin as incomplete for
    lacking a protocol's revenue. They are kept apart so an absence
    always says which kind it is.
    """

    #: A value was read.
    AVAILABLE = "available"

    #: The question does not apply to this entity. Not a gap.
    NOT_APPLICABLE = "not_applicable"

    #: Applicable, and no free source publishes it.
    UNAVAILABLE_FREE = "unavailable_free"

    #: Applicable and published, and what the figure means is not
    #: settled enough to serve.
    SEMANTICS_UNRESOLVED = "semantics_unresolved"

    #: No entity could be mapped, so there is nothing to measure.
    IDENTITY_UNRESOLVED = "identity_unresolved"

    @property
    def stated(self) -> str:
        return _AVAILABILITY[self]


_AVAILABILITY = {
    MetricAvailability.AVAILABLE: "Available",
    MetricAvailability.NOT_APPLICABLE: "Not applicable",
    MetricAvailability.UNAVAILABLE_FREE: "Not available free",
    MetricAvailability.SEMANTICS_UNRESOLVED: "Semantics unresolved",
    MetricAvailability.IDENTITY_UNRESOLVED: "Identity unresolved",
}


@dataclass(frozen=True, slots=True)
class ProtocolFact:
    """One protocol figure, with everything needed to read it honestly."""

    metric: ProtocolMetric
    entity: ProtocolEntity

    availability: MetricAvailability
    standing: EvidenceStanding

    value: float | None = None

    #: The window the figure covers — "24 hours", "7 days" — or None
    #: for a level, which covers no window at all.
    window: str | None = None

    source: str | None = None
    observed_at: datetime | None = None

    #: The provider's own definition of this metric for this entity,
    #: verbatim. The sentence that says a protocol keeps no fees and
    #: sends 99% to a fund that buys the token is the investment case;
    #: paraphrasing it would be this platform inventing the mechanism.
    provider_methodology: str | None = None

    #: This platform's account of the standing and the availability.
    because: str | None = None

    @property
    def semantics(self) -> MetricSemantics:
        return SEMANTICS[self.metric]

    @property
    def established_value(self) -> float | None:
        """The value if established, and nothing otherwise."""

        if self.standing is EvidenceStanding.ESTABLISHED:
            return self.value

        return None


@dataclass(frozen=True, slots=True)
class DerivedProtocolFigure:
    """This platform's arithmetic over a protocol observation.

    Held apart from the observations so it can never be mistaken for
    one. A run rate is what a single window implies if it repeats; it
    is not a year that happened, and the wording says so wherever it is
    shown.
    """

    label: str
    value: float
    unit: str

    #: The arithmetic in one checkable line, naming the observation.
    stated: str

    #: What this is not, said plainly.
    caveat: str


@dataclass(frozen=True, slots=True)
class ProtocolFundamentals:
    """Everything held about the economics behind one security."""

    symbol: str

    #: The entities this security's economics are measured over. Empty
    #: where none could be mapped — which is a different state from a
    #: mapped entity with no data.
    entities: tuple[ProtocolEntity, ...]

    facts: tuple[ProtocolFact, ...]

    #: Arithmetic this platform performed, never a provider's.
    derived: tuple[DerivedProtocolFigure, ...] = ()

    #: Why no entity could be mapped, where none could.
    unmapped_because: str | None = None

    @property
    def is_applicable(self) -> bool:
        """Whether protocol economics are a question for this security.

        False only where every metric is inapplicable — a security
        whose economics are not measured by anything of this kind. It
        is never inferred from an absence of data.
        """

        return any(
            fact.availability is not MetricAvailability.NOT_APPLICABLE
            for fact in self.facts
        )

    def fact(
        self,
        metric: ProtocolMetric,
        entity_key: str | None = None,
    ) -> ProtocolFact | None:
        """One fact, optionally for a named entity."""

        for fact in self.facts:
            if fact.metric is metric and (
                entity_key is None or fact.entity.key == entity_key
            ):
                return fact

        return None

    def facts_for(self, entity_key: str) -> tuple[ProtocolFact, ...]:
        return tuple(fact for fact in self.facts if fact.entity.key == entity_key)


def annualise(fact: ProtocolFact) -> DerivedProtocolFigure | None:
    """A daily flow at a yearly run rate — this platform's arithmetic.

    Only over an established daily flow: annualising a claim would
    dress an unverified figure in arithmetic's authority, and
    annualising a level is meaningless. The caveat travels with the
    figure because the number is the one most likely to be quoted as
    though a year of it had happened.
    """

    if fact.standing is not EvidenceStanding.ESTABLISHED:
        return None

    if fact.semantics.periodicity is not Periodicity.FLOW:
        return None

    if fact.window != "24 hours" or fact.value is None:
        return None

    return DerivedProtocolFigure(
        label=f"{fact.semantics.label} at a yearly run rate",
        value=fact.value * 365,
        unit=fact.semantics.unit,
        stated=(
            f"{fact.semantics.label.lower()} of {_money(fact.value)} over "
            f"24 hours, multiplied by 365 — MOVRvest's arithmetic over "
            f"one observation, not a provider figure."
        ),
        caveat=(
            "A run rate is what one day implies if it repeats. It is "
            "not a year that happened, and a single day is not a trend."
        ),
    )


def _money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    if value >= 1_000:
        return f"${value / 1_000:,.0f}k"

    return f"${value:,.0f}"
