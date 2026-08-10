"""Read a token's market claims from CoinGecko, once a day.

The second independent factual claimant in the token-facts pool.
CoinGecko earns its place from the S1 measurement: it agreed with the
crypto-native provider to within 0.3% on every major, exposed a stale
circulating supply the native provider's own arithmetic could not, and
carries a total supply the native endpoint lacks.

Its claims keep their own semantics. `total_volume` is volume across
the venues CoinGecko tracks — a vendor-defined universe carried as
`market_volume_24h`, never mapped onto tracked spot volume or onto the
generalist's broader figure. Its rank ranks CoinGecko's listing
universe and nobody else's.

Nothing here validates; claims go to the pool. The one check made at
read time is identity, exactly as every claimant is checked.

Operational note, measured: the keyless free tier rate-limits at
roughly six calls a minute, which is enough for the daily acquisition
batch only with backoff. A free demo key (registered by the operator —
this platform never creates accounts) lifts the limit; it is read from
`COINGECKO_API_KEY` or settings and sent as `x-cg-demo-api-key`.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Any

import requests

from app.config import get_settings
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import TokenClaimSet
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache

#: CoinGecko's own identifier for each token this platform watches.
#:
#: Declared rather than looked up, and every entry verified against the
#: provider by hand during the S1 measurement: each `/coins/{id}` call
#: echoed the symbol below. The provider confirms it again on every
#: read, so a wrong entry shows up as a refusal rather than as another
#: token's figures under this one's name.
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "ARB": "arbitrum",
    "1INCH": "1inch",
    "HYPE": "hyperliquid",
    "TAO": "bittensor",
}

API_KEY_ENV = "COINGECKO_API_KEY"


class CoinGeckoFactsUnavailable(LookupError):
    """No facts could be read, and the reason is worded for a caller."""


class CoinGeckoFactsProvider:
    """One token's market claims from CoinGecko, or a worded refusal."""

    SOURCE = "CoinGecko"

    BASE = "https://api.coingecko.com/api/v3"

    TIMEOUT = 30

    #: One retry after the keyless tier's rate limit, with the pause
    #: the measurement showed it wants. An acquisition batch is eight
    #: calls; a page view never reaches this class at all.
    RATE_LIMIT_PAUSE = 65.0

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def key(self) -> str:
        """The configured demo key, environment first and `.env` second.

        Optional: the keyless tier works, slowly. No account is ever
        created by this platform; the key exists only if the operator
        registered one.
        """

        if self._api_key is not None:
            return self._api_key

        configured = os.environ.get(API_KEY_ENV) or get_settings().coingecko_api_key

        return str(configured or "")

    def claims(self, symbol: str) -> TokenClaimSet:
        normalized = symbol.upper().strip()

        coin_id = COINGECKO_IDS.get(normalized)

        if coin_id is None:
            raise CoinGeckoFactsUnavailable(
                f"{self.SOURCE} is not asked about {normalized}: this "
                "platform has not verified which listing it means by it."
            )

        response = self._get(coin_id)

        if response.status_code == 429:
            # The keyless tier's ceiling, measured. One paced retry.
            time.sleep(self.RATE_LIMIT_PAUSE)
            response = self._get(coin_id)

        if not response.ok:
            raise CoinGeckoFactsUnavailable(
                f"{self.SOURCE} answered {response.status_code} for {normalized}."
            )

        data = response.json() or {}

        if not data:
            raise CoinGeckoFactsUnavailable(
                f"{self.SOURCE} publishes no market data for {normalized}."
            )

        return self._distill(normalized, data)

    def _get(self, coin_id: str) -> requests.Response:
        headers = {
            "accept": "application/json",
            "user-agent": "movrvest/1.0",
        }

        key = self.key()

        if key:
            headers["x-cg-demo-api-key"] = key

        return requests.get(
            f"{self.BASE}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            },
            headers=headers,
            timeout=self.TIMEOUT,
        )

    @classmethod
    def _distill(cls, symbol: str, data: dict[str, Any]) -> TokenClaimSet:
        # Identity before anything is carried.
        answered = str(data.get("symbol", "")).upper().strip()

        if answered and answered != symbol:
            raise CoinGeckoFactsUnavailable(
                f"{cls.SOURCE} answered about {answered} when asked about "
                f"{symbol}, so nothing was read."
            )

        market = data.get("market_data") or {}

        def usd(field: str) -> float | None:
            row = market.get(field)

            value = row.get("usd") if isinstance(row, dict) else None

            return cls._amount(value)

        return TokenClaimSet(
            source=cls.SOURCE,
            symbol_echo=answered or symbol,
            provider_id=str(data.get("id") or ""),
            read=Provenance(
                source=cls.SOURCE,
                observed_at=(
                    cls._moment(market.get("last_updated")) or datetime.now(UTC)
                ),
            ),
            price=usd("current_price"),
            market_cap=usd("market_cap"),
            circulating_supply=cls._amount(market.get("circulating_supply")),
            total_supply=cls._amount(market.get("total_supply")),
            max_supply=cls._amount(market.get("max_supply")),
            fully_diluted_valuation=usd("fully_diluted_valuation"),
            rank=cls._amount(data.get("market_cap_rank")),
            # CoinGecko's tracked-venue aggregate, kept as its own
            # concept — see the module docstring.
            market_volume_24h=usd("total_volume"),
        )

    @staticmethod
    def _amount(value: object) -> float | None:
        """An amount, where the provider reported one; zero is absence."""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) if value else None

        return None

    @staticmethod
    def _moment(value: object) -> datetime | None:
        """CoinGecko's ISO timestamp, where it sends one."""

        if not isinstance(value, str) or not value:
            return None

        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

        return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


class CachedCoinGeckoFactsProvider:
    """CoinGecko's claims once a day, behind the same two doors as every
    provider on this platform: a surface opens `stored` and never
    reaches the network; `movrvest acquire` opens the other."""

    def __init__(
        self,
        provider: CoinGeckoFactsProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or CoinGeckoFactsProvider()
        self._cache = cache or JsonCache("data/cache/coingecko_facts")
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedCoinGeckoFactsProvider:
        """The claims already read, and no others."""

        return cls(cache=cache, acquires=False)

    def claims(self, symbol: str) -> TokenClaimSet | None:
        key = symbol.upper().strip()
        entry = self._cache.read(key)

        held = self._restore(entry) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            claims = self._provider.claims(key)
        except Exception:
            return held

        self._cache.write(key, self._encode(claims))

        return claims

    @staticmethod
    def _encode(claims: TokenClaimSet) -> dict[str, Any]:
        return {
            "symbol": claims.symbol_echo,
            "provider_id": claims.provider_id,
            "source": claims.source,
            "observed_at": claims.read.observed_at.isoformat(),
            "price": claims.price,
            "market_cap": claims.market_cap,
            "circulating_supply": claims.circulating_supply,
            "total_supply": claims.total_supply,
            "max_supply": claims.max_supply,
            "fully_diluted_valuation": claims.fully_diluted_valuation,
            "rank": claims.rank,
            "market_volume_24h": claims.market_volume_24h,
        }

    @staticmethod
    def _restore(entry: CachedEntry) -> TokenClaimSet | None:
        value = entry.value

        symbol = value.get("symbol")

        if not isinstance(symbol, str) or not symbol:
            return None

        def amount(field: str) -> float | None:
            raw = value.get(field)

            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                return float(raw)

            return None

        raw_moment = value.get("observed_at")

        try:
            observed_at = (
                datetime.fromisoformat(raw_moment)
                if isinstance(raw_moment, str)
                else entry.stored_at
            )
        except ValueError:
            observed_at = entry.stored_at

        return TokenClaimSet(
            source=str(value.get("source", CoinGeckoFactsProvider.SOURCE)),
            symbol_echo=symbol,
            provider_id=str(value.get("provider_id", "")),
            read=Provenance(
                source=str(value.get("source", CoinGeckoFactsProvider.SOURCE)),
                observed_at=observed_at,
            ),
            price=amount("price"),
            market_cap=amount("market_cap"),
            circulating_supply=amount("circulating_supply"),
            total_supply=amount("total_supply"),
            max_supply=amount("max_supply"),
            fully_diluted_valuation=amount("fully_diluted_valuation"),
            rank=amount("rank"),
            market_volume_24h=amount("market_volume_24h"),
        )
