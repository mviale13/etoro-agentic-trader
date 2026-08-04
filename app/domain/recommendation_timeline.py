from dataclasses import dataclass

from app.domain.recommendation_replay import RecommendationReplay


@dataclass(frozen=True)
class RecommendationTimeline:
    items: tuple[RecommendationReplay, ...]
