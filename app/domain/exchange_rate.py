"""What one currency was worth in another, and when that was read."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """
    One rate, read at one moment, from a named source.

    A conversion is a measurement like any other on this platform, and it
    was the one number that had never been treated as one: the investor's
    portfolio total was converted by a constant written into the source —
    `EUR_PER_USD = 0.85`, undated, and about 1.8% away from the market
    the day this was written. A plausible number on an investment
    dashboard reads as a measurement, so it must be one.
    """

    #: The currency an amount is converted *from*.
    base: str

    #: The currency an amount is converted *to*.
    quote: str

    #: How many units of `quote` one unit of `base` buys.
    rate: float

    reading: Provenance

    def convert(self, amount: float) -> float:
        """The amount in `quote`, at this rate."""

        return amount * self.rate
