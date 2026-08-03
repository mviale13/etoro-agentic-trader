"""Fundamentals that stay still while the day does."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.providers.value_provider import ValueProvider


class CachedValueProvider:
    """
    Read a company's fundamentals once a day, and remember them.

    Two properties matter more than the saved requests:

    Determinism. Fundamentals are published at most daily, so two runs on
    the same day must produce the same evidence. Without that, a rate-limit
    hiccup changes a score, the score changes a decision, and the platform
    records that the Artificial CIO changed its mind about a company when
    nothing about the company changed.

    Truthful age. A snapshot replayed from cache keeps the observation time
    it was fetched with. When the provider fails and yesterday's reading is
    served instead, it is served as yesterday's reading — old evidence is
    still evidence, but it is never dated today.
    """

    def __init__(
        self,
        provider: ValueProvider | None = None,
        cache: JsonCache | None = None,
    ) -> None:
        self._provider = provider or ValueProvider()
        self._cache = cache or JsonCache("data/cache/fundamentals")

    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot:
        key = symbol.upper().strip()
        entry = self._cache.read(key)

        if entry is not None and entry.is_from_today():
            return self._restore(entry)

        try:
            snapshot = self._provider.snapshot(symbol)
        except Exception:
            # The provider rate-limits. Dropping the company's fundamentals
            # would flip its evidence to "unknown" and, with it, the
            # decision — so the last real reading is served, still carrying
            # the date it was actually taken.
            #
            # And marked. Served under its own date it is indistinguishable
            # from a reading taken on schedule, which would hide a provider
            # outage behind a plausible-looking figure.
            if entry is not None:
                return self._restore(entry, last_known=True)

            raise

        self._cache.write(key, self._encode(snapshot))

        return snapshot

    @staticmethod
    def _encode(
        snapshot: ValuationSnapshot,
    ) -> dict[str, object]:
        reading = snapshot.reading or Provenance(
            source=ValueProvider.SOURCE,
            observed_at=datetime.now(UTC),
        )

        return {
            "forward_pe": snapshot.forward_pe,
            "trailing_pe": snapshot.trailing_pe,
            "peg_ratio": snapshot.peg_ratio,
            "dividend_yield": snapshot.dividend_yield,
            "market_cap": snapshot.market_cap,
            "eps": snapshot.eps,
            "circulating_supply": snapshot.circulating_supply,
            "max_supply": snapshot.max_supply,
            "volume_24h": snapshot.volume_24h,
            "inception": (
                snapshot.inception.isoformat()
                if snapshot.inception is not None
                else None
            ),
            "source": reading.source,
            "observed_at": reading.observed_at.isoformat(),
        }

    @classmethod
    def _restore(
        cls,
        entry: CachedEntry,
        last_known: bool = False,
    ) -> ValuationSnapshot:
        value = entry.value

        def number(field: str) -> float | None:
            raw = value.get(field)

            return float(raw) if isinstance(raw, (int, float)) else None

        observed_at = entry.stored_at

        raw_observed = value.get("observed_at")

        if isinstance(raw_observed, str):
            try:
                observed_at = datetime.fromisoformat(raw_observed)
            except ValueError:
                observed_at = entry.stored_at

        source = value.get("source")

        return ValuationSnapshot(
            forward_pe=number("forward_pe"),
            trailing_pe=number("trailing_pe"),
            peg_ratio=number("peg_ratio"),
            dividend_yield=number("dividend_yield"),
            market_cap=number("market_cap"),
            eps=number("eps"),
            circulating_supply=number("circulating_supply"),
            max_supply=number("max_supply"),
            volume_24h=number("volume_24h"),
            inception=cls._timestamp(value.get("inception")),
            reading=Provenance(
                source=source if isinstance(source, str) else ValueProvider.SOURCE,
                observed_at=observed_at,
                last_known=last_known,
            ),
        )

    @staticmethod
    def _timestamp(raw: object) -> datetime | None:
        if not isinstance(raw, str):
            return None

        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None
