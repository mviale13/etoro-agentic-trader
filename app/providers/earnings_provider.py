"""The next earnings dates a company has published, read once a day."""

from __future__ import annotations

from datetime import UTC, date, datetime

import yfinance as yf

from app.domain.earnings_schedule import EarningsWindow
from app.domain.provenance import Provenance
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache


class EarningsDatesProvider:
    """Read a company's published earnings window from Yahoo Finance."""

    SOURCE = "Yahoo Finance"

    def dates(self, symbol: str) -> tuple[date, ...]:
        """
        The published upcoming window, oldest first. Empty when none is.

        An empty answer is an answer: Yahoo lists no upcoming report for
        this company. A provider failure raises instead, so the caller
        can tell "no date published" from "could not be read".
        """

        calendar = yf.Ticker(symbol).calendar

        raw = calendar.get("Earnings Date") if isinstance(calendar, dict) else None

        return tuple(sorted(entry for entry in raw or () if isinstance(entry, date)))


class ReadDates:
    """What one read produced, and when it was actually taken."""

    def __init__(
        self,
        dates: tuple[date, ...],
        reading: Provenance,
    ) -> None:
        self.dates = dates
        self.reading = reading

    def window(self) -> EarningsWindow | None:
        """
        The published window, or nothing where no date was published.

        The one place raw dates become a window. Both callers — the book's
        calendar and a single security's investment case — read the same
        provider, and reading it two ways would let the same company report
        on two different days depending on which page asked.
        """

        if not self.dates:
            return None

        return EarningsWindow(
            starts_on=self.dates[0],
            ends_on=self.dates[-1] if len(self.dates) > 1 else None,
            reading=self.reading,
        )


class CachedEarningsProvider:
    """
    Read each company's earnings window once a day, and remember it.

    The same two properties the fundamentals cache exists for: two runs
    on the same day see the same calendar, and a reading replayed from
    cache keeps the time it was actually taken. When the provider fails,
    the last real reading is served marked `last_known` — old scheduling
    is still scheduling, but it is never dated today.
    """

    def __init__(
        self,
        provider: EarningsDatesProvider | None = None,
        cache: JsonCache | None = None,
    ) -> None:
        self._provider = provider or EarningsDatesProvider()
        self._cache = cache or JsonCache("data/cache/earnings")

    def read(self, symbol: str) -> ReadDates:
        key = symbol.upper().strip()
        entry = self._cache.read(key)

        if entry is not None and entry.is_from_today():
            return self._restore(entry)

        try:
            dates = self._provider.dates(key)
        except Exception:
            if entry is not None:
                return self._restore(entry, last_known=True)

            raise

        observed_at = datetime.now(UTC)

        self._cache.write(
            key,
            {
                "dates": [entry.isoformat() for entry in dates],
                "observed_at": observed_at.isoformat(),
            },
        )

        return ReadDates(
            dates=dates,
            reading=Provenance(
                source=EarningsDatesProvider.SOURCE,
                observed_at=observed_at,
            ),
        )

    @staticmethod
    def _restore(
        entry: CachedEntry,
        last_known: bool = False,
    ) -> ReadDates:
        raw = entry.value.get("dates")

        dates = tuple(
            date.fromisoformat(item)
            for item in (raw if isinstance(raw, list) else ())
            if isinstance(item, str)
        )

        observed = entry.value.get("observed_at")

        observed_at = (
            datetime.fromisoformat(observed)
            if isinstance(observed, str)
            else entry.stored_at
        )

        return ReadDates(
            dates=dates,
            reading=Provenance(
                source=EarningsDatesProvider.SOURCE,
                observed_at=observed_at,
                last_known=last_known,
            ),
        )
