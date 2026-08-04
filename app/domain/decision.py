from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    action: str
    priority: str
    confidence: int
    explanation: str
