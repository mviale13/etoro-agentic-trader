"""Beta measured from returns, and the absences that must stay absent."""

from __future__ import annotations

import pandas as pd

from app.domain.market_sensitivity import measure_sensitivity
from app.providers.yahoo_market_provider import YahooMarketProvider

BENCH = [0.01, -0.02, 0.03, -0.015, 0.005, 0.02, -0.01, 0.012, -0.008, 0.017]


def _repeat(values: list[float], times: int) -> list[float]:
    return (values * times)[: len(values) * times]


def test_a_security_that_amplifies_the_market_has_beta_two() -> None:
    benchmark = _repeat(BENCH, 4)
    security = [value * 2 for value in benchmark]

    sensitivity = measure_sensitivity(
        security,
        benchmark,
        benchmark="SPY",
        minimum_observations=5,
    )

    assert sensitivity is not None
    assert sensitivity.beta == 2.0
    assert sensitivity.correlation == 1.0
    assert sensitivity.benchmark == "SPY"
    assert sensitivity.observations == len(benchmark)


def test_a_security_that_moves_against_the_market_has_negative_beta() -> None:
    benchmark = _repeat(BENCH, 4)
    security = [-value for value in benchmark]

    sensitivity = measure_sensitivity(
        security, benchmark, benchmark="SPY", minimum_observations=5
    )

    assert sensitivity is not None
    assert sensitivity.beta == -1.0
    assert sensitivity.correlation == -1.0


def test_a_window_too_short_is_not_measured() -> None:
    assert (
        measure_sensitivity(
            [0.01, 0.02, 0.03],
            [0.01, 0.02, 0.03],
            benchmark="SPY",
            minimum_observations=30,
        )
        is None
    )


def test_a_market_that_did_not_move_cannot_anchor_a_beta() -> None:
    """Every security would divide by zero against a flat benchmark."""

    assert (
        measure_sensitivity(
            _repeat(BENCH, 4),
            [0.0] * (len(BENCH) * 4),
            benchmark="SPY",
            minimum_observations=5,
        )
        is None
    )


def test_a_security_that_never_moved_is_zero_beta_not_absent() -> None:
    benchmark = _repeat(BENCH, 4)

    sensitivity = measure_sensitivity(
        [0.0] * len(benchmark),
        benchmark,
        benchmark="SPY",
        minimum_observations=5,
    )

    assert sensitivity is not None
    assert sensitivity.beta == 0.0
    assert sensitivity.correlation == 0.0


def test_mismatched_lengths_are_not_measured() -> None:
    assert (
        measure_sensitivity(
            [0.01, 0.02],
            [0.01, 0.02, 0.03],
            benchmark="SPY",
            minimum_observations=1,
        )
        is None
    )


def test_the_reading_states_its_figures_and_window() -> None:
    sensitivity = measure_sensitivity(
        [value * 2 for value in _repeat(BENCH, 4)],
        _repeat(BENCH, 4),
        benchmark="SPY",
        minimum_observations=5,
    )

    assert sensitivity is not None
    stated = sensitivity.stated()

    assert "2.00×" in stated
    assert "SPY" in stated
    assert "40 daily returns" in stated


# ------------------------------------------------------------------
# Provider alignment: the pandas side that pairs the two series by date.
# ------------------------------------------------------------------


def _closes(start: str, returns: list[float]) -> pd.Series:
    prices = [100.0]

    for value in returns:
        prices.append(prices[-1] * (1.0 + value))

    return pd.Series(prices, index=pd.bdate_range(start, periods=len(prices)))


def test_provider_pairs_the_two_series_on_their_common_dates() -> None:
    security = _closes("2025-11-01", _repeat(BENCH, 6))
    # The same prices over a window inside the security's own history: only
    # the overlapping dates are comparable, and an identical shape over them
    # gives a beta of one.
    benchmark = security.iloc[10:50]

    sensitivity = YahooMarketProvider._market_sensitivity(security, benchmark)

    assert sensitivity is not None
    assert sensitivity.beta == 1.0
    assert sensitivity.correlation == 1.0
    # Only the shared dates count, never the security's full history.
    assert 30 <= sensitivity.observations < 60


def test_provider_reports_no_sensitivity_without_a_benchmark() -> None:
    security = _closes("2026-01-01", _repeat(BENCH, 6))

    assert YahooMarketProvider._market_sensitivity(security, None) is None
