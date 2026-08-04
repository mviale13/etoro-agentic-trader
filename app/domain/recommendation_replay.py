from dataclasses import dataclass

from app.domain.event import Event


@dataclass(frozen=True)
class RecommendationReplay:
    recommendation: Event
    outcome: Event | None
