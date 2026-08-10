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
from app.domain.crypto_intelligence import (
    ClaimType,
    CryptoIntelligenceSnapshot,
    Direction,
    Driver,
    DriverSupport,
    EventKind,
    Foundation,
    IntelligenceClaim,
    relevance_of,
)
from app.domain.crypto_market import MarketInterval, MarketMetric
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import ProtocolMetric
from app.domain.supply_semantics import SupplyConcept
from app.providers.etf_flow_provider import CachedEtfFlowProvider
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


class CryptoIntelligenceService:
    """What changed, what may be driving it, and what to watch."""

    def __init__(
        self,
        facts: TokenFactsService | None = None,
        market: CryptoMarketService | None = None,
        protocol: ProtocolFundamentalsService | None = None,
        supply: SupplySemanticsService | None = None,
        flows: CachedEtfFlowProvider | None = None,
    ) -> None:
        self._facts = facts or TokenFactsService()
        self._market = market or CryptoMarketService()
        self._protocol = protocol or ProtocolFundamentalsService()
        self._supply = supply or SupplySemanticsService()
        self._flows = flows or CachedEtfFlowProvider.stored()

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

        drivers = self._drivers(claims)

        return CryptoIntelligenceSnapshot(
            symbol=normalized,
            as_of=moment,
            claims=tuple(claims),
            drivers=drivers,
            relative_context=self._relative(normalized, asset_class),
            foundation=self._foundation(normalized, asset_class),
            conflicting=self._conflicting(normalized, asset_class, drivers),
            watch_next=self._watch_next(normalized, claims, drivers),
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
                        stated=(
                            f"Over the last {reading.days_counted_30d} published "
                            f"days those funds took {_money(reading.flow_30d)} net, "
                            f"positive on {reading.inflow_days_30d} of them."
                        ),
                        source=f"MOVRvest, over {reading.source}'s daily series",
                        authority=EvidenceAuthority.SECONDARY_COMPUTATION,
                        standing=EvidenceStanding.CLAIMED,
                        relevance=relevance_of(settled, now),
                        observed_at=reading.observed_at,
                        event_at=settled,
                        value=reading.flow_30d,
                        unit="USD",
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

    # ── what appears to be driving it ───────────────────────────────

    @staticmethod
    def _drivers(claims: list[IntelligenceClaim]) -> tuple[Driver, ...]:
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

            drivers.append(
                Driver(
                    stated=(
                        "Fund flows have been a net "
                        + ("source" if positive else "drain")
                        + " of demand over the last month."
                    ),
                    direction=(Direction.SUPPORTIVE if positive else Direction.ADVERSE),
                    # Several days of the source's own series pointing
                    # the same way. Not a causal claim about the price.
                    support=DriverSupport.SUPPORTED,
                    claims=tuple(
                        ref for ref in ("flow.30d", "flow.daily") if ref in held
                    ),
                    matters_because=(
                        "It is an identifiable source of marginal "
                        + ("demand" if positive else "supply")
                        + " that does not depend on what other holders do."
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

        return tuple(drivers)

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

    @staticmethod
    def _watch_next(
        symbol: str,
        claims: list[IntelligenceClaim],
        drivers: tuple[Driver, ...],
    ) -> tuple[str, ...]:
        """The most useful open question. Never a prediction."""

        watch: list[str] = []

        refs = {claim.ref for claim in claims}

        if "flow.30d" in refs:
            watch.append(
                "Whether fund flows stay one-directional: a month of net "
                "buying is a different setup from a month of alternating days."
            )

        if any(ref.startswith("network.") for ref in refs):
            watch.append(
                "Whether the fee economy holds up — today's reading is one "
                "day, and one day is a reading rather than a trend."
            )

        stale = [claim for claim in claims if not claim.is_live]

        if stale:
            watch.append(
                f"{len(stale)} reading(s) here have aged out of their "
                "relevance window and are shown as stale rather than current."
            )

        return tuple(watch)


def _interval(interval: MarketInterval) -> str:
    return {
        MarketInterval.HOURS_1: "an hour",
        MarketInterval.HOURS_24: "24 hours",
        MarketInterval.DAYS_7: "7 days",
        MarketInterval.DAYS_30: "30 days",
    }.get(interval, interval.value)


def _money(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.0f}m"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.0f}k"

    return f"${value:,.0f}"
