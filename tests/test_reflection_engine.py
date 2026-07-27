from datetime import UTC, datetime

from app.domain.committee_outcome import CommitteeOutcome
from app.services.reflection_engine import ReflectionEngine


def outcome(successful: bool) -> CommitteeOutcome:
    return CommitteeOutcome(
        recommendation_timestamp=datetime.now(UTC),
        evaluation_timestamp=datetime.now(UTC),
        symbol="MSFT",
        recommendation="BUY",
        entry_price=100,
        evaluation_price=110 if successful else 90,
        return_pct=10 if successful else -10,
        successful=successful,
    )


def test_successful_reflection():
    reflection = ReflectionEngine().reflect(
        outcome(True),
    )

    assert reflection.title == "Successful Recommendation"


def test_failed_reflection():
    reflection = ReflectionEngine().reflect(
        outcome(False),
    )

    assert reflection.title == "Recommendation Review"
