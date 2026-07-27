from datetime import UTC, datetime

from app.domain.memory_event import MemoryEvent
from app.services.investor_dna_service import InvestorDNAService


def test_confidence_is_zero_without_events() -> None:
    dna = InvestorDNAService().analyze([])

    assert dna.confidence == 0


def test_confidence_reaches_100_after_20_events() -> None:
    events = [
        MemoryEvent(
            timestamp=datetime.now(UTC),
            event_type="TEST",
            subject="Microsoft",
            value="opened",
        )
        for _ in range(20)
    ]

    dna = InvestorDNAService().analyze(events)

    assert dna.confidence == 100
