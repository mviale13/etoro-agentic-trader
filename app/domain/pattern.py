from dataclasses import dataclass


@dataclass(frozen=True)
class Pattern:
    title: str
    description: str
    confidence: int
