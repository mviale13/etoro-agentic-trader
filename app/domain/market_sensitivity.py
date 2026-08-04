"""How much a security moves with the market it is measured against."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import covariance, variance


@dataclass(frozen=True, slots=True)
class MarketSensitivity:
    """
    A security's measured exposure to a benchmark, not its asset-class label.

    `beta` is the slope of the security's daily returns against the
    benchmark's: 1.0 moves point-for-point, 1.8 amplifies the market by four
    fifths, a value near zero barely moves with it, a negative one moves
    against it. It is what "how much does this move with the market" means as
    a number rather than as a category — two equities in the same asset class
    can carry very different betas, which is the whole reason a shared label
    is not exposure.

    `correlation` says how much of the security's movement the benchmark
    actually explains, from -1 to 1. It is reported beside the beta because a
    beta with weak correlation is a line fitted through noise: the number is
    real, but the security is not really moving *with* the market, and a
    reader deciding what the beta is worth needs to see that.

    Both are measurements of the observed window — `observations` daily
    returns against the named `benchmark` — never a forecast.
    """

    #: Slope of the security's returns on the benchmark's, rounded to 0.0001.
    beta: float

    #: Correlation of the two return series, in [-1, 1].
    correlation: float

    #: How many aligned daily returns the measurement was taken over.
    observations: int

    #: The market this sensitivity is measured against, e.g. "SPY".
    benchmark: str

    def stated(self) -> str:
        """One sentence an investor can read, figures and window included."""

        return (
            f"It moves {self.beta:.2f}× with {self.benchmark}, "
            f"correlation {self.correlation:+.2f} over "
            f"{self.observations} daily returns."
        )


def measure_sensitivity(
    security_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    *,
    benchmark: str,
    minimum_observations: int = 30,
) -> MarketSensitivity | None:
    """
    Regress a security's daily returns on its benchmark's.

    The two sequences must already be aligned to the same dates, newest or
    oldest first alike — the measurement is symmetric in order. Alignment is
    the caller's to do, because pairing dates is a property of where the
    series came from, not of the arithmetic here.

    Nothing is returned where a sensitivity cannot honestly be expressed: a
    window too short to measure, a value that is not finite, or a benchmark
    that did not move at all over the window. A market with no variance
    cannot anchor a beta — every security would divide by zero against it —
    and reporting one anyway would put an invented exposure on a risk report.
    A security that itself never moved is a real answer, not an absent one:
    its beta is zero and it is correlated with nothing.
    """

    if len(security_returns) != len(benchmark_returns):
        return None

    observations = len(security_returns)

    if observations < minimum_observations:
        return None

    if any(not isfinite(value) for value in security_returns):
        return None

    if any(not isfinite(value) for value in benchmark_returns):
        return None

    benchmark_variance = variance(benchmark_returns)

    if benchmark_variance <= 0:
        return None

    beta = covariance(security_returns, benchmark_returns) / benchmark_variance

    security_variance = variance(security_returns)

    # A security that never moved is correlated with nothing, rather than
    # undefined: the covariance is zero, so the beta is zero, and there is no
    # co-movement to correlate. Only the benchmark standing still is fatal.
    correlation = (
        covariance(security_returns, benchmark_returns)
        / sqrt(security_variance * benchmark_variance)
        if security_variance > 0
        else 0.0
    )

    if not isfinite(beta) or not isfinite(correlation):
        return None

    return MarketSensitivity(
        beta=round(beta, 4),
        correlation=round(max(-1.0, min(1.0, correlation)), 4),
        observations=observations,
        benchmark=benchmark,
    )
