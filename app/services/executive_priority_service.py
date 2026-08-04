from app.domain.executive_priority import (
    ExecutivePriority,
)
from app.domain.insight import Insight


class ExecutivePriorityService:
    PRIMARY_THRESHOLD = 90
    MAX_PRIORITIES = 6

    def build(
        self,
        insights: list[Insight],
    ) -> tuple[ExecutivePriority, ...]:
        priorities = [self._from_insight(insight) for insight in insights]

        priorities.sort(
            key=lambda item: item.importance,
            reverse=True,
        )

        return tuple(priorities[: self.MAX_PRIORITIES])

    def _from_insight(
        self,
        insight: Insight,
    ) -> ExecutivePriority:
        importance = self._importance(
            insight,
        )

        return ExecutivePriority(
            importance=importance,
            category=insight.category,
            title=insight.title,
            summary=insight.message,
            recommended_action=(insight.recommended_action),
            evidence=tuple(insight.evidence),
            affected_assets=(),
            display_size=(
                "primary" if importance >= self.PRIMARY_THRESHOLD else "supporting"
            ),
        )

    def _importance(
        self,
        insight: Insight,
    ) -> int:
        importance = insight.priority

        if insight.attention_level == "critical":
            importance = max(
                importance,
                100,
            )

        elif insight.attention_level == "important":
            importance = max(
                importance,
                85,
            )

        return min(
            max(importance, 0),
            100,
        )
