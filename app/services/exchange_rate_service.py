"""Convert an amount at a rate this platform actually read."""

from __future__ import annotations

from typing import Protocol

from app.domain.exchange_rate import ExchangeRate
from app.providers.exchange_rate_provider import CachedExchangeRateProvider


class RateProvider(Protocol):
    def usd_to_eur(self) -> ExchangeRate | None: ...


class ExchangeRateService:
    """
    The one place dollars become euros.

    There were two of these, disagreeing: `EUR_PER_USD = 0.85` here and
    `USD_TO_EUR_RATE = 0.92` in an `FXService` nothing imported. Both were
    constants written into the source, undated, and the live rate the day
    this was written was 0.865 — so the portfolio total an investor read
    in euros was a number nobody had measured, on the one page that is
    about their own money.

    The read-only door by default, because this runs on a page view.
    `movrvest acquire` reads the rate; a page serves what it left.
    """

    def __init__(
        self,
        provider: RateProvider | None = None,
    ) -> None:
        self._provider = provider or CachedExchangeRateProvider.stored()

    def rate(self) -> ExchangeRate | None:
        """The rate as read, or nothing where none has been."""

        return self._provider.usd_to_eur()

    def usd_to_eur(
        self,
        amount: float,
        rate: ExchangeRate | None = None,
    ) -> float | None:
        """
        The amount in euros, or nothing where no rate has been read.

        Absent, never estimated. A converted figure is derived from a
        measurement, and where the measurement is missing the figure is
        missing too — it is not filled in from a plausible constant,
        which is exactly what this replaced.

        A caller converting several amounts reads the rate once and passes
        it in, so every figure on one page is converted at one rate.
        """

        applied = rate if rate is not None else self.rate()

        if applied is None:
            return None

        return round(applied.convert(amount), 2)
