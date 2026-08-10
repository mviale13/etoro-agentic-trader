"""What changed in a digital asset, what may be driving it, and why it matters.

A different kind of layer from everything else in the crypto stack, and
the difference is worth stating before the code: **Asset Quality asks
what an asset durably is; this asks what is happening to it now.** The
first is deliberately slow and refuses most questions. The second is
perishable, and refusing to speak until every fact establishes would
make it useless — an investor asking *what is going on with Bitcoin*
is not served by silence.

So the discipline here is not *only established facts*. It is **every
claim carries what kind of claim it is**:

```text
MEASURED      this platform computed it from evidence it holds
REPORTED      a source states it as a fact
ATTRIBUTED    a source's interpretation, carried with the source's name
INFERRED      this platform's interpretation of evidence it holds
UNRESOLVED    sources conflict, or the evidence is missing
```

A provider paragraph — *"ETF inflows are supporting Bitcoin while
institutional interest remains high"* — is never one fact. It
decomposes: the flow is `REPORTED` and independently checkable, the
price state is `MEASURED`, the institutional interest is `INFERRED` from
holdings, and *supporting* is `ATTRIBUTED` to whoever said it. Four
claims, four standings, one sentence.

**This layer never rewrites a canonical fact.** It consumes token facts,
market context, protocol fundamentals and supply, and adds only what
those families do not carry: flows, events and narratives, each with a
time and a shelf life.

**Nothing here depends on Asset Quality.** A structural rule, not a
convention: an asset whose quality is UNKNOWN is not an asset this
platform has nothing to say about, and the two layers cannot import each
other.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.domain.crypto_event import CryptoEvent
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding


class ClaimType(StrEnum):
    """What kind of statement this is. The epistemic axis.

    Distinct from `EvidenceStanding`, which says how far a claim can be
    trusted, and from `EvidenceAuthority`, which says where it came
    from. This says *what sort of thing is being asserted* — and a
    surface that could not tell a measurement from an interpretation
    would let the second borrow the first's authority, which is the
    failure this whole platform is built against.
    """

    #: This platform computed it from evidence it holds. Re-runnable.
    MEASURED = "measured"

    #: A source states it as a fact about the world. Checkable in
    #: principle, and not checked here.
    REPORTED = "reported"

    #: A source's *interpretation*, carried with the source's name on
    #: it. "ETF inflows are supporting Bitcoin" is this, always.
    ATTRIBUTED = "attributed"

    #: This platform's interpretation of evidence it holds. Never a
    #: fact, and never presented as one.
    INFERRED = "inferred"

    #: Sources disagree, or the evidence that would settle it is
    #: missing. Shown rather than resolved.
    UNRESOLVED = "unresolved"

    @property
    def stated(self) -> str:
        return _CLAIM_TYPES[self]

    @property
    def is_fact(self) -> bool:
        """Whether this asserts something about the world rather than an
        opinion about it."""

        return self in (ClaimType.MEASURED, ClaimType.REPORTED)


_CLAIM_TYPES = {
    ClaimType.MEASURED: "Measured here",
    ClaimType.REPORTED: "Reported",
    ClaimType.ATTRIBUTED: "Attributed view",
    ClaimType.INFERRED: "MOVRvest reading",
    ClaimType.UNRESOLVED: "Unresolved",
}


class EventKind(StrEnum):
    """The small ontology. Every member earns its place by changing what
    a reader should do with the claim, not by completing a taxonomy."""

    #: Money moving into or out of the asset through an identifiable
    #: vehicle. Flows are facts; what they cause is not.
    CAPITAL_FLOW = "capital_flow"

    #: Who holds it — treasuries, funds, identifiable balance sheets.
    #: A stock, where a flow is a rate.
    INSTITUTIONAL_HOLDING = "institutional_holding"

    #: What the asset's own market did. Price, volume, participation.
    MARKET_BEHAVIOUR = "market_behaviour"

    #: What the network or protocol did — usage, fees, capital held.
    NETWORK_ACTIVITY = "network_activity"

    #: A change to the protocol itself.
    PROTOCOL_CHANGE = "protocol_change"

    #: A published view about the asset, always attributed.
    MARKET_NARRATIVE = "market_narrative"

    #: An exploit, a drain, a key compromise. Added in slice 2, when a
    #: register of incidents first gave this layer one to carry.
    SECURITY_INCIDENT = "security_incident"

    #: A regulator, court or supervisor acted.
    REGULATORY_ACTION = "regulatory_action"

    @property
    def stated(self) -> str:
        return _EVENT_KINDS[self]


_EVENT_KINDS = {
    EventKind.CAPITAL_FLOW: "Capital flow",
    EventKind.INSTITUTIONAL_HOLDING: "Institutional holdings",
    EventKind.MARKET_BEHAVIOUR: "Market behaviour",
    EventKind.NETWORK_ACTIVITY: "Network activity",
    EventKind.PROTOCOL_CHANGE: "Protocol change",
    EventKind.MARKET_NARRATIVE: "Market narrative",
    EventKind.SECURITY_INCIDENT: "Security incident",
    EventKind.REGULATORY_ACTION: "Regulatory action",
}


class Relevance(StrEnum):
    """How long a claim is worth reading. Intelligence is perishable.

    Asset Quality has no equivalent because a supply rule does not go
    off. A driver does: a two-week-old flow reading kept in a brief
    because it once mattered is worse than no brief, since the reader
    cannot tell it is stale.
    """

    #: Today's reading.
    CURRENT = "current"

    #: The last several days — still what is happening.
    RECENT = "recent"

    #: An ongoing condition rather than a change. A holdings level, a
    #: fee economy.
    STRUCTURAL = "structural"

    #: Past its shelf life. Retained so a reader can see it aged out,
    #: never presented as current.
    STALE = "stale"

    @property
    def stated(self) -> str:
        return _RELEVANCE[self]

    @property
    def is_live(self) -> bool:
        return self is not Relevance.STALE


_RELEVANCE = {
    Relevance.CURRENT: "Today",
    Relevance.RECENT: "Recent",
    Relevance.STRUCTURAL: "Ongoing",
    Relevance.STALE: "Stale",
}


#: How old a dated observation may be before each band lapses. Chosen
#: for the cadence of the evidence rather than for neatness: ETF flows
#: report on business days and lag settlement, so a two-day-old flow is
#: still the latest one there is.
CURRENT_WITHIN = timedelta(days=2)
RECENT_WITHIN = timedelta(days=8)
STRUCTURAL_WITHIN = timedelta(days=45)


def relevance_of(
    observed_at: datetime | None,
    now: datetime | None = None,
    structural: bool = False,
) -> Relevance:
    """How live a dated observation is. Undated is never current."""

    if observed_at is None:
        return Relevance.STALE

    moment = now or datetime.now(UTC)

    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)

    age = moment - observed_at

    if structural:
        return Relevance.STRUCTURAL if age <= STRUCTURAL_WITHIN else Relevance.STALE

    if age <= CURRENT_WITHIN:
        return Relevance.CURRENT

    if age <= RECENT_WITHIN:
        return Relevance.RECENT

    return Relevance.STALE


@dataclass(frozen=True, slots=True)
class IntelligenceClaim:
    """One thing worth telling an investor, and everything about its status.

    The unit the whole layer is built from. A driver references these
    rather than restating them, so a narrative can never say something
    the evidence does not.
    """

    #: Stable within one snapshot, so a driver or a sentence can point
    #: at this claim rather than repeat it.
    ref: str

    kind: EventKind
    claim_type: ClaimType

    #: The sentence an investor reads. Complete on its own.
    stated: str

    source: str
    authority: EvidenceAuthority
    standing: EvidenceStanding

    relevance: Relevance

    #: When the thing happened, where that differs from when it was
    #: read. A flow settles on a date and is published later.
    observed_at: datetime | None = None
    event_at: datetime | None = None

    value: float | None = None
    unit: str | None = None

    #: What this does *not* establish. Populated wherever a reader
    #: would otherwise over-read it.
    does_not_establish: str | None = None

    @property
    def is_live(self) -> bool:
        return self.relevance.is_live


class DriverSupport(StrEnum):
    """How well evidenced a proposed driver is.

    Separate from the claims beneath it, because a driver is an
    assertion *about* claims — that this is what is moving the asset —
    and that assertion has its own standing. Correlation does not
    become causation by being printed next to a price.
    """

    #: A measured fact that is itself the change. No causal claim.
    OBSERVED = "observed"

    #: Two things happened in the same window, and this platform says
    #: only that. §12's vocabulary: *"ETF inflows were strongly positive
    #: while BTC consolidated"* is permitted and *"inflows prevented BTC
    #: from falling"* is not, and the difference between them is exactly
    #: this member. It is the weakest support that still earns a place
    #: in a brief, and it never becomes a stronger one by repetition.
    COINCIDENT = "coincident"

    #: Several claims point the same way, and this platform says so.
    SUPPORTED = "supported"

    #: A source asserts the causal link. Carried with its name.
    ATTRIBUTED_BY_SOURCE = "attributed_by_source"

    #: This platform's reading, from evidence it holds.
    INFERRED = "inferred"

    #: The evidence points both ways, or is too thin to say.
    UNRESOLVED = "unresolved"

    @property
    def stated(self) -> str:
        return _SUPPORT[self]


_SUPPORT = {
    DriverSupport.OBSERVED: "Observed",
    DriverSupport.COINCIDENT: "Coincident, not shown to be causal",
    DriverSupport.SUPPORTED: "Supported by several readings",
    DriverSupport.ATTRIBUTED_BY_SOURCE: "Attributed by the source",
    DriverSupport.INFERRED: "MOVRvest reading",
    DriverSupport.UNRESOLVED: "Unresolved",
}


class Direction(StrEnum):
    """Which way a driver cuts for a holder."""

    SUPPORTIVE = "supportive"
    ADVERSE = "adverse"

    #: Real, material, and not obviously either. A fee economy is this
    #: until something says whether its level is good.
    NEUTRAL = "neutral"

    @property
    def stated(self) -> str:
        return {
            Direction.SUPPORTIVE: "Supportive",
            Direction.ADVERSE: "Adverse",
            Direction.NEUTRAL: "Context",
        }[self]


@dataclass(frozen=True, slots=True)
class Driver:
    """Something that appears to be moving the asset, and how well evidenced.

    `stated` is what an investor reads; `matters_because` is the
    consequence. The ruling's own example: *"ETF inflows increased"* is a
    fact and not yet intelligence, and the second field is where it
    becomes one — but only where the evidence carries the claim.
    """

    stated: str

    direction: Direction
    support: DriverSupport

    #: The claims this rests on. Never empty: a driver with no evidence
    #: beneath it cannot be constructed, which is the point.
    claims: tuple[str, ...]

    #: Why it matters to a holder. None where the evidence supports the
    #: observation and not yet a consequence — an honest state, and
    #: better than inventing one.
    matters_because: str | None = None


@dataclass(frozen=True, slots=True)
class Foundation:
    """A compact link back to the durable evidence, not a second dossier.

    Three lines at most. What an intelligence brief needs from the
    permanent record is the ground a reader stands on while reading the
    news — market significance, how supply works, what the network is —
    and anything more belongs on the dossier.
    """

    lines: tuple[str, ...] = ()

    #: What the durable layer could not settle. Carried here so a brief
    #: never reads as though the foundation were complete.
    unresolved: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WatchItem:
    """One thing that would materially change this view, and how to tell.

    First-class in slice 2 because §16 asked for it, and because the
    slice-1 version — a sentence in a list — could not distinguish
    *"the upgrade activates on the 14th"* from *"keep an eye on flows"*.
    The distinction that matters to an investor is whether there is a
    **date** or only a **condition**, and the rule is unambiguous:
    **never invent a future date.** Where nothing scheduled is known,
    the item is a measurable condition on evidence this platform already
    reads, and it says so.
    """

    stated: str

    #: What would settle it — a figure this platform already reads, or a
    #: named event whose date came from a source rather than from here.
    measured_by: str

    #: The claims or events this rests on. A watch item with nothing
    #: beneath it is a guess, and cannot be constructed.
    because: tuple[str, ...] = ()

    #: Only ever from a source that published one. None is the ordinary
    #: case, and an empty date is better than a plausible one.
    scheduled_for: datetime | None = None

    @property
    def is_scheduled(self) -> bool:
        return self.scheduled_for is not None


@dataclass(frozen=True, slots=True)
class AttributedNarrative:
    """Somebody's published reading of the asset, carried with their name.

    The `ATTRIBUTED` type had no live producer in slice 1. This is it:
    a source's interpretation, kept whole and kept theirs. It is never
    merged with another source's, never averaged, and never promoted —
    if this platform ever agrees, it says so separately in its own voice
    with its own evidence.
    """

    stated: str
    source: str

    #: Whether the sentence asserts one thing caused another. §12: kept,
    #: marked, and never settled here.
    is_causal: bool = False

    #: The event it was published about, so a reader can reach the facts
    #: the opinion was formed over.
    about: str | None = None


@dataclass(frozen=True, slots=True)
class CryptoIntelligenceSnapshot:
    """What changed, what may be driving it, and what to watch.

    The structured object exists before any prose. A writer may order
    and word it; a writer may not add to it, and with the writer
    disabled the whole thing still renders.
    """

    symbol: str
    as_of: datetime

    #: Every claim, addressable by ref.
    claims: tuple[IntelligenceClaim, ...] = ()

    drivers: tuple[Driver, ...] = ()

    #: The developments themselves, whole, for drill-down. Claims carry
    #: the sentences a brief prints; these carry the sources, the facts
    #: and the readings beneath each one.
    events: tuple[CryptoEvent, ...] = ()

    #: Published opinions about the asset, each with its author.
    narratives: tuple[AttributedNarrative, ...] = ()

    #: How it moved against the market and its peer group, in S4's
    #: interval-safe arithmetic. Sentences, already checked.
    relative_context: tuple[str, ...] = ()

    foundation: Foundation = Foundation()

    #: Signals that point opposite ways, stated as tension rather than
    #: resolved into one label.
    conflicting: tuple[str, ...] = ()

    #: At most three things that would materially change this view.
    #: Never a prediction, and never an invented date.
    watch_next: tuple[WatchItem, ...] = ()

    #: Why the brief is thin, where it is.
    thin_because: str | None = None

    #: Where a surface this brief depends on did not answer, or answered
    #: in a shape it could not read. Carried so an empty section can say
    #: which — an absence with no reason is the failure mode this
    #: platform has been caught by before.
    surfaces_unread: tuple[str, ...] = ()

    def claim(self, ref: str) -> IntelligenceClaim | None:
        for item in self.claims:
            if item.ref == ref:
                return item

        return None

    def event(self, identity: str) -> CryptoEvent | None:
        for item in self.events:
            if item.identity == identity:
                return item

        return None

    @property
    def live(self) -> tuple[IntelligenceClaim, ...]:
        return tuple(item for item in self.claims if item.is_live)

    @property
    def causal_claims(self) -> tuple[AttributedNarrative, ...]:
        """Published assertions of cause, left unresolved on purpose."""

        return tuple(item for item in self.narratives if item.is_causal)

    @property
    def tailwinds(self) -> tuple[Driver, ...]:
        return tuple(d for d in self.drivers if d.direction is Direction.SUPPORTIVE)

    @property
    def headwinds(self) -> tuple[Driver, ...]:
        return tuple(d for d in self.drivers if d.direction is Direction.ADVERSE)

    @property
    def is_useful(self) -> bool:
        """Whether there is enough here to be worth showing at all."""

        return bool(self.live)

    @property
    def grounded(self) -> bool:
        """Whether every driver points at claims this snapshot holds.

        The grounding contract, checkable rather than promised. A driver
        referencing a claim that is not here would be a sentence with no
        evidence behind it.

        Slice 2 extends it to watch items and narratives, for the same
        reason and against a new temptation: *"watch whether the upgrade
        activates"* is worth nothing if no upgrade was ever read, and a
        narrative attributed to a source this brief does not hold is an
        opinion with no author.
        """

        held = {item.ref for item in self.claims} | {
            item.identity for item in self.events
        }

        if not all(set(driver.claims) <= held for driver in self.drivers):
            return False

        if not all(set(item.because) <= held for item in self.watch_next):
            return False

        return all(item.about is None or item.about in held for item in self.narratives)
