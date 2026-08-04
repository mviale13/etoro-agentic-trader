"""The deepest peak-to-trough fall in an observed series."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class Drawdown:
    """
    How far a series fell from its own running peak, and where.

    Positions rather than dates or prices, because the same walk measures
    a security's closing prices and an account's daily equity. Whichever
    series it was given, the caller knows what index 4 means.
    """

    #: Deepest fall in the window, as a positive ratio. 0.34 is a 34% fall.
    depth: float

    #: Where the fall started, and where it bottomed out.
    peak_index: int
    trough_index: int

    #: How far below the running peak the series ended, as a positive
    #: ratio. Zero when the series ends at a new high.
    #:
    #: A 40% fall fully recovered and a 40% fall still underwater are the
    #: same `depth` and a different situation for whoever is holding it.
    current_depth: float


def deepest_drawdown(
    values: Sequence[float],
) -> Drawdown | None:
    """
    Measure the worst fall the series actually suffered.

    This is a measurement of the observed window, not a forecast, and it
    says nothing about how long the window should be — that is the
    caller's to decide and to state.

    Nothing is returned where a fall cannot be expressed as a fraction of
    what came before it: a series with fewer than two observations, one
    carrying a value that is not a finite number, or one whose running
    peak is not positive. A fall from zero is not a percentage, and
    returning one anyway would put an invented figure on a risk report.
    """

    if len(values) < 2:
        return None

    if any(not isfinite(value) for value in values):
        return None

    peak = values[0]
    peak_index = 0

    deepest = 0.0
    deepest_peak_index = 0
    deepest_trough_index = 0

    for index, value in enumerate(values):
        if value > peak:
            peak = value
            peak_index = index

        if peak <= 0:
            return None

        fall = (peak - value) / peak

        if fall > deepest:
            deepest = fall
            deepest_peak_index = peak_index
            deepest_trough_index = index

    return Drawdown(
        # Four decimals is 0.01% resolution on a ratio, which is finer than
        # any of these series is accurate to and coarse enough that two
        # callers measuring the same window agree on the number.
        depth=round(deepest, 4),
        peak_index=deepest_peak_index,
        trough_index=deepest_trough_index,
        current_depth=round((peak - values[-1]) / peak, 4),
    )
