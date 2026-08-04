"""What the account was worth, day by day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """One day's closing account value, as the broker recorded it."""

    observed_on: date
    total_value_usd: float


@dataclass(frozen=True, slots=True)
class EquityCurve:
    """
    The account's value over a window, in order and without gaps.

    Facts, not a conclusion: the broker's own daily figures, kept as they
    were reported. Everything read off this curve — the deepest fall, how
    far below its peak the account still sits — is measured elsewhere.

    A curve is never built with a snapshot missing from the middle. Depth
    is measured peak to trough, and a hole can hide either.
    """

    points: tuple[EquityPoint, ...]

    #: Who reported these figures, and when they were read.
    reading: Provenance

    @property
    def observations(self) -> int:
        return len(self.points)

    @property
    def values(self) -> tuple[float, ...]:
        return tuple(point.total_value_usd for point in self.points)

    @property
    def starts_on(self) -> date | None:
        return self.points[0].observed_on if self.points else None

    @property
    def ends_on(self) -> date | None:
        return self.points[-1].observed_on if self.points else None
