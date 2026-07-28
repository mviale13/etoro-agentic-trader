from app.domain.insight import Insight
from app.services.executive_priority_service import (
    ExecutivePriorityService,
)


def insight(
    *,
    priority: int,
    title: str,
    attention_level: str,
) -> Insight:
    return Insight(
        priority=priority,
        category="market",
        title=title,
        message=f"{title} summary",
        evidence=[
            f"{title} evidence",
        ],
        recommended_action=(f"Review {title.lower()}."),
        confidence="high",
        policy_alignment=None,
        attention_level=attention_level,
    )


def test_high_importance_becomes_primary() -> None:
    priorities = ExecutivePriorityService().build(
        [
            insight(
                priority=95,
                title="Federal Reserve decision",
                attention_level="critical",
            ),
        ]
    )

    assert len(priorities) == 1
    assert priorities[0].display_size == "primary"
    assert priorities[0].importance == 100


def test_lower_importance_is_supporting() -> None:
    priorities = ExecutivePriorityService().build(
        [
            insight(
                priority=70,
                title="Gold declined",
                attention_level=("informational"),
            ),
        ]
    )

    assert priorities[0].display_size == "supporting"
    assert priorities[0].importance == 70


def test_priorities_are_ranked() -> None:
    priorities = ExecutivePriorityService().build(
        [
            insight(
                priority=65,
                title="Oil",
                attention_level=("informational"),
            ),
            insight(
                priority=95,
                title="Portfolio risk",
                attention_level="critical",
            ),
            insight(
                priority=80,
                title="Bitcoin",
                attention_level="important",
            ),
        ]
    )

    assert [priority.title for priority in priorities] == [
        "Portfolio risk",
        "Bitcoin",
        "Oil",
    ]


def test_workspace_is_limited() -> None:
    insights = [
        insight(
            priority=100 - index,
            title=f"Priority {index}",
            attention_level=("informational"),
        )
        for index in range(10)
    ]

    priorities = ExecutivePriorityService().build(insights)

    assert len(priorities) == 6
