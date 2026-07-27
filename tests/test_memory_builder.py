from app.domain.signal import Signal
from app.services.memory_builder import MemoryBuilder


def test_build_memory_from_high_cash_signal() -> None:
    signals = [
        Signal(
            type="cash",
            severity="info",
            title="High Cash Position",
            message="You currently hold a significant cash allocation.",
        )
    ]

    memories = MemoryBuilder().build(signals)

    assert len(memories) == 1
    assert memories[0].event_type == "portfolio_pattern"
    assert memories[0].subject == "cash_allocation"
    assert memories[0].value == "You tend to keep a high cash allocation."


def test_no_memory_for_unknown_signal() -> None:
    signals = [
        Signal(
            type="general",
            severity="info",
            title="Healthy Portfolio",
            message="Everything looks balanced.",
        )
    ]

    memories = MemoryBuilder().build(signals)

    assert memories == []
