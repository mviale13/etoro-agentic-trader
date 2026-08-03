"""How violently the market this account is exposed to has been moving."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class ExposureVolatility:
    """
    One slice of the account, and the volatility of what it is exposed to.

    Named per slice rather than rolled into a single figure, because the
    same blended number can come from an account half in cash and half in
    crypto or from one wholly in equities, and those are not the same
    account.
    """

    #: How the slice is named to the investor: "cash", "equities", "crypto".
    exposure: str

    #: Share of the whole account, as a ratio.
    share: float

    #: Annualised volatility of what this slice is exposed to, as a ratio.
    #: Zero for cash, which is a measurement and not an assumption — cash
    #: does not move with the market.
    volatility: float

    #: The instruments the volatility was read from. Empty for cash, which
    #: needs no benchmark.
    benchmarks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MarketRisk:
    """
    The account's exposure to market movement, measured not assumed.

    This is the market as this account meets it, not the market in
    general. An account in cash is exposed to none of it, and one in
    crypto is exposed to far more of it than the index that usually
    stands in for "the market".

    What could not be assigned a benchmark is excluded and counted, so a
    figure is never quietly stretched to describe holdings it says
    nothing about.
    """

    #: The account's blended annualised volatility, as a ratio.
    volatility: float

    exposures: tuple[ExposureVolatility, ...]

    #: Share of the account this figure actually describes, as a ratio.
    covered_share: float

    #: The least reliable of the benchmark readings behind it. None where
    #: no benchmark carried one — an all-cash account needs no benchmark.
    reading: Provenance | None

    @property
    def uncovered_share(self) -> float:
        """Share of the account no benchmark could be found for."""

        return max(0.0, 1.0 - self.covered_share)
