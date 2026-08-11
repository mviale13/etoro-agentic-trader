"""The rate a currency actually traded at, read once a day and remembered."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from app.domain.exchange_rate import ExchangeRate
from app.domain.provenance import Provenance
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path


class ExchangeRateProvider:
    """
    Read one currency pair from the market.

    Yahoo quotes `EURUSD=X` as dollars per euro. The platform converts the
    other way — the broker reports the account in dollars and the investor
    reads it in euros — so the rate is inverted once, here, rather than at
    each call site where an inversion could go the wrong way unnoticed.
    """

    SOURCE = "Yahoo Finance"

    #: Dollars per euro, as the provider publishes it.
    PAIR = "EURUSD=X"

    BASE = "USD"
    QUOTE = "EUR"

    def usd_to_eur(self) -> ExchangeRate:
        """Euros per dollar, or a raised failure."""

        history: Any = yf.download(
            self.PAIR,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=15,
            multi_level_index=False,
        )

        if history is None or history.empty or "Close" not in history:
            raise RuntimeError(f"{self.SOURCE} returned no rate for {self.PAIR}")

        closes = history["Close"].dropna()

        if closes.empty:
            raise RuntimeError(f"{self.SOURCE} returned no rate for {self.PAIR}")

        dollars_per_euro = float(closes.iloc[-1])

        if dollars_per_euro <= 0:
            raise RuntimeError(
                f"{self.SOURCE} returned an unusable rate for {self.PAIR}"
            )

        return ExchangeRate(
            base=self.BASE,
            quote=self.QUOTE,
            rate=1 / dollars_per_euro,
            reading=Provenance(source=self.SOURCE, observed_at=datetime.now(UTC)),
        )


class CachedExchangeRateProvider:
    """
    Read the rate once a day, and remember it.

    The same two properties the fundamentals cache exists for. Determinism:
    two runs on the same day must convert the same dollars to the same
    euros, or a portfolio total moves while the portfolio does not. And
    truthful age: a rate replayed from the store keeps the moment it was
    read, so a figure converted at yesterday's rate says so rather than
    presenting itself as current.

    Two doors, as everywhere else. `stored` is what a page opens: it
    serves the rate already read and never reaches a provider. A rate that
    has never been read is absent, and the conversion that depended on it
    is absent with it — the platform does not invent a rate to fill a
    figure with.
    """

    KEY = "USD:EUR"

    def __init__(
        self,
        provider: ExchangeRateProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or ExchangeRateProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "fx"),
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
    ) -> CachedExchangeRateProvider:
        """The rate already read, and nothing this platform has not read."""

        return cls(cache=cache, acquires=False)

    def usd_to_eur(self) -> ExchangeRate | None:
        entry = self._cache.read(self.KEY)

        held = self._restore(entry) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            rate = self._provider.usd_to_eur()
        except Exception:
            # A rate that could not be read leaves the last real one
            # standing, marked — old evidence is still evidence when it
            # carries its date, and a conversion is not worth failing a
            # portfolio over.
            if held is not None:
                return self._marked(held)

            return None

        self._cache.write(
            self.KEY,
            {
                "base": rate.base,
                "quote": rate.quote,
                "rate": rate.rate,
                "source": rate.reading.source,
                "observed_at": rate.reading.observed_at.isoformat(),
            },
        )

        return rate

    @staticmethod
    def _marked(rate: ExchangeRate) -> ExchangeRate:
        """The same rate, saying the source did not answer this time."""

        return ExchangeRate(
            base=rate.base,
            quote=rate.quote,
            rate=rate.rate,
            reading=Provenance(
                source=rate.reading.source,
                observed_at=rate.reading.observed_at,
                last_known=True,
            ),
        )

    @classmethod
    def _restore(
        cls,
        entry: CachedEntry,
    ) -> ExchangeRate | None:
        value = entry.value

        rate = value.get("rate")
        observed = value.get("observed_at")

        if not isinstance(rate, (int, float)) or rate <= 0:
            return None

        try:
            observed_at = (
                datetime.fromisoformat(observed)
                if isinstance(observed, str)
                else entry.stored_at
            )
        except ValueError:
            return None

        return ExchangeRate(
            base=str(value.get("base", cls.__dict__.get("BASE", "USD"))),
            quote=str(value.get("quote", "EUR")),
            rate=float(rate),
            reading=Provenance(
                source=str(value.get("source", ExchangeRateProvider.SOURCE)),
                observed_at=observed_at,
            ),
        )
