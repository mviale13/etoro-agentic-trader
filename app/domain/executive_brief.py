from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutiveBrief:
    headline: str
    why: str
    action: str
    confidence: str
