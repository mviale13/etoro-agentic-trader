"""The Fresh Quote Ribbon's provider half — display plumbing, not evidence.

Reads eToro's batched rates route with the platform's own credential and
serves `FreshQuote`s to the two dossier heroes. Stage 0 (2026-08-25)
measured everything this file relies on: the route answers US, non-US
and crypto instruments in one call; its per-instrument `date` is
tz-aware and advances between calls; an unknown instrument id is
**silently omitted** rather than errored; and it states neither a
currency name, a delay classification nor a market status.

The contract, enforced here rather than promised:

- **no persistence.** `EtoroClient.get` archives every response to the
  evidence store unconditionally, which is right for acquisition and
  wrong for a display quote — so this service issues the same
  authenticated GET itself and writes nothing anywhere.
- **one in-flight request, 60-second TTL.** Concurrent page views of
  any symbols coalesce onto one provider call; a refresh happens at
  most once per TTL. The route's stated budget is 120 requests a
  minute; this uses at most one.
- **identity from the platform's own stored captures.** Symbols resolve
  to eToro instrument ids by reading the newest watchlists and
  instruments evidence already acquired — the same broker the quotes
  come from, zero extra calls, hermetic under the evidence root. A
  symbol the stored catalog does not name is refused, not guessed.
- **a quote failure is a quote failure.** Every fault becomes an
  UNAVAILABLE quote with a sentence; nothing raises past this service,
  so the dossier cannot be damaged by its ribbon.
"""

from __future__ import annotations

import asyncio
import math
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import Settings
from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.fresh_quote import AssetClass, FreshQuote
from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)

PROVIDER = "eToro"

RATES_PATH = "/api/v1/market-data/instruments/rates"

#: How long a fetched batch serves before the provider is asked again.
QUOTE_TTL_SECONDS = 60.0

#: How many stored captures of each catalog endpoint to read for
#: identity. One watchlists capture carried 75 symbols; holdings-only
#: instruments captures are small, so several are read to accumulate
#: coverage without walking the whole archive.
CATALOG_CAPTURES = 12


@dataclass(frozen=True, slots=True)
class _Identity:
    instrument_id: int
    label: str | None


def _asset_class(symbol: str) -> AssetClass:
    """The same declaration the crypto corpus and its surfaces serve."""

    return AssetClass.CRYPTO if symbol in ASSIGNMENTS else AssetClass.SECURITY


class FreshQuoteService:
    """One process-wide door to display quotes."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
        store: VersionedSnapshotStore | None = None,
        ttl_seconds: float = QUOTE_TTL_SECONDS,
        clock: Any | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._store = store or VersionedSnapshotStore()
        self._ttl = ttl_seconds
        self._monotonic = clock or time.monotonic

        self._catalog: dict[str, _Identity] | None = None
        self._catalog_loaded_at: float | None = None
        self._quotes: dict[str, FreshQuote] = {}
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()

    # ── identity ────────────────────────────────────────────────────

    def _load_catalog(self) -> dict[str, _Identity]:
        """Symbol → instrument identity, from stored broker evidence.

        Watchlist items carry `market.symbolName` and `market.id`;
        instrument captures carry `symbolFull` and `instrumentID`.
        Newest capture wins a disagreement, which is why the walk is
        newest-first and only absent entries are filled.
        """

        # The catalog ages on the same TTL as the quotes: a process that
        # never restarts would otherwise refuse a newly watched security
        # forever, because `movrvest acquire` appends captures the
        # frozen map never re-reads. This is a stored read — a couple of
        # dozen local files — never a provider call.
        if self._catalog is not None and self._catalog_loaded_at is not None:
            if self._monotonic() - self._catalog_loaded_at < self._ttl:
                return self._catalog

        catalog: dict[str, _Identity] = {}
        environment = self._settings.trading_mode

        for snapshot in self._store.recent(
            broker="etoro",
            environment=environment,
            endpoint="watchlists",
            limit=CATALOG_CAPTURES,
        ):
            payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}

            for watchlist in payload.get("watchlists") or []:
                if not isinstance(watchlist, dict):
                    continue

                for item in watchlist.get("items") or []:
                    market = item.get("market") if isinstance(item, dict) else None

                    if not isinstance(market, dict):
                        continue

                    symbol = str(market.get("symbolName") or "").upper().strip()
                    instrument_id = _identifier(market.get("id"))

                    if instrument_id is None:
                        continue

                    if symbol and symbol not in catalog:
                        catalog[symbol] = _Identity(
                            instrument_id=instrument_id,
                            label=str(market.get("displayName") or "") or None,
                        )

        for snapshot in self._store.recent(
            broker="etoro",
            environment=environment,
            endpoint="marketDataInstruments",
            limit=CATALOG_CAPTURES,
        ):
            payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}

            for row in payload.get("instrumentDisplayDatas") or []:
                if not isinstance(row, dict):
                    continue

                symbol = str(row.get("symbolFull") or "").upper().strip()
                instrument_id = _identifier(row.get("instrumentID"))

                if instrument_id is None:
                    continue

                if symbol and symbol not in catalog:
                    catalog[symbol] = _Identity(
                        instrument_id=instrument_id,
                        label=str(row.get("instrumentDisplayName") or "") or None,
                    )

        self._catalog = catalog
        self._catalog_loaded_at = self._monotonic()

        return catalog

    # ── quotes ──────────────────────────────────────────────────────

    async def quotes(self, symbols: tuple[str, ...]) -> tuple[FreshQuote, ...]:
        """Display quotes for the asked symbols, in the asked order.

        The cache is one batch covering the whole stored catalog, so
        every concurrent page view — whatever symbol it shows — rides
        the same provider call. The lock is the single-flight: a view
        arriving while a fetch is in progress awaits it rather than
        starting another.
        """

        wanted = tuple(dict.fromkeys(s.upper().strip() for s in symbols if s))

        if not wanted:
            return ()

        # Off by default, on by an explicit operator action. The REST
        # credential's entitlement to read rates is proven; its privilege
        # *boundary* is not, and until an operator establishes it the
        # ribbon stays dark — the heroes then render exactly their
        # fallbacks. No provider is contacted on this path.
        if not self._enabled():
            return tuple(
                FreshQuote.unavailable(
                    symbol,
                    _asset_class(symbol),
                    PROVIDER,
                    identity=None,
                    label=None,
                    because=(
                        "Fresh display quotes are not enabled. Enabling them "
                        "is an operator action (MOVRVEST_FRESH_QUOTES=on), "
                        "and production activation remains scope-unresolved "
                        "pending a least-privilege credential determination."
                    ),
                )
                for symbol in wanted
            )

        catalog = self._load_catalog()

        async with self._lock:
            if self._stale():
                await self._refresh(catalog)

        results: list[FreshQuote] = []

        for symbol in wanted:
            identity = catalog.get(symbol)

            if identity is None:
                results.append(
                    FreshQuote.identity_refused(symbol, _asset_class(symbol), PROVIDER)
                )
                continue

            held = self._quotes.get(symbol)

            if held is not None:
                results.append(held)
                continue

            results.append(
                FreshQuote.unavailable(
                    symbol,
                    _asset_class(symbol),
                    PROVIDER,
                    identity=str(identity.instrument_id),
                    label=identity.label,
                    because=(
                        "The provider answered the batch and omitted this "
                        "instrument, or the batch itself could not be read. "
                        "Nothing is substituted."
                    ),
                )
            )

        return tuple(results)

    def _enabled(self) -> bool:
        return self._settings.movrvest_fresh_quotes.strip().lower() == "on"

    def _stale(self) -> bool:
        return (
            self._fetched_at is None
            or self._monotonic() - self._fetched_at >= self._ttl
        )

    async def _refresh(self, catalog: dict[str, _Identity]) -> None:
        """One provider call for the whole catalog. Faults become an
        empty quote set — served as UNAVAILABLE — never an exception,
        and the TTL still advances so a failing provider is asked once
        per window rather than once per page view."""

        self._fetched_at = self._monotonic()
        self._quotes = {}

        if not catalog:
            return

        by_id = {
            identity.instrument_id: (symbol, identity)
            for symbol, identity in catalog.items()
        }

        try:
            rows = await self._fetch_rates(tuple(sorted(by_id)))
        except Exception:
            # The sentence for this state is written per symbol at read
            # time; the empty dict is "asked and not answered".
            return

        received_at = datetime.now(UTC)

        for row in rows:
            if not isinstance(row, dict):
                continue

            instrument_id = _identifier(row.get("instrumentID"))

            if instrument_id is None:
                continue

            entry = by_id.get(instrument_id)

            if entry is None:
                # A row nobody asked for names an instrument outside the
                # catalog; it is not evidence about any symbol here.
                continue

            symbol, identity = entry

            price = _price(row.get("lastExecution"))

            # A headline price must be a finite, strictly positive
            # number or there is no answer to display: zero and
            # negative are not prices of anything tradable, and a
            # non-finite float is transport noise. Invalid bid/ask
            # merely become null — they qualify a price, they are not
            # the price.
            if price is None:
                self._quotes[symbol] = FreshQuote.unavailable(
                    symbol,
                    _asset_class(symbol),
                    PROVIDER,
                    identity=str(instrument_id),
                    label=identity.label,
                    because=(
                        "The provider's row carried no usable traded "
                        "price, so no figure is displayed."
                    ),
                )
                continue

            self._quotes[symbol] = FreshQuote.answered(
                symbol=symbol,
                asset_class=_asset_class(symbol),
                provider=PROVIDER,
                identity=str(instrument_id),
                label=identity.label,
                price=price,
                bid=_price(row.get("bid")),
                ask=_price(row.get("ask")),
                source_as_of=_moment(row.get("date")),
                received_at=received_at,
            )

    async def _fetch_rates(self, instrument_ids: tuple[int, ...]) -> list[Any]:
        """The one authenticated GET — httpx, no retry, no archive."""

        if not self._settings.etoro_api_key or not self._settings.etoro_user_key:
            raise RuntimeError("eToro credentials are not configured")

        headers = {
            "x-api-key": self._settings.etoro_api_key,
            "x-user-key": self._settings.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
        }
        params = {
            "instrumentIds": ",".join(str(i) for i in instrument_ids),
        }
        url = f"{self._settings.etoro_base_url}{RATES_PATH}"

        if self._client is not None:
            response = await self._client.get(
                url, params=params, headers=headers, timeout=10.0
            )
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, params=params, headers=headers, timeout=10.0
                )

        response.raise_for_status()
        body = response.json()

        rates = body.get("rates") if isinstance(body, dict) else None

        return rates if isinstance(rates, list) else []


def _identifier(value: Any) -> int | None:
    """An instrument id from a payload field — int or numeric text."""

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())

    return None


def _price(value: Any) -> float | None:
    """A finite, strictly positive number, or nothing."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        figure = float(value)

        if math.isfinite(figure) and figure > 0:
            return figure

    return None


def _moment(value: Any) -> datetime | None:
    """The provider's clock, kept only when it is genuinely aware."""

    if not isinstance(value, str) or not value:
        return None

    text = value.replace("Z", "+00:00")

    # Sub-second precision beyond microseconds breaks fromisoformat on
    # some feeds; trim rather than refuse, keeping the offset intact.
    if "." in text and "+" in text:
        head, _, rest = text.partition(".")
        fraction, _, offset = rest.partition("+")
        text = f"{head}.{fraction[:6]}+{offset}"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        # A naive time is a claim with no zone; refusing it keeps the
        # receipt-only path honest rather than inventing UTC.
        return None

    return parsed.astimezone(UTC)
