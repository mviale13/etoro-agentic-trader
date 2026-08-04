"""What the dashboard is told about the account's worst fall."""

from datetime import UTC, date, datetime

from app.api.routes.brain import _drawdown
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.provenance import Provenance


def make_drawdown() -> PortfolioDrawdown:
    return PortfolioDrawdown(
        depth=0.2537,
        peak_on=date(2026, 7, 1),
        peak_value_usd=52_000.0,
        trough_on=date(2026, 7, 21),
        trough_value_usd=38_806.0,
        current_depth=0.1043,
        starts_on=date(2026, 7, 1),
        ends_on=date(2026, 8, 3),
        observations=34,
        reading=Provenance(source="eToro", observed_at=datetime.now(UTC)),
    )


def test_an_unmeasured_drawdown_is_served_as_null_not_as_zero() -> None:
    """
    A page cannot tell an account that never fell from one whose history
    nobody could read, and this is where that difference reaches the
    investor.
    """

    assert _drawdown(None) is None


def test_the_measured_fall_is_served_with_the_window_it_was_taken_over() -> None:
    served = _drawdown(make_drawdown())

    assert served is not None
    assert served["depth_pct"] == 25.37
    assert served["current_depth_pct"] == 10.43
    assert served["recovered"] is False
    assert served["peak_on"] == "2026-07-01"
    assert served["trough_on"] == "2026-07-21"
    assert served["observations"] == 34
    assert served["starts_on"] == "2026-07-01"
    assert served["ends_on"] == "2026-08-03"

    # The dashboard states provenance for every figure it shows.
    assert "eToro" in str(served["reading"])
