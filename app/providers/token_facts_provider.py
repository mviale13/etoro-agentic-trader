"""Read a token's market facts from the crypto-native provider.

The factual half of the TokenInsight integration, and strictly that:
market value, supply, valuation and activity figures, distilled into
unjudged claims. The published *rating* is the other half, lives in its
own module, and never mixes with this one — an opinion does not become
evidence because facts from the same vendor were accepted elsewhere.

Nothing here validates. Claims go to the validation gate
(`app.domain.token_fact_validation`), which is where a value earns —
or fails to earn — the standing of a fact. The one check made at read
time is identity: an answer about another token is refused outright,
exactly as the rating reader refuses one.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import requests

from app.config import get_settings
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import TokenClaimSet
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.token_insight_provider import API_KEY_ENV, TOKEN_IDS


class TokenFactsUnavailable(LookupError):
    """No facts could be read, and the reason is worded for a caller."""


class TokenFactsProvider:
    """One token's market claims, or a worded reason there are none."""

    SOURCE = "TokenInsight"

    BASE = "https://api.tokeninsight.com/api/v1"

    #: The same bot filter as the rating endpoint: the default library
    #: signature is rejected outright, key or no key.
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )

    TIMEOUT = 20

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def key(self) -> str:
        """The configured key, environment first and `.env` second."""

        if self._api_key is not None:
            return self._api_key

        configured = os.environ.get(API_KEY_ENV) or get_settings().tokeninsight_api_key

        return str(configured or "")

    def claims(self, symbol: str) -> TokenClaimSet:
        normalized = symbol.upper().strip()

        key = self.key()

        if not key:
            raise TokenFactsUnavailable(
                f"No {self.SOURCE} key is configured, so no token facts were read."
            )

        token_id = TOKEN_IDS.get(normalized)

        if token_id is None:
            raise TokenFactsUnavailable(
                f"{self.SOURCE} is not asked about {normalized}: this platform "
                "has not verified which token the provider means by it."
            )

        response = requests.get(
            f"{self.BASE}/coins/{token_id}",
            headers={
                "TI_API_KEY": key,
                "accept": "application/json",
                "user-agent": self.USER_AGENT,
            },
            timeout=self.TIMEOUT,
        )

        if not response.ok:
            raise TokenFactsUnavailable(
                f"{self.SOURCE} answered {response.status_code} for {normalized}."
            )

        data = (response.json() or {}).get("data") or {}

        if not data:
            raise TokenFactsUnavailable(
                f"{self.SOURCE} publishes no market data for {normalized}."
            )

        return self._distill(normalized, token_id, data)

    @classmethod
    def _distill(
        cls,
        symbol: str,
        token_id: str,
        data: dict[str, Any],
    ) -> TokenClaimSet:
        # Identity before anything is carried: an answer about another
        # token is refused, never distilled.
        answered = str(data.get("symbol", "")).upper().strip()

        if answered and answered != symbol:
            raise TokenFactsUnavailable(
                f"{cls.SOURCE} answered about {answered} when asked about "
                f"{symbol}, so nothing was read."
            )

        market = data.get("market_data") or {}

        usd = cls._usd_entry(market.get("price"))

        return TokenClaimSet(
            symbol_echo=answered or symbol,
            provider_id=str(data.get("id") or token_id),
            source=cls.SOURCE,
            # A receipt clock, and named as one — #223's ruling arriving
            # through the provider door.
            #
            # This adapter used to read `market_data.last_updated` as
            # "the honest age of the observation". Measured on
            # 2026-08-21, it is not an observation time at all: over a
            # single 90-second window `price_latest` moved from
            # 73.06613809983222 to 73.0488279001271 while
            # `last_updated` did not advance by one millisecond, and
            # over 16.5 hours it stayed frozen at 2026-08-20T14:29:38
            # across five assets stamped within 49 seconds of each
            # other — one batch stamp, not a per-quote time.
            #
            # No field in the payload states when `price_latest` was
            # observed. `rating.update_date` belongs to another object,
            # `ath_date`/`atl_date` are all-time extremes, and
            # `tickers[].last_traded_at` is a venue's last trade — also
            # frozen across the same 90 seconds. So the honest reading
            # is that TokenInsight states no observation time, and the
            # only moment this platform can vouch for is its own.
            #
            # What must never happen here is the substitution done
            # silently: `observation_stated=False` is what keeps the
            # receipt moment from being read as the source's.
            read=Provenance(
                source=cls.SOURCE,
                observed_at=datetime.now(UTC),
                observation_stated=False,
            ),
            price=cls._amount(usd.get("price_latest")),
            market_cap=cls._amount(usd.get("market_cap")),
            circulating_supply=cls._amount(market.get("circulating_supply")),
            max_supply=cls._amount(market.get("max_supply")),
            fully_diluted_valuation=cls._amount(usd.get("fully_diluted_valuation")),
            rank=cls._amount(data.get("rank")),
            spot_volume_24h=cls._amount(usd.get("vol_spot_24h")),
            # Signed movements: zero is a legitimate value for a change,
            # so these are not normalised the way amounts are.
            spot_volume_change_24h=cls._fraction(
                usd.get("vol_spot_change_percentage_24h")
            ),
            price_change_24h=cls._fraction(usd.get("price_change_percentage_24h")),
        )

    @staticmethod
    def _usd_entry(price: object) -> dict[str, Any]:
        """The dollar row of the provider's per-currency price list."""

        rows = [
            row
            for row in (price if isinstance(price, list) else [])
            if isinstance(row, dict)
        ]

        for row in rows:
            if str(row.get("currency", "")).lower() == "usd":
                return row

        return rows[0] if rows else {}

    @staticmethod
    def _amount(value: object) -> float | None:
        """An amount, where the provider reported one.

        Zero is a provider reporting nothing: no market value, supply,
        price or volume of a trading token is genuinely zero, and a
        zero read as a measurement is how Bittensor's absent market cap
        once became an adverse finding.
        """

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) if value else None

        return None

    @staticmethod
    def _fraction(value: object) -> float | None:
        """A signed movement, where zero means unchanged rather than absent."""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)

        return None


def _receipt_clock(value: dict[str, Any]) -> dict[str, Any] | None:
    """Bring a schema-1 record forward by discarding a false timestamp.

    A schema-1 record's `observed_at` is `market_data.last_updated` —
    measured not to describe the price stored beside it. There is no
    arithmetic that turns it into an observation time and none that
    turns it into a receipt time either, so it is dropped rather than
    relabelled: reissuing the frozen batch stamp as a receipt moment
    would be the same fabrication in the opposite direction.

    What survives is real. The record's own `stored_at` is the moment
    MOVRvest wrote the response down, which is exactly the receipt
    clock schema 2 carries — and `_restore` already falls back to it
    when no `observed_at` is present. So the migration drops the field
    and marks the clock, and the entry keeps its figures rather than
    costing a re-acquisition.
    """

    migrated = {key: item for key, item in value.items() if key != "observed_at"}
    migrated["observation_stated"] = False

    return migrated


class CachedTokenFactsProvider:
    """
    Read a token's market claims once a day, and remember them.

    The same two doors as every provider on this platform: a surface
    opens `stored` and never reaches the network; `movrvest acquire`
    opens the other. Claims never read are absent, and the validation
    gate words that absence.

    Daily is the rating store's cadence and the right one here too: the
    figures move continuously, but this platform's cycle reads once per
    acquisition, and a fresher figure would still be one observation.
    """

    def __init__(
        self,
        provider: TokenFactsProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or TokenFactsProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "token_facts"),
            # Schema 2: `observed_at` stopped meaning "when the source
            # says it observed this" and started meaning "when MOVRvest
            # received it", which is a change of meaning rather than of
            # shape — precisely the kind a reader must never absorb
            # silently.
            schema=2,
            migrations={1: _receipt_clock},
            # Records predating the schema key have schema 1's shape,
            # and reach 2 through the same migration.
            accepts_unversioned=True,
        )
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedTokenFactsProvider:
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
            # Claims that could not be re-read leave the last ones
            # standing, dated as they were.
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
            "observation_stated": claims.read.observation_stated,
            "price": claims.price,
            "market_cap": claims.market_cap,
            "circulating_supply": claims.circulating_supply,
            "max_supply": claims.max_supply,
            "fully_diluted_valuation": claims.fully_diluted_valuation,
            "rank": claims.rank,
            "spot_volume_24h": claims.spot_volume_24h,
            "spot_volume_change_24h": claims.spot_volume_change_24h,
            "price_change_24h": claims.price_change_24h,
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
            symbol_echo=symbol,
            provider_id=str(value.get("provider_id", "")),
            source=str(value.get("source", TokenFactsProvider.SOURCE)),
            read=Provenance(
                source=str(value.get("source", TokenFactsProvider.SOURCE)),
                observed_at=observed_at,
                # A record that does not say is a receipt clock: this
                # store's only writer is the adapter above, and it
                # states no observation time. Defaulting to True here
                # would restore the very claim schema 2 withdrew.
                observation_stated=value.get("observation_stated") is True,
            ),
            price=amount("price"),
            market_cap=amount("market_cap"),
            circulating_supply=amount("circulating_supply"),
            max_supply=amount("max_supply"),
            fully_diluted_valuation=amount("fully_diluted_valuation"),
            rank=amount("rank"),
            spot_volume_24h=amount("spot_volume_24h"),
            spot_volume_change_24h=amount("spot_volume_change_24h"),
            price_change_24h=amount("price_change_24h"),
        )
