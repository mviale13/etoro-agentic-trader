from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyAssessment:
    aligned: bool
    status: str
    rationale: tuple[str, ...]
