"""The crypto environment, and one asset's place in it — read-only.

A door in the family `CompanyKnowledgeService.established` and
`ProtocolFundamentalsService.established` belong to: it asks the store
what a cycle already read and stops. It fetches nothing, asks no model
and writes nothing, so a page view may sit behind it.

**Everything here is a provider claim.** The S1 rule applies uniformly —
agreement inside one provider is not corroboration — and there is one
market source today. That is worth stating rather than working around,
because the market family raises an epistemic question the token family
did not: a *total* market capitalisation is not independently
reproducible at all. The universe is the vendor's own, so a second
vendor computing "the total" would be computing a different total rather
than corroborating this one. See the S4 report; no rule was changed to
make the number look firmer.

Nothing here scores, bands, or names a regime. `RISK_ON`, `ALTSEASON`
and their relatives are interpretations, and the layer entitled to make
one does not exist.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.crypto_market import (
    Concentration,
    CryptoMarketSnapshot,
    MarketInterval,
    MarketMetric,
    MarketObservation,
    MarketUniverse,
    RelativeReturn,
    concentration,
    relative_return,
)
from app.domain.crypto_market_context import CryptoMarketContext
from app.domain.evidence_standing import EvidenceStanding
from app.domain.market_peer_group import (
    PeerGroupSelection,
    acquired_groups,
    peer_group_for,
)
from app.providers.coingecko_market_provider import (
    CachedCoinGeckoMarketProvider,
    MarketClaimSet,
    UniverseClaim,
)

#: The intervals the provider publishes an asset return at.
_ASSET_INTERVALS: tuple[tuple[str, MarketInterval], ...] = (
    ("1h", MarketInterval.HOURS_1),
    ("24h", MarketInterval.HOURS_24),
    ("7d", MarketInterval.DAYS_7),
    ("30d", MarketInterval.DAYS_30),
)

#: The one interval every side of the comparison is published at.
#:
#: Not a configuration choice: the provider publishes asset returns at
#: four intervals and market and category figures at one, so 24 hours is
#: the only window where a difference between them means anything. Every
#: other interval's return is carried and reported as uncompared.
_ALIGNED = MarketInterval.HOURS_24

_MARKET = "the crypto market"


class MarketClaimsReader(Protocol):
    """A market provider's read-only door."""

    def claims(
        self,
        coin_ids: tuple[str, ...] = (),
        category_keys: tuple[str, ...] = (),
    ) -> MarketClaimSet | None: ...


class CryptoMarketService:
    """What the market did, and what one asset did inside it."""

    def __init__(self, reader: MarketClaimsReader | None = None) -> None:
        self._reader: MarketClaimsReader = (
            reader or CachedCoinGeckoMarketProvider.stored()
        )

    # ── the environment ─────────────────────────────────────────────

    def established(self) -> CryptoMarketSnapshot:
        """The market's own state, as the last cycle read it."""

        claims = self._read()

        if claims is None:
            return CryptoMarketSnapshot(
                observed_at=None,
                source=None,
                unavailable_because=(
                    "No market cycle has been read. Reading one is an "
                    "explicit spend, and no surface takes it — "
                    "`movrvest acquire` does."
                ),
            )

        return self._snapshot(claims)

    # ── one asset inside it ─────────────────────────────────────────

    def context(
        self,
        symbol: str,
        asset_class: AssetClass | None,
    ) -> CryptoMarketContext | None:
        """One security's market context, or None for anything not a token.

        Only a security positively classified as crypto is answered, the
        rule every crypto evidence service on this platform lives by.
        """

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        peer = peer_group_for(normalized)

        claims = self._read()

        if claims is None:
            return CryptoMarketContext(
                symbol=normalized,
                snapshot=self.established(),
                peer=peer,
                unavailable_because=(
                    "No market cycle has been read, so there is nothing "
                    "to place this asset against."
                ),
            )

        snapshot = self._snapshot(claims)

        asset = claims.asset(normalized)

        returns = self._returns(claims, normalized)

        peer_observations = self._peer_observations(claims, peer)

        relative, uncompared = self._relative(
            normalized,
            returns,
            snapshot,
            peer,
            peer_observations,
        )

        return CryptoMarketContext(
            symbol=normalized,
            snapshot=snapshot,
            returns=returns,
            peer=peer,
            peer_observations=peer_observations,
            relative=relative,
            concentrations=self._concentrations(
                normalized,
                asset.market_cap if asset is not None else None,
                claims,
                peer,
            ),
            uncompared=uncompared,
        )

    # ── assembly ────────────────────────────────────────────────────

    def _read(self) -> MarketClaimSet | None:
        try:
            return self._reader.claims()
        except Exception:
            return None

    def _snapshot(self, claims: MarketClaimSet) -> CryptoMarketSnapshot:
        observations: list[MarketObservation] = []
        universes: list[MarketUniverse] = []

        state = claims.state

        if state is not None:
            for metric, value, interval in (
                (
                    MarketMetric.TOTAL_MARKET_CAP,
                    state.total_market_cap,
                    MarketInterval.INSTANT,
                ),
                (
                    MarketMetric.TOTAL_VOLUME,
                    state.total_volume,
                    MarketInterval.INSTANT,
                ),
                (
                    MarketMetric.MARKET_CAP_CHANGE,
                    state.market_cap_change_24h,
                    MarketInterval.HOURS_24,
                ),
                (
                    MarketMetric.VOLUME_CHANGE,
                    state.volume_change_24h,
                    MarketInterval.HOURS_24,
                ),
                (
                    MarketMetric.BTC_DOMINANCE,
                    state.btc_dominance,
                    MarketInterval.INSTANT,
                ),
                (
                    MarketMetric.ETH_DOMINANCE,
                    state.eth_dominance,
                    MarketInterval.INSTANT,
                ),
                (
                    MarketMetric.STABLECOIN_SHARE,
                    state.stablecoin_share,
                    MarketInterval.INSTANT,
                ),
                (
                    MarketMetric.TRACKED_ASSETS,
                    state.tracked_assets,
                    MarketInterval.INSTANT,
                ),
            ):
                observations.append(self._claimed(claims, metric, interval, value))

        universe = claims.universe

        if universe is not None:
            named = _universe(universe)

            universes.append(named)

            for metric, value in (
                (MarketMetric.MARKET_RETURN, universe.weighted_return_24h),
                (MarketMetric.ADVANCING, float(universe.advancing)),
                (MarketMetric.DECLINING, float(universe.declining)),
            ):
                observations.append(
                    self._claimed(
                        claims,
                        metric,
                        MarketInterval.HOURS_24,
                        value,
                        universe=named,
                        derived_from=(
                            f"the 24-hour price return and market value of "
                            f"each of the {universe.counted} assets on the page",
                        ),
                    )
                )

        return CryptoMarketSnapshot(
            observed_at=claims.read.observed_at,
            source=claims.source,
            observations=tuple(observations),
            universes=tuple(universes),
        )

    def _returns(
        self,
        claims: MarketClaimSet,
        symbol: str,
    ) -> tuple[MarketObservation, ...]:
        asset = claims.asset(symbol)

        if asset is None:
            return ()

        return tuple(
            self._claimed(
                claims,
                MarketMetric.ASSET_RETURN,
                interval,
                asset.returns.get(key),
            )
            for key, interval in _ASSET_INTERVALS
            if key in asset.returns
        )

    def _peer_observations(
        self,
        claims: MarketClaimSet,
        peer: PeerGroupSelection,
    ) -> tuple[MarketObservation, ...]:
        if peer.group is None:
            return ()

        key = peer.group.key

        observations: list[MarketObservation] = []

        category = claims.category(key)

        if category is not None:
            observations.append(
                self._claimed(
                    claims,
                    MarketMetric.PEER_MARKET_CAP,
                    MarketInterval.INSTANT,
                    category.market_cap,
                )
            )
            observations.append(
                self._claimed(
                    claims,
                    MarketMetric.PEER_MARKET_CAP_CHANGE,
                    MarketInterval.HOURS_24,
                    category.market_cap_change_24h,
                )
            )
            observations.append(
                self._claimed(
                    claims,
                    MarketMetric.PEER_VOLUME,
                    MarketInterval.INSTANT,
                    category.volume_24h,
                )
            )

        universe = claims.category_universes.get(key)

        if universe is not None:
            named = _universe(universe, name=peer.group.name)

            for metric, value in (
                (MarketMetric.PEER_RETURN, universe.weighted_return_24h),
                (MarketMetric.PEER_ADVANCING, float(universe.advancing)),
                (MarketMetric.PEER_DECLINING, float(universe.declining)),
            ):
                observations.append(
                    self._claimed(
                        claims,
                        metric,
                        MarketInterval.HOURS_24,
                        value,
                        universe=named,
                        derived_from=(
                            f"the 24-hour price return and market value of "
                            f"each of the {universe.counted} members read",
                        ),
                    )
                )

        return tuple(observations)

    def _relative(
        self,
        symbol: str,
        returns: tuple[MarketObservation, ...],
        snapshot: CryptoMarketSnapshot,
        peer: PeerGroupSelection,
        peer_observations: tuple[MarketObservation, ...],
    ) -> tuple[tuple[RelativeReturn, ...], tuple[MarketInterval, ...]]:
        """The arithmetic, and the intervals it could not be done at.

        Both halves are returned together on purpose. An interval with
        an asset return and no comparator is a gap in the comparator,
        and reporting only the deltas would let a reader take four
        intervals of asset movement for four intervals of context.
        """

        aligned = next(
            (item for item in returns if item.interval is _ALIGNED),
            None,
        )

        uncompared = tuple(
            item.interval for item in returns if item.interval is not _ALIGNED
        )

        if aligned is None:
            return (), uncompared

        relative: list[RelativeReturn] = []

        market = snapshot.observation(MarketMetric.MARKET_RETURN, _ALIGNED)

        if market is not None and market.universe is not None:
            against_market = relative_return(
                subject=symbol,
                subject_observation=aligned,
                comparator=_MARKET,
                comparator_observation=market,
                caveat=(
                    "The market's figure is this platform's "
                    f"capitalisation-weighted return over {market.universe.described}."
                ),
            )

            if against_market is not None:
                relative.append(against_market)

        peer_return = next(
            (
                item
                for item in peer_observations
                if item.metric is MarketMetric.PEER_RETURN
            ),
            None,
        )

        if peer.group is not None and peer_return is not None:
            against_peers = relative_return(
                subject=symbol,
                subject_observation=aligned,
                comparator=peer.group.name,
                comparator_observation=peer_return,
                caveat=(" ".join(peer.group.caveats) if peer.group.caveats else None),
            )

            if against_peers is not None:
                relative.append(against_peers)

        return tuple(relative), uncompared

    def _concentrations(
        self,
        symbol: str,
        market_cap: float | None,
        claims: MarketClaimSet,
        peer: PeerGroupSelection,
    ) -> tuple[Concentration, ...]:
        """How much of each comparator this asset itself is.

        Computed from the *market provider's own* figures on both sides,
        never from the token-facts family: a share whose numerator and
        denominator came from different vendors' universes would not be
        a share of anything.
        """

        if not market_cap:
            return ()

        found: list[Concentration] = []

        universe = claims.universe

        if universe is not None:
            share = concentration(
                subject=symbol,
                subject_market_cap=market_cap,
                comparator=_MARKET,
                comparator_market_cap=universe.market_cap,
                standing=EvidenceStanding.CLAIMED,
                comparator_described=universe.described,
            )

            if share is not None:
                found.append(share)

        if peer.group is not None:
            category = claims.category(peer.group.key)

            share = concentration(
                subject=symbol,
                subject_market_cap=market_cap,
                comparator=peer.group.name,
                comparator_market_cap=(
                    category.market_cap if category is not None else None
                ),
                standing=EvidenceStanding.CLAIMED,
                comparator_described=(
                    f"CoinGecko's {peer.group.key} category, as the "
                    "provider computes its membership"
                ),
            )

            if share is not None:
                found.append(share)

        return tuple(found)

    @staticmethod
    def _claimed(
        claims: MarketClaimSet,
        metric: MarketMetric,
        interval: MarketInterval,
        value: float | None,
        universe: MarketUniverse | None = None,
        derived_from: tuple[str, ...] = (),
    ) -> MarketObservation:
        """One figure, served as the source's claim and never more.

        There is one market source, so nothing here is corroborated.
        A derived figure is this platform's arithmetic over that source's
        claims and inherits its standing rather than improving on it.
        """

        if value is None:
            return MarketObservation(
                metric=metric,
                interval=interval,
                standing=EvidenceStanding.ABSENT,
                universe=universe,
                because=(
                    f"{claims.source} published no figure for this in the "
                    "cycle that was read."
                ),
            )

        derived = " This platform computed it from that source's claims."

        return MarketObservation(
            metric=metric,
            interval=interval,
            standing=EvidenceStanding.CLAIMED,
            value=value,
            universe=universe,
            source=claims.source,
            observed_at=claims.read.observed_at,
            derived_from=derived_from,
            because=(
                f"{claims.source} reports it. No independent source "
                "corroborates it — agreement inside one provider is not "
                "corroboration." + (derived if derived_from else "")
            ),
        )


def _universe(claim: UniverseClaim, name: str | None = None) -> MarketUniverse:
    return MarketUniverse(
        key=claim.key,
        name=name or claim.key,
        described=claim.described,
        counted=claim.counted,
    )


def acquisition_targets() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """What one market cycle asks the provider for.

    Named here so the acquisition service and the report agree on the
    call count without either of them re-deriving it.
    """

    from app.providers.coingecko_facts_provider import COINGECKO_IDS

    return (
        tuple(COINGECKO_IDS.values()),
        tuple(group.key for group in acquired_groups()),
    )
