"""Compose what is happening to a digital asset, from what is held.

The synthesis half of the intelligence layer. It reads the canonical
families — token facts, market context, protocol fundamentals, supply —
adds flows and holdings, and assembles claims and drivers. It rewrites
nothing.

Three rules it is built to keep.

**Asset Quality is not consulted, and cannot be.** The module does not
import it, and a test says so. An asset whose quality reads UNKNOWN is
not an asset this platform has nothing to say about — that is the whole
reason this layer exists.

**Applicability carries the differences between assets, never a symbol
check.** Bitcoin gets ETF flows because a fund group exists for it, not
because the code says "BTC". Hyperliquid gets venue economics because it
is mapped to a venue. Nothing here branches on a ticker.

**Every driver points at claims.** A driver is an assertion *about*
evidence, so it carries the refs and never the prose. That is what makes
the grounding contract checkable rather than promised.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.crypto_event import CryptoEvent, EventFamily, EventStatus
from app.domain.crypto_intelligence import (
    AttributedNarrative,
    ClaimType,
    CryptoIntelligenceSnapshot,
    Direction,
    Driver,
    DriverSupport,
    EventKind,
    Foundation,
    IntelligenceClaim,
    WatchItem,
    relevance_of,
)
from app.domain.crypto_market import MarketInterval, MarketMetric
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import ProtocolMetric
from app.domain.supply_semantics import SupplyConcept
from app.providers.etf_flow_provider import CachedEtfFlowProvider, EtfFlowReading
from app.services.crypto_event_service import CryptoEventService
from app.services.crypto_market_service import CryptoMarketService
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
from app.services.supply_semantics_service import SupplySemanticsService
from app.services.token_facts_service import TokenFactsService

#: A day's flow above this is worth calling out rather than reporting as
#: noise. Not a threshold on quality — a threshold on *mentioning*, so a
#: brief does not lead with a rounding error. Set at a tenth of a
#: percent of the funds' own net assets, so it scales with the vehicle
#: rather than being a dollar figure that ages.
FLOW_MATERIAL = 0.001

#: How many developments reach a brief. The event service ranks and
#: ages them; this is only how many of the survivors are shown, and it
#: is small because §1 asks for *"a small number of material
#: developments, not completeness"*.
EVENTS_SHOWN = 5

#: Which claim kind an event family produces. Two vocabularies, kept
#: apart on purpose: `EventFamily` says what kind of development
#: happened, `EventKind` says what kind of thing a brief is telling the
#: investor about. They are nearly parallel and they are not the same
#: question, and collapsing them would make the claim layer inherit an
#: acquisition taxonomy.
_KIND_OF = {
    EventFamily.SECURITY: EventKind.SECURITY_INCIDENT,
    EventFamily.REGULATORY: EventKind.REGULATORY_ACTION,
    EventFamily.PROTOCOL_UPGRADE: EventKind.PROTOCOL_CHANGE,
    EventFamily.TOKENOMICS: EventKind.PROTOCOL_CHANGE,
    EventFamily.CAPITAL_FLOW: EventKind.CAPITAL_FLOW,
    EventFamily.INSTITUTIONAL_ADOPTION: EventKind.INSTITUTIONAL_HOLDING,
    EventFamily.NETWORK_OPERATION: EventKind.NETWORK_ACTIVITY,
    EventFamily.ECOSYSTEM_ADOPTION: EventKind.NETWORK_ACTIVITY,
    EventFamily.MARKET_STRUCTURE: EventKind.MARKET_BEHAVIOUR,
}


class CryptoIntelligenceService:
    """What changed, what may be driving it, and what to watch."""

    def __init__(
        self,
        facts: TokenFactsService | None = None,
        market: CryptoMarketService | None = None,
        protocol: ProtocolFundamentalsService | None = None,
        supply: SupplySemanticsService | None = None,
        flows: CachedEtfFlowProvider | None = None,
        events: CryptoEventService | None = None,
    ) -> None:
        self._facts = facts or TokenFactsService()
        self._market = market or CryptoMarketService()
        self._protocol = protocol or ProtocolFundamentalsService()
        self._supply = supply or SupplySemanticsService()
        self._flows = flows or CachedEtfFlowProvider.stored()
        self._events = events or CryptoEventService.stored()

    def snapshot(
        self,
        symbol: str,
        asset_class: AssetClass | None,
        now: datetime | None = None,
    ) -> CryptoIntelligenceSnapshot | None:
        """This asset's current intelligence, or None if it is not a token."""

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()
        moment = now or datetime.now(UTC)

        claims: list[IntelligenceClaim] = []

        claims.extend(self._market_behaviour(normalized, asset_class, moment))
        claims.extend(self._flow_claims(normalized, moment))
        claims.extend(self._network_claims(normalized, asset_class, moment))

        feed = self._events.established(normalized, moment)

        events = feed.events[:EVENTS_SHOWN]

        claims.extend(self._event_claims(events, moment))

        drivers = self._drivers(claims, events, self._flows.flows(normalized))

        return CryptoIntelligenceSnapshot(
            symbol=normalized,
            as_of=moment,
            claims=tuple(claims),
            drivers=drivers,
            events=events,
            narratives=self._narratives(events),
            relative_context=self._relative(normalized, asset_class),
            foundation=self._foundation(normalized, asset_class),
            conflicting=self._conflicting(normalized, asset_class, drivers),
            watch_next=self._watch_next(normalized, claims, events),
            surfaces_unread=tuple(item.stated for item in feed.degraded),
            thin_because=(
                None
                if any(claim.is_live for claim in claims)
                else (
                    "Nothing current has been read for this asset. Reading "
                    "it is an explicit spend — `movrvest acquire` does it."
                )
            ),
        )

    # ── what changed ────────────────────────────────────────────────

    def _market_behaviour(
        self,
        symbol: str,
        asset_class: AssetClass,
        now: datetime,
    ) -> list[IntelligenceClaim]:
        context = self._market.context(symbol, asset_class)

        if context is None:
            return []

        claims: list[IntelligenceClaim] = []

        wanted = (
            MarketInterval.HOURS_24,
            MarketInterval.DAYS_7,
            MarketInterval.DAYS_30,
        )

        for observation in context.returns:
            if observation.metric is not MarketMetric.ASSET_RETURN:
                continue

            if observation.interval not in wanted:
                continue

            if observation.value is None:
                continue

            claims.append(
                IntelligenceClaim(
                    ref=f"return.{observation.interval.value}",
                    kind=EventKind.MARKET_BEHAVIOUR,
                    # The provider published the return; this platform
                    # did not compute it from prices it holds.
                    claim_type=ClaimType.REPORTED,
                    stated=(
                        f"{symbol} returned {observation.value:+.1f}% over "
                        f"{_interval(observation.interval)}."
                    ),
                    source=observation.source or "the market provider",
                    authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
                    standing=EvidenceStanding.CLAIMED,
                    relevance=relevance_of(observation.observed_at, now),
                    observed_at=observation.observed_at,
                    value=observation.value,
                    unit="%",
                )
            )

        return claims

    def _flow_claims(
        self,
        symbol: str,
        now: datetime,
    ) -> list[IntelligenceClaim]:
        """Flows and holdings. Absent for an asset with no fund group.

        Nothing here branches on a symbol: the provider returns None
        where no group is mapped, and Hyperliquid simply has no flow
        claims rather than empty ones.
        """

        claims: list[IntelligenceClaim] = []

        reading = self._flows.flows(symbol)

        if reading is not None and reading.is_read:
            settled = datetime.combine(reading.as_of, datetime.min.time(), tzinfo=UTC)

            if reading.daily_net_flow is not None:
                material = (
                    reading.total_net_assets
                    and abs(reading.daily_net_flow)
                    > reading.total_net_assets * FLOW_MATERIAL
                )

                claims.append(
                    IntelligenceClaim(
                        ref="flow.daily",
                        kind=EventKind.CAPITAL_FLOW,
                        claim_type=ClaimType.REPORTED,
                        stated=(
                            f"US spot {symbol} ETFs took "
                            f"{_money(reading.daily_net_flow)} net on "
                            f"{reading.as_of:%-d %B}"
                            + ("." if material else ", a small day.")
                        ),
                        source=reading.source,
                        authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
                        standing=EvidenceStanding.CLAIMED,
                        relevance=relevance_of(settled, now),
                        observed_at=reading.observed_at,
                        event_at=settled,
                        value=reading.daily_net_flow,
                        unit="USD",
                        does_not_establish=(
                            "A day's flow through one set of vehicles. It "
                            "is not the market's demand, and it does not "
                            "say what the price did."
                        ),
                    )
                )

            if reading.flow_30d is not None and reading.days_counted_30d:
                claims.append(
                    IntelligenceClaim(
                        ref="flow.30d",
                        kind=EventKind.CAPITAL_FLOW,
                        # This platform added the source's own daily
                        # figures. Arithmetic, and named as such.
                        claim_type=ClaimType.MEASURED,
                        stated=_flow_sentence(reading, symbol),
                        source=f"MOVRvest, over {reading.source}'s daily series",
                        authority=EvidenceAuthority.SECONDARY_COMPUTATION,
                        standing=EvidenceStanding.CLAIMED,
                        relevance=relevance_of(settled, now),
                        observed_at=reading.observed_at,
                        event_at=settled,
                        value=reading.flow_30d,
                        unit="USD",
                        does_not_establish=(
                            "A net total is not a rate of demand. This one is "
                            f"the residue of {reading.days_counted_30d} days "
                            "that pulled both ways, and the dispersion beside "
                            "it is what says how much."
                        ),
                    )
                )

            if reading.token_holdings is not None:
                share = (
                    f" — {reading.share_of_supply:.1%} of the supply"
                    if reading.share_of_supply
                    else ""
                )

                claims.append(
                    IntelligenceClaim(
                        ref="flow.holdings",
                        kind=EventKind.INSTITUTIONAL_HOLDING,
                        claim_type=ClaimType.REPORTED,
                        stated=(
                            f"Those funds hold {reading.token_holdings:,.0f} "
                            f"{symbol}{share}, worth "
                            f"{_money(reading.total_net_assets or 0)}."
                        ),
                        source=reading.source,
                        authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
                        standing=EvidenceStanding.CLAIMED,
                        relevance=relevance_of(settled, now, structural=True),
                        observed_at=reading.observed_at,
                        event_at=settled,
                        value=reading.token_holdings,
                        unit=symbol,
                    )
                )

        treasury = self._flows.treasuries(symbol)

        if treasury is not None:
            claims.append(
                IntelligenceClaim(
                    ref="holding.treasuries",
                    kind=EventKind.INSTITUTIONAL_HOLDING,
                    claim_type=ClaimType.REPORTED,
                    stated=(
                        f"{treasury.companies} public companies report holding "
                        f"{treasury.total_holdings:,.0f} {symbol}, worth "
                        f"{_money(treasury.total_value_usd)}."
                    ),
                    source=treasury.source,
                    authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
                    standing=EvidenceStanding.CLAIMED,
                    relevance=relevance_of(treasury.observed_at, now, structural=True),
                    observed_at=treasury.observed_at,
                    value=treasury.total_holdings,
                    unit=symbol,
                    does_not_establish=(
                        "What one source has counted. Companies that do not "
                        "disclose are not in it."
                    ),
                )
            )

        return claims

    def _network_claims(
        self,
        symbol: str,
        asset_class: AssetClass,
        now: datetime,
    ) -> list[IntelligenceClaim]:
        """What the network or venue did, from the protocol family."""

        protocol = self._protocol.established(symbol, asset_class)

        if protocol is None or not protocol.entities:
            return []

        claims: list[IntelligenceClaim] = []

        for metric, kind, wording in (
            (ProtocolMetric.FEES, EventKind.NETWORK_ACTIVITY, "paid in fees"),
            (
                ProtocolMetric.HOLDER_REVENUE,
                EventKind.NETWORK_ACTIVITY,
                "reached holders",
            ),
            (ProtocolMetric.OPEN_INTEREST, EventKind.MARKET_BEHAVIOUR, "held open"),
        ):
            for entity in protocol.entities:
                fact = protocol.fact(metric, entity.key)

                if fact is None or fact.value is None:
                    continue

                mechanism = (
                    f" {fact.provider_methodology.split('.')[0]}."
                    if metric is ProtocolMetric.HOLDER_REVENUE
                    and fact.provider_methodology
                    else ""
                )

                claims.append(
                    IntelligenceClaim(
                        ref=f"network.{metric.value}.{entity.key}",
                        kind=kind,
                        claim_type=ClaimType.REPORTED,
                        stated=(
                            f"{entity.name}: {_money(fact.value)} {wording}"
                            + (
                                " over a day."
                                if metric is not ProtocolMetric.OPEN_INTEREST
                                else "."
                            )
                            + mechanism
                        ),
                        source=fact.source or "the protocol provider",
                        authority=EvidenceAuthority.PROVIDER_SCOPED_AGGREGATE,
                        standing=fact.standing,
                        relevance=relevance_of(fact.observed_at, now),
                        observed_at=fact.observed_at,
                        value=fact.value,
                        unit="USD",
                    )
                )

        return claims

    # ── what happened ───────────────────────────────────────────────

    @staticmethod
    def _event_claims(
        events: tuple[CryptoEvent, ...],
        now: datetime,
    ) -> list[IntelligenceClaim]:
        """One claim per development, addressable by the event's identity.

        The claim carries what a brief prints and the event carries
        everything beneath it, so a driver can reference a development
        without the brief restating the whole account.

        Standing is `CLAIMED` throughout and never rises. Corroboration
        by a second outlet raises **provenance**, not standing — S1's
        rule, applied to news: a claim establishes when independent
        sources are checked against each other by this platform, and
        two publications carrying one figure have not been checked, they
        have been counted.
        """

        claims: list[IntelligenceClaim] = []

        for event in events:
            corroborated = [fact for fact in event.facts if fact.is_corroborated]

            others = tuple(
                source for source in event.sources if source != event.reports[0].source
            )

            claims.append(
                IntelligenceClaim(
                    ref=event.identity,
                    kind=_KIND_OF[event.family],
                    claim_type=ClaimType.REPORTED,
                    stated=event.headline,
                    source=(
                        f"{event.sources[0]}"
                        + (f" and {len(others)} other source(s)" if others else "")
                    ),
                    authority=event.tier.authority,
                    standing=EvidenceStanding.CLAIMED,
                    relevance=relevance_of(event.at, now),
                    observed_at=event.observed_at,
                    event_at=event.at,
                    does_not_establish=(
                        "Reported, not checked here. "
                        + (
                            f"{len(corroborated)} of its figures appear in an "
                            "independent account; the rest rest on one source."
                            if corroborated
                            else "No independent account of its figures was found."
                        )
                    ),
                )
            )

        return claims

    @staticmethod
    def _narratives(
        events: tuple[CryptoEvent, ...],
    ) -> tuple[AttributedNarrative, ...]:
        """Every published reading, with its author's name kept on it.

        The `ATTRIBUTED` type finally has a live producer. Nothing is
        merged and nothing is scored: two sources reading one event
        oppositely both appear, which is the honest outcome and the one
        a single sentiment label destroys.
        """

        narratives: list[AttributedNarrative] = []

        for event in events:
            for reading in event.interpretations:
                narratives.append(
                    AttributedNarrative(
                        stated=reading.stated,
                        source=reading.source,
                        is_causal=reading.is_causal,
                        about=event.identity,
                    )
                )

        return tuple(narratives)

    # ── what appears to be driving it ───────────────────────────────

    @staticmethod
    def _drivers(
        claims: list[IntelligenceClaim],
        events: tuple[CryptoEvent, ...] = (),
        reading: EtfFlowReading | None = None,
    ) -> tuple[Driver, ...]:
        """Assemble drivers from claims, each with its own support level.

        A driver never restates a claim: it references one. Where the
        evidence supports an observation and not a consequence,
        `matters_because` is left absent rather than invented.
        """

        held = {claim.ref: claim for claim in claims}

        drivers: list[Driver] = []

        thirty = held.get("flow.30d")
        daily = held.get("flow.daily")

        if thirty is not None and thirty.value is not None:
            positive = thirty.value > 0

            # A net total does not make a driver. Whether the month was
            # accumulation or two large days cancelling decides both what
            # this says and how strongly, and slice 1 got that wrong in
            # exactly one direction: it called $128m net across offsetting
            # sessions "a net source of demand" and put it under
            # tailwinds. The shape is what the sign test was missing.
            shape = reading.shape if reading is not None else None

            concentrated = shape == "concentrated"

            drivers.append(
                Driver(
                    stated=(
                        (
                            "Fund flows netted "
                            + ("positive" if positive else "negative")
                            + " over the month, but on offsetting sessions "
                            "rather than sustained buying."
                        )
                        if concentrated
                        else (
                            "Fund flows have been a net "
                            + ("source" if positive else "drain")
                            + " of demand over the last month."
                        )
                    ),
                    direction=(
                        Direction.NEUTRAL
                        if concentrated
                        else (Direction.SUPPORTIVE if positive else Direction.ADVERSE)
                    ),
                    support=(
                        # One session larger than the month's net total is
                        # not several readings pointing one way.
                        DriverSupport.OBSERVED
                        if concentrated
                        else DriverSupport.SUPPORTED
                    ),
                    claims=tuple(
                        ref for ref in ("flow.30d", "flow.daily") if ref in held
                    ),
                    matters_because=(
                        (
                            "The net total is the residue of days pulling both "
                            "ways, so it is a weaker signal of demand than its "
                            "size suggests."
                        )
                        if concentrated
                        else (
                            "It is an identifiable source of marginal "
                            + ("demand" if positive else "supply")
                            + " that does not depend on what other holders do."
                        )
                    ),
                )
            )
        elif daily is not None:
            drivers.append(
                Driver(
                    stated="One day's fund flow is the only flow reading held.",
                    direction=Direction.NEUTRAL,
                    support=DriverSupport.OBSERVED,
                    claims=("flow.daily",),
                )
            )

        holdings = [
            ref for ref in ("flow.holdings", "holding.treasuries") if ref in held
        ]

        if holdings:
            drivers.append(
                Driver(
                    stated=(
                        "Identifiable institutional balance sheets hold a "
                        "material share of the asset."
                    ),
                    direction=Direction.NEUTRAL,
                    # This platform's reading of two holdings figures.
                    # Whether it is supportive depends on whether those
                    # holders sell, which nothing here knows.
                    support=DriverSupport.INFERRED,
                    claims=tuple(holdings),
                    matters_because=(
                        "It is a stock rather than a flow: it says who owns "
                        "the asset, not who is buying it, and a large "
                        "disclosed holder base cuts both ways."
                    ),
                )
            )

        accrual = [ref for ref in held if ref.startswith("network.holder_revenue")]

        if accrual:
            drivers.append(
                Driver(
                    stated="Economic activity is reaching the token itself.",
                    direction=Direction.SUPPORTIVE,
                    support=DriverSupport.OBSERVED,
                    claims=tuple(accrual),
                    matters_because=(
                        "A protocol can earn and pass its holders nothing. "
                        "Where a mechanism is named, the earning and the "
                        "holder are connected rather than merely adjacent."
                    ),
                )
            )

        month = held.get("return.30d")

        if month is not None and month.value is not None and abs(month.value) >= 10:
            drivers.append(
                Driver(
                    stated=(f"The asset has moved {month.value:+.0f}% over a month."),
                    direction=(
                        Direction.SUPPORTIVE if month.value > 0 else Direction.ADVERSE
                    ),
                    support=DriverSupport.OBSERVED,
                    claims=("return.30d",),
                )
            )

        drivers.extend(CryptoIntelligenceService._event_drivers(events, held, month))

        return tuple(drivers)

    @staticmethod
    def _event_drivers(
        events: tuple[CryptoEvent, ...],
        held: dict[str, IntelligenceClaim],
        month: IntelligenceClaim | None,
    ) -> list[Driver]:
        """Drivers a development supports, and never one it merely
        preceded.

        §12 is the whole design of this method. An event happened and
        the price moved: those are two facts, and the sentence joining
        them is the one this platform must not write. So there are
        exactly three things it will say.

        A development that **changes what the asset is** — an exploit, a
        rule change, a regulator's decision — is a driver in its own
        right, because its consequence does not run through the price at
        all. A development that only coincides with a move is
        `COINCIDENT`, worded as *"while"* and never as *"because"*. And
        where a **source** asserts the causal link, the assertion is a
        driver attributed to that source, which is the only way a causal
        claim ever appears here.
        """

        drivers: list[Driver] = []

        for event in events:
            if not event.family.changes_durable_facts:
                continue

            adverse = event.family in (EventFamily.SECURITY, EventFamily.REGULATORY)

            drivers.append(
                Driver(
                    stated=f"{event.family.stated}: {event.headline}",
                    direction=Direction.ADVERSE if adverse else Direction.NEUTRAL,
                    support=(
                        DriverSupport.OBSERVED
                        if event.tier.value == "primary"
                        else DriverSupport.SUPPORTED
                    ),
                    claims=(event.identity,),
                    matters_because=(
                        "It bears on what the asset durably is rather than on "
                        "how it traded today, so it outlasts the week it "
                        "happened in."
                        if not event.status.value == "ongoing"
                        else "It is still running, so the next reading may differ."
                    ),
                )
            )

        # A source's own causal claim, carried as theirs.
        for event in events:
            for reading in event.causal_claims[:1]:
                drivers.append(
                    Driver(
                        stated=f"{reading.source}: {reading.stated}",
                        direction=Direction.NEUTRAL,
                        support=DriverSupport.ATTRIBUTED_BY_SOURCE,
                        claims=(event.identity,),
                        matters_because=(
                            "This is the source's reading of cause, not this "
                            "platform's. Nothing here checks it."
                        ),
                    )
                )

        # Coincidence, said as coincidence.
        flow = held.get("flow.30d")

        if (
            flow is not None
            and flow.value is not None
            and month is not None
            and month.value is not None
        ):
            drivers.append(
                Driver(
                    stated=(
                        "Fund flows were net "
                        + ("positive" if flow.value > 0 else "negative")
                        + " over the last month while the asset moved "
                        + f"{month.value:+.0f}%."
                    ),
                    direction=Direction.NEUTRAL,
                    support=DriverSupport.COINCIDENT,
                    claims=tuple(
                        ref for ref in ("flow.30d", "return.30d") if ref in held
                    ),
                    matters_because=(
                        "Two readings over one window. Which moved which is "
                        "not something this platform can see, and it does not "
                        "say."
                    ),
                )
            )

        return drivers

    # ── context, foundation, tension ────────────────────────────────

    def _relative(self, symbol: str, asset_class: AssetClass) -> tuple[str, ...]:
        """S4's interval-safe arithmetic, already checked. Never recomputed."""

        context = self._market.context(symbol, asset_class)

        if context is None:
            return ()

        return tuple(item.stated for item in context.relative)

    def _foundation(self, symbol: str, asset_class: AssetClass) -> Foundation:
        """Three lines of durable ground, and what it could not settle."""

        lines: list[str] = []
        unresolved: list[str] = []

        facts = self._facts.established(symbol, symbol, asset_class)

        if facts is not None:
            cap = facts.fact("market_cap")

            if cap is not None and cap.value is not None:
                lines.append(
                    f"Market significance: {_money(cap.value)} "
                    f"({cap.standing.stated.lower()}, {cap.source})."
                )
            elif cap is not None and cap.standing is EvidenceStanding.CONFLICTED:
                unresolved.append(
                    "Sources disagree on this asset's market value, so it "
                    "has none here."
                )

        picture = self._supply.established(symbol, asset_class)

        if picture is not None and picture.is_read:
            maximum = picture.of(SupplyConcept.MAX_SUPPLY)
            emitted = picture.of(SupplyConcept.EMITTED_SUPPLY)

            if maximum and emitted:
                share = emitted[0].value / maximum[0].value

                lines.append(
                    f"Supply: {share:.1%} of a protocol maximum of "
                    f"{maximum[0].stated} has been emitted."
                )
            elif not maximum:
                lines.append(
                    "Supply: no protocol maximum is reported, so issuance is "
                    "governed by a rule rather than a cap."
                )

            for conflict in picture.conflicts[:1]:
                unresolved.append(conflict.because)

        protocol = self._protocol.established(symbol, asset_class)

        if protocol is not None and protocol.entities:
            names = ", ".join(entity.name for entity in protocol.entities)

            lines.append(f"Economic system: {names}.")

        return Foundation(lines=tuple(lines), unresolved=tuple(unresolved))

    def _conflicting(
        self,
        symbol: str,
        asset_class: AssetClass,
        drivers: tuple[Driver, ...],
    ) -> tuple[str, ...]:
        """Tension, stated rather than resolved into one label."""

        tension: list[str] = []

        supportive = [d for d in drivers if d.direction is Direction.SUPPORTIVE]
        adverse = [d for d in drivers if d.direction is Direction.ADVERSE]

        if supportive and adverse:
            tension.append(
                f"{supportive[0].stated} At the same time, "
                f"{adverse[0].stated[0].lower() + adverse[0].stated[1:]}"
            )

        picture = self._supply.established(symbol, asset_class)

        if picture is not None and picture.has_methodology_disagreement:
            tension.append(
                "How much of this asset is actually circulating is disputed "
                "between sources, so any figure computed from it inherits "
                "the disagreement."
            )

        return tuple(tension)

    def _watch_next(
        self,
        symbol: str,
        claims: list[IntelligenceClaim],
        events: tuple[CryptoEvent, ...],
    ) -> tuple[WatchItem, ...]:
        """At most three things that would materially change this view.

        §16, and its hard rule: **never invent a future date.** Nothing
        this platform reads publishes a schedule of upgrades, votes or
        unlocks, so every item here is a *measurable condition* on
        evidence already held — and each says what would settle it, so
        an investor can check rather than wait to be told.

        Ordered by what would move the view most: an unfinished event
        first, then the flow state, then the fee economy.
        """

        watch: list[WatchItem] = []

        held = {claim.ref: claim for claim in claims}

        for event in events:
            if event.status is not EventStatus.ONGOING:
                continue

            watch.append(
                WatchItem(
                    stated=(
                        f"Whether {event.entity or event.headline} is resolved — "
                        "the register still records this one as unsettled."
                    ),
                    measured_by=(
                        "the incident register's own record of funds returned"
                    ),
                    because=(event.identity,),
                )
            )

            break

        flow = held.get("flow.30d")

        if flow is not None:
            reading = self._flows.flows(symbol)

            shape = reading.shape if reading is not None else None

            watch.append(
                WatchItem(
                    stated=(
                        "Whether fund flows stay positive over the next few "
                        "sessions"
                        + (
                            ", and whether the pattern stops being offsetting "
                            "days around a small net total"
                            if shape == "concentrated"
                            else ""
                        )
                        + "."
                    ),
                    measured_by=(
                        "the published daily net flow, and the count of "
                        "positive days in the next window"
                    ),
                    because=("flow.30d",),
                )
            )

        if any(ref.startswith("network.") for ref in held):
            watch.append(
                WatchItem(
                    stated=(
                        "Whether the fee economy holds up — today's reading is "
                        "one day, and one day is a reading rather than a trend."
                    ),
                    measured_by="the next daily fee and holder-revenue reading",
                    because=tuple(ref for ref in held if ref.startswith("network."))[
                        :1
                    ],
                )
            )

        return tuple(watch[:3])


def _flow_sentence(reading: EtfFlowReading, symbol: str) -> str:
    """The month's flows, with the dispersion the total hides.

    Slice 1 wrote *"$128m net, positive on 18 of 30 days"* and the
    handoff flagged it: a reader takes steadier demand from that than
    the data supports. The measurement proved the flag right — BTC's
    single largest outflow day was $445m, three and a half times the
    whole month's net — so the sentence now carries the biggest day in
    each direction and says which shape the window is.
    """

    head = (
        f"Over the last {reading.days_counted_30d} published days those funds "
        f"took {_money(reading.flow_30d or 0)} net, positive on "
        f"{reading.inflow_days_30d} of them"
    )

    if reading.largest_inflow_day is None and reading.largest_outflow_day is None:
        return f"{head}."

    extremes = " and ".join(
        part
        for part in (
            (
                f"the largest single day of buying was "
                f"{_money(reading.largest_inflow_day)}"
                if reading.largest_inflow_day is not None
                else ""
            ),
            (
                f"the largest day of selling {_money(reading.largest_outflow_day)}"
                if reading.largest_outflow_day is not None
                else ""
            ),
        )
        if part
    )

    shape = reading.shape

    tail = f" — {_SHAPES[shape]}" if shape in _SHAPES else ""

    # The run, where there is one. A month's shape and its most recent
    # days are different questions, and an investor asking whether
    # anything has changed lately is asking the second.
    streak = ""

    if reading.current_streak:
        run = abs(reading.current_streak)

        streak = (
            f" The last {run} published session(s) were "
            + ("inflows" if reading.current_streak > 0 else "outflows")
            + "."
        )

    return f"{head}; {extremes}{tail}.{streak}"


#: How each flow shape is worded. Three outcomes, and the wording is the
#: only thing that changes — nothing reads these to rank or recommend.
_SHAPES = {
    "concentrated": (
        "a single session outweighed the month's whole net total, so this is "
        "offsetting flows rather than accumulation"
    ),
    "persistent": "buying on most sessions rather than a few large ones",
    "persistently negative": "selling on most sessions rather than a few large ones",
    "mixed": "days pulling both ways in roughly equal number",
}


def _interval(interval: MarketInterval) -> str:
    return {
        MarketInterval.HOURS_1: "an hour",
        MarketInterval.HOURS_24: "24 hours",
        MarketInterval.DAYS_7: "7 days",
        MarketInterval.DAYS_30: "30 days",
    }.get(interval, interval.value)


def _money(value: float) -> str:
    # The sign goes before the currency: "-$445m", never "$-445m".
    sign = "-" if value < 0 else ""

    size = abs(value)

    if size >= 1_000_000_000:
        return f"{sign}${size / 1_000_000_000:,.1f}bn"

    if size >= 1_000_000:
        return f"{sign}${size / 1_000_000:,.0f}m"

    if size >= 1_000:
        return f"{sign}${size / 1_000:,.0f}k"

    return f"{sign}${size:,.0f}"
