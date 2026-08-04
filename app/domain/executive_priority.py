from dataclasses import dataclass
from typing import Literal

DisplaySize = Literal[
    "primary",
    "supporting",
]


@dataclass(frozen=True, slots=True)
class ExecutivePriority:
    importance: int
    category: str
    title: str
    summary: str
    recommended_action: str
    evidence: tuple[str, ...]
    affected_assets: tuple[str, ...]
    display_size: DisplaySize
