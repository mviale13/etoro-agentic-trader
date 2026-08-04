from app.domain.signal import Signal
from app.services.investor_observation_service import InvestorObservationService


def test_warning_signal_becomes_observation() -> None:
    signals = [
        Signal(
            type="concentration",
            severity="warning",
            title="Concentrated Portfolio",
            message="Your portfolio contains only a few positions.",
        )
    ]

    observation = InvestorObservationService().observe(signals)

    assert observation.title == "Concentrated Portfolio"
    assert observation.category == "risk"


def test_warning_has_priority_over_info() -> None:
    signals = [
        Signal(
            type="cash",
            severity="info",
            title="High Cash Position",
            message="You hold a significant cash allocation.",
        ),
        Signal(
            type="concentration",
            severity="warning",
            title="Concentrated Portfolio",
            message="Your portfolio contains only a few positions.",
        ),
    ]

    observation = InvestorObservationService().observe(signals)

    assert observation.title == "Concentrated Portfolio"


def test_no_signals_returns_steady_course() -> None:
    observation = InvestorObservationService().observe([])

    assert observation.title == "Steady Course"
    assert observation.category == "general"
