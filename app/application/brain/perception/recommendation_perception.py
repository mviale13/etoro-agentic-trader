"""Recommendation perception component."""

from app.domain.recommendation import Recommendation
from app.repositories.event_repository import EventRepository
from app.services.committee_service import CommitteeService


class RecommendationPerception:
    """Produces the executive recommendation."""

    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._committee = CommitteeService(repository)

    async def execute(self) -> Recommendation:
        return await self._committee.evaluate()
