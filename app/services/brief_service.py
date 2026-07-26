from datetime import UTC, datetime

from app.domain.brief_snapshot import BriefSnapshot
from app.domain.event_type import EventType
from app.repositories.event_repository import EventRepository
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_service import CommitteeService
from app.services.doctor_service import DoctorService


class BriefService:
    def __init__(
        self,
        event_repository: EventRepository | None = None,
    ) -> None:
        self._event_repository = (
            event_repository if event_repository is not None else JsonEventRepository()
        )

    async def build(
        self,
        symbol: str = "SPY",
    ) -> BriefSnapshot:
        recommendation = await CommitteeService(
            event_repository=self._event_repository,
        ).evaluate(symbol)

        health = DoctorService().evaluate(
            recommendation,
        )

        changes = self._build_changes(
            symbol=recommendation.symbol,
            current_confidence=recommendation.decision.confidence,
        )

        return BriefSnapshot(
            greeting=self._greeting(),
            health=health,
            recommendation=recommendation,
            changes=changes,
            summary=self._summary(
                health.overall_score,
                recommendation.intelligence.outlook,
            ),
            next_action=health.recommendation,
        )

    def _build_changes(
        self,
        symbol: str,
        current_confidence: int,
    ) -> tuple[str, ...]:
        previous_events = [
            event
            for event in self._event_repository.load_latest(limit=10)
            if (
                event.event_type == EventType.RECOMMENDATION_GENERATED
                and event.symbol == symbol
            )
        ]

        if len(previous_events) < 2:
            return ("No previous recommendation available for comparison.",)

        previous_confidence = int(
            previous_events[1].payload.get(
                "confidence",
                current_confidence,
            )
        )

        difference = current_confidence - previous_confidence

        if difference > 0:
            return (f"{symbol} confidence increased by {difference} points.",)

        if difference < 0:
            return (f"{symbol} confidence decreased by {abs(difference)} points.",)

        return (f"{symbol} confidence is unchanged.",)

    @staticmethod
    def _greeting() -> str:
        hour = datetime.now(UTC).hour

        if hour < 12:
            return "Good morning."

        if hour < 18:
            return "Good afternoon."

        return "Good evening."

    @staticmethod
    def _summary(
        health_score: int,
        market_outlook: str,
    ) -> str:
        if health_score >= 85:
            health_text = "Portfolio health is strong."
        elif health_score >= 70:
            health_text = "Portfolio health is acceptable."
        else:
            health_text = "Portfolio health requires attention."

        market_text = f"Market outlook is {market_outlook.lower()}."

        return f"{health_text} {market_text}"
