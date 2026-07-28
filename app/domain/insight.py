from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Insight:
    priority: int
    category: str

    title: str
    message: str

    evidence: list[str]

    recommended_action: str = ""

    confidence: str = "medium"

    policy_alignment: bool | None = None

    attention_level: str = "informational"
