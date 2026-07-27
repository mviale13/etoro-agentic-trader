from dataclasses import dataclass


@dataclass(frozen=True)
class Opportunity:
    company: str
    action: str
    confidence: int
    summary: str
