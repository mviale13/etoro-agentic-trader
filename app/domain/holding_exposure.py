"""One holding's measured exposure to the market, beside its size."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.market_sensitivity import MarketSensitivity


@dataclass(frozen=True, slots=True)
class HoldingExposure:
    """
    What is measured about one holding's co-movement with the market.

    This exists so a market movement can be connected to the holdings it
    touches on evidence: the holding's measured sensitivity to a named
    benchmark, and how much of the account rides on it. Both halves can be
    absent, and the absence is part of the picture rather than a reason to
    leave the holding out — a feed that names only the measured holdings
    silently reads as "the rest are untouched", which nothing measured.
    """

    symbol: str

    #: The holding's share of the account, as a percentage. None where the
    #: account reported no total value to take a share of.
    weight_pct: float | None

    #: How much this holding moves with its benchmark, or None where no
    #: sensitivity was measured — a holding no watchlist names, or one whose
    #: history was too short to regress.
    sensitivity: MarketSensitivity | None
