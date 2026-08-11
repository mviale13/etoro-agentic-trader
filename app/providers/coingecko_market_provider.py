"""Read the crypto market's own state from CoinGecko, once a day.

The first market-context claimant. It is an adapter and nothing more:
every CoinGecko field terminates in this module, and what leaves it is
the canonical vocabulary in `app/domain/crypto_market.py`. A second
market source — CoinMarketCap, or anything else — joins by writing one
of these and appearing in a list, changing no canonical object, no
surface and no reasoning.

**The daily batch is deterministic and small**, because the keyless free
tier was measured to rate-limit at roughly six calls a minute:

```text
1  /global                                 the market's own state
1  /coins/categories                       every category, in one answer
1  /coins/markets?ids=…                    the corpus's returns
1  /coins/markets?per_page=250             breadth, and the market return
n  /coins/markets?category=…               one per peer group in use
```

Eight calls with today's four peer groups, measured at 90 seconds end
to end on the keyless tier. Each is paced, each result
is stored raw, and every surface reads the store — so re-reading costs
nothing and a page view never reaches this class at all.

**Two figures here are this platform's arithmetic, not the provider's.**
The market return is a capitalisation-weighted average of the returns of
a *named* universe, and breadth is a count over the same universe.
CoinGecko publishes neither. They are computed here rather than in the
domain because they are properties of the page that was read — a
different provider's page would be a different universe — and each
carries that universe with it.

A demo key (registered by the operator; this platform never creates
accounts) lifts the rate limit and is read from `COINGECKO_API_KEY`.
Nothing here depends on one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import requests

from app.domain.provenance import Provenance
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.coingecko_facts_provider import CoinGeckoFactsProvider

#: The stablecoins the provider names in its dominance table. Their
#: shares are summed into a floor rather than a total, which is what the
#: canonical measure's definition says: the table lists only the largest
#: assets, so smaller stablecoins are not counted.
STABLECOIN_KEYS = ("usdt", "usdc", "dai", "busd", "usde", "fdusd", "tusd")

#: How many assets the breadth-and-return universe covers.
UNIVERSE_SIZE = 250


@dataclass(frozen=True, slots=True)
class MarketStateClaim:
    """The market's own state, as one provider reports it."""

    total_market_cap: float | None = None
    total_volume: float | None = None
    market_cap_change_24h: float | None = None
    volume_change_24h: float | None = None

    btc_dominance: float | None = None
    eth_dominance: float | None = None
    stablecoin_share: float | None = None

    tracked_assets: float | None = None


@dataclass(frozen=True, slots=True)
class UniverseClaim:
    """What this platform computed over one page of assets.

    The universe is part of every figure: `counted` and `described` are
    not decoration, they are what makes a market return checkable.
    """

    key: str
    described: str
    counted: int

    #: Capitalisation-weighted return over the assets on the page.
    weighted_return_24h: float | None = None

    advancing: int = 0
    declining: int = 0

    #: The summed capitalisation of the page, used as the denominator of
    #: a share and never served as "the market's value".
    market_cap: float | None = None


@dataclass(frozen=True, slots=True)
class CategoryClaim:
    """One provider category's state, as the provider computes it."""

    key: str
    name: str
    market_cap: float | None = None
    market_cap_change_24h: float | None = None
    volume_24h: float | None = None


@dataclass(frozen=True, slots=True)
class AssetReturnClaim:
    """One asset's returns at every interval the provider publishes."""

    symbol: str
    provider_id: str
    market_cap: float | None = None
    returns: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MarketClaimSet:
    """Everything one market provider reported in one cycle."""

    source: str
    read: Provenance

    state: MarketStateClaim | None = None
    universe: UniverseClaim | None = None

    categories: tuple[CategoryClaim, ...] = ()
    assets: tuple[AssetReturnClaim, ...] = ()

    #: What this platform computed over each peer group's own membership
    #: page — breadth and a capitalisation-weighted return. Keyed by the
    #: provider's category identifier.
    category_universes: dict[str, UniverseClaim] = field(default_factory=dict)

    def category(self, key: str) -> CategoryClaim | None:
        for item in self.categories:
            if item.key == key:
                return item

        return None

    def asset(self, symbol: str) -> AssetReturnClaim | None:
        for item in self.assets:
            if item.symbol == symbol.upper().strip():
                return item

        return None


class CoinGeckoMarketUnavailable(LookupError):
    """Nothing could be read, and the reason is worded for a caller."""


class CoinGeckoMarketProvider:
    """The crypto market's state from CoinGecko, or a worded refusal."""

    SOURCE = "CoinGecko"

    BASE = "https://api.coingecko.com/api/v3"

    TIMEOUT = 45

    #: Seconds between calls in the batch. The keyless tier was measured
    #: at roughly six a minute, so the batch paces itself rather than
    #: discovering the ceiling and backing off from it.
    PACE = 11.0

    #: One paced retry after a rate limit, with the pause the
    #: measurement showed the keyless tier wants.
    RATE_LIMIT_PAUSE = 65.0

    def __init__(
        self,
        api_key: str | None = None,
        pace: float | None = None,
    ) -> None:
        self._key = CoinGeckoFactsProvider(api_key).key
        self._pace = self.PACE if pace is None else pace

    # ── the batch ───────────────────────────────────────────────────

    def claims(
        self,
        coin_ids: tuple[str, ...],
        category_keys: tuple[str, ...],
    ) -> MarketClaimSet:
        """One cycle's reading of the market, paced.

        Partial answers are kept: a rate limit on the fourth call leaves
        the first three stored rather than discarding the cycle. Every
        absence downstream then says which piece was missing.
        """

        read = Provenance(source=self.SOURCE, observed_at=datetime.now(UTC))

        state = self._state()

        categories = self._categories(category_keys)

        assets = self._assets(coin_ids)

        universe = self._universe()

        universes: dict[str, UniverseClaim] = {}

        for key in category_keys:
            counted = self._category_universe(key)

            if counted is not None:
                universes[key] = counted

        if state is None and not categories and not assets and universe is None:
            raise CoinGeckoMarketUnavailable(
                f"{self.SOURCE} answered nothing for the market cycle."
            )

        return MarketClaimSet(
            source=self.SOURCE,
            read=read,
            state=state,
            universe=universe,
            categories=categories,
            assets=assets,
            category_universes=universes,
        )

    # ── one call each ───────────────────────────────────────────────

    def _state(self) -> MarketStateClaim | None:
        payload = self._get("/global")

        data = (payload or {}).get("data")

        if not isinstance(data, dict):
            return None

        dominance = data.get("market_cap_percentage")
        dominance = dominance if isinstance(dominance, dict) else {}

        stablecoins = sum(
            share
            for key in STABLECOIN_KEYS
            if isinstance(share := dominance.get(key), (int, float))
        )

        return MarketStateClaim(
            total_market_cap=_usd(data.get("total_market_cap")),
            total_volume=_usd(data.get("total_volume")),
            market_cap_change_24h=_number(
                data.get("market_cap_change_percentage_24h_usd")
            ),
            volume_change_24h=_number(data.get("volume_change_percentage_24h_usd")),
            btc_dominance=_number(dominance.get("btc")),
            eth_dominance=_number(dominance.get("eth")),
            stablecoin_share=stablecoins or None,
            tracked_assets=_number(data.get("active_cryptocurrencies")),
        )

    def _categories(self, keys: tuple[str, ...]) -> tuple[CategoryClaim, ...]:
        """Every category in one answer, filtered to the ones in use.

        The provider returns all 749 in a single call, so reading them
        per peer group would spend a rate limit on an answer already in
        hand.
        """

        if not keys:
            return ()

        payload = self._get("/coins/categories")

        if not isinstance(payload, list):
            return ()

        wanted = set(keys)

        return tuple(
            CategoryClaim(
                key=str(row.get("id")),
                name=str(row.get("name") or row.get("id")),
                market_cap=_number(row.get("market_cap")),
                # The provider names this "market_cap_change_24h" and
                # publishes a percentage in it, which the global
                # endpoint's own percentage field confirms by scale.
                market_cap_change_24h=_number(row.get("market_cap_change_24h")),
                volume_24h=_number(row.get("volume_24h")),
            )
            for row in payload
            if isinstance(row, dict) and str(row.get("id")) in wanted
        )

    def _assets(self, coin_ids: tuple[str, ...]) -> tuple[AssetReturnClaim, ...]:
        """Every corpus asset's returns, in one call."""

        if not coin_ids:
            return ()

        payload = self._get(
            "/coins/markets",
            {
                "vs_currency": "usd",
                "ids": ",".join(coin_ids),
                "price_change_percentage": "1h,24h,7d,30d",
                "sparkline": "false",
                "per_page": str(len(coin_ids)),
            },
        )

        if not isinstance(payload, list):
            return ()

        return tuple(
            AssetReturnClaim(
                symbol=str(row.get("symbol") or "").upper().strip(),
                provider_id=str(row.get("id") or ""),
                market_cap=_number(row.get("market_cap")),
                returns={
                    interval: value
                    for interval, field_name in (
                        ("1h", "price_change_percentage_1h_in_currency"),
                        ("24h", "price_change_percentage_24h_in_currency"),
                        ("7d", "price_change_percentage_7d_in_currency"),
                        ("30d", "price_change_percentage_30d_in_currency"),
                    )
                    if (value := _number(row.get(field_name))) is not None
                },
            )
            for row in payload
            if isinstance(row, dict) and row.get("symbol")
        )

    def _universe(self) -> UniverseClaim | None:
        """Breadth and a capitalisation-weighted return, over a named page.

        The provider publishes an aggregate capitalisation *change* and
        no market *return*. They are different quantities — the first
        moves with issuance and with listings — and only the second can
        be subtracted from an asset's price return. So this platform
        computes one, over a universe it can name.
        """

        payload = self._get(
            "/coins/markets",
            {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": str(UNIVERSE_SIZE),
                "page": "1",
                "price_change_percentage": "24h",
                "sparkline": "false",
            },
        )

        return _weigh(
            payload,
            key=f"coingecko-top-{UNIVERSE_SIZE}",
            described=(
                f"the {UNIVERSE_SIZE} largest assets by market "
                "capitalisation as CoinGecko ranks them, read in one page"
            ),
        )

    def _category_universe(self, key: str) -> UniverseClaim | None:
        """One peer group's breadth and its capitalisation-weighted return.

        The category endpoint publishes an aggregate capitalisation and
        its change, and no breadth and no return. This reads the
        membership page instead — one call per peer group in use, which
        is why the groups are deduplicated before the batch, and it
        yields both the count and a return of the same kind as an
        asset's own.
        """

        payload = self._get(
            "/coins/markets",
            {
                "vs_currency": "usd",
                "category": key,
                "order": "market_cap_desc",
                "per_page": "100",
                "page": "1",
                "price_change_percentage": "24h",
                "sparkline": "false",
            },
        )

        if not isinstance(payload, list) or not payload:
            return None

        return _weigh(
            payload,
            key=key,
            described=(
                f"the largest members of CoinGecko's {key} category, "
                "read in one page of up to 100"
            ),
        )

    # ── the wire ────────────────────────────────────────────────────

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        """One paced call, with a single retry after a rate limit.

        Returns None rather than raising: a cycle that lost one call
        keeps the others, and every absence downstream carries its own
        worded reason.
        """

        if self._pace:
            time.sleep(self._pace)

        try:
            response = self._request(path, params)

            if response.status_code == 429:
                time.sleep(self.RATE_LIMIT_PAUSE)
                response = self._request(path, params)

            if not response.ok:
                return None

            return response.json()
        except Exception:
            return None

    def _request(
        self,
        path: str,
        params: dict[str, str] | None,
    ) -> requests.Response:
        headers = {
            "accept": "application/json",
            "user-agent": "movrvest/1.0",
        }

        key = self._key()

        if key:
            headers["x-cg-demo-api-key"] = key

        return requests.get(
            f"{self.BASE}{path}",
            params=params or {},
            headers=headers,
            timeout=self.TIMEOUT,
        )


def _weigh(payload: list[Any], key: str, described: str) -> UniverseClaim:
    """Breadth and a capitalisation-weighted return over one page of assets.

    This platform's arithmetic, computed here rather than in the domain
    because it is a property of the page that was read: a different
    provider's page is a different universe, and the universe travels
    with every figure that comes out of this.
    """

    weighted = 0.0
    weight = 0.0
    advancing = 0
    declining = 0

    for row in payload:
        if not isinstance(row, dict):
            continue

        change = _number(row.get("price_change_percentage_24h"))

        if change is None:
            continue

        if change > 0:
            advancing += 1
        elif change < 0:
            declining += 1

        cap = _number(row.get("market_cap"))

        if cap:
            weighted += change * cap
            weight += cap

    return UniverseClaim(
        key=key,
        described=described,
        counted=len(payload),
        weighted_return_24h=(weighted / weight) if weight else None,
        advancing=advancing,
        declining=declining,
        market_cap=weight or None,
    )


def _usd(value: object) -> float | None:
    """The dollar figure out of the provider's currency map."""

    if isinstance(value, dict):
        return _number(value.get("usd"))

    return _number(value)


def _number(value: object) -> float | None:
    """A number the provider actually reported.

    Zero is kept for a *change* and dropped for a level elsewhere: a
    market that moved 0.00% is a reading, and a total capitalisation of
    zero is a provider that has lost its place. The distinction is made
    by the caller, which knows which it asked for.
    """

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    return None


class CachedCoinGeckoMarketProvider:
    """The market's state once a day, behind the platform's two doors.

    A surface opens `stored` and never reaches the network; `movrvest
    acquire` opens the other. The whole cycle is one cache entry, so a
    partial batch is replayed exactly as it was read rather than being
    half-refreshed by a later page view.
    """

    KEY = "crypto-market"

    def __init__(
        self,
        provider: CoinGeckoMarketProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or CoinGeckoMarketProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "crypto_market"),
            # Schema 1, and records written before this store
            # declared one are accepted as schema 1 deliberately —
            # their shape is what schema 1 describes. The next bump
            # needs a migration or they re-acquire, which is the
            # protection: the store cannot change shape by accident.
            schema=1,
            accepts_unversioned=True,
        )
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedCoinGeckoMarketProvider:
        """The cycle already read, and no other."""

        return cls(cache=cache, acquires=False)

    def claims(
        self,
        coin_ids: tuple[str, ...] = (),
        category_keys: tuple[str, ...] = (),
    ) -> MarketClaimSet | None:
        entry = self._cache.read(self.KEY)

        held = self._restore(entry) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            claims = self._provider.claims(coin_ids, category_keys)
        except Exception:
            return held

        self._cache.write(self.KEY, self._encode(claims))

        return claims

    # ── storage ─────────────────────────────────────────────────────

    @staticmethod
    def _encode(claims: MarketClaimSet) -> dict[str, Any]:
        state = claims.state
        universe = claims.universe

        return {
            "source": claims.source,
            "observed_at": claims.read.observed_at.isoformat(),
            "state": (
                {
                    "total_market_cap": state.total_market_cap,
                    "total_volume": state.total_volume,
                    "market_cap_change_24h": state.market_cap_change_24h,
                    "volume_change_24h": state.volume_change_24h,
                    "btc_dominance": state.btc_dominance,
                    "eth_dominance": state.eth_dominance,
                    "stablecoin_share": state.stablecoin_share,
                    "tracked_assets": state.tracked_assets,
                }
                if state is not None
                else None
            ),
            "universe": (
                {
                    "key": universe.key,
                    "described": universe.described,
                    "counted": universe.counted,
                    "weighted_return_24h": universe.weighted_return_24h,
                    "advancing": universe.advancing,
                    "declining": universe.declining,
                    "market_cap": universe.market_cap,
                }
                if universe is not None
                else None
            ),
            "categories": [
                {
                    "key": item.key,
                    "name": item.name,
                    "market_cap": item.market_cap,
                    "market_cap_change_24h": item.market_cap_change_24h,
                    "volume_24h": item.volume_24h,
                }
                for item in claims.categories
            ],
            "assets": [
                {
                    "symbol": item.symbol,
                    "provider_id": item.provider_id,
                    "market_cap": item.market_cap,
                    "returns": item.returns,
                }
                for item in claims.assets
            ],
            "category_universes": {
                key: {
                    "key": item.key,
                    "described": item.described,
                    "counted": item.counted,
                    "weighted_return_24h": item.weighted_return_24h,
                    "advancing": item.advancing,
                    "declining": item.declining,
                    "market_cap": item.market_cap,
                }
                for key, item in claims.category_universes.items()
            },
        }

    @staticmethod
    def _restore(entry: CachedEntry) -> MarketClaimSet | None:
        value = entry.value

        try:
            observed_at = datetime.fromisoformat(str(value["observed_at"]))
            source = str(value["source"])
        except (KeyError, ValueError, TypeError):
            return None

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)

        state = value.get("state")
        universe = value.get("universe")

        return MarketClaimSet(
            source=source,
            read=Provenance(source=source, observed_at=observed_at),
            state=MarketStateClaim(**state) if isinstance(state, dict) else None,
            universe=(
                UniverseClaim(**universe) if isinstance(universe, dict) else None
            ),
            categories=tuple(
                CategoryClaim(**row)
                for row in value.get("categories", [])
                if isinstance(row, dict)
            ),
            assets=tuple(
                AssetReturnClaim(**row)
                for row in value.get("assets", [])
                if isinstance(row, dict)
            ),
            category_universes={
                str(key): UniverseClaim(**row)
                for key, row in (value.get("category_universes") or {}).items()
                if isinstance(row, dict)
            },
        )
