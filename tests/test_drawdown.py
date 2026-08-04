"""Measuring how far a series fell."""

from app.domain.drawdown import deepest_drawdown


def test_the_deepest_fall_is_found_and_located() -> None:
    """Two falls; the measurement reports the worse one and where it was."""

    measurement = deepest_drawdown([100.0, 90.0, 120.0, 60.0, 80.0])

    assert measurement is not None
    assert measurement.depth == 0.5
    assert measurement.peak_index == 2
    assert measurement.trough_index == 3


def test_a_fall_is_measured_from_the_running_peak_not_the_first_value() -> None:
    """
    A series that rose before it fell did not fall from where it started.

    Measuring against the opening value would report a rise as no
    drawdown at all, which is how an account that lost a fifth of a
    doubled balance ends up looking untouched.
    """

    measurement = deepest_drawdown([100.0, 200.0, 160.0])

    assert measurement is not None
    assert measurement.depth == 0.2


def test_a_series_that_only_rose_fell_by_nothing() -> None:
    measurement = deepest_drawdown([10.0, 11.0, 12.0])

    assert measurement is not None
    assert measurement.depth == 0.0
    assert measurement.current_depth == 0.0


def test_recovery_is_reported_apart_from_depth() -> None:
    """
    The same fall, recovered and not, is the same depth and not the same
    situation for whoever is holding it.
    """

    underwater = deepest_drawdown([100.0, 50.0, 75.0])
    recovered = deepest_drawdown([100.0, 50.0, 120.0])

    assert underwater is not None and recovered is not None
    assert underwater.depth == recovered.depth == 0.5

    assert underwater.current_depth == 0.25
    assert recovered.current_depth == 0.0


def test_a_series_too_short_to_have_fallen_is_not_measured() -> None:
    assert deepest_drawdown([]) is None
    assert deepest_drawdown([100.0]) is None


def test_a_value_that_is_not_a_number_abandons_the_measurement() -> None:
    """A hole cannot be averaged over: the trough may be exactly there."""

    assert deepest_drawdown([100.0, float("nan"), 50.0]) is None
    assert deepest_drawdown([100.0, float("inf")]) is None


def test_a_fall_from_nothing_is_not_a_percentage() -> None:
    """
    An account worth zero has no denominator, and inventing one would put
    a fabricated ratio on a risk report.
    """

    assert deepest_drawdown([0.0, 0.0, 10.0]) is None
