"""Shared primitives used by reasoning assessments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssessmentLevel(StrEnum):
    """Normalized qualitative interpretation of an assessment score."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True, slots=True)
class Evidence:
    """A traceable fact supporting or opposing an assessment."""

    description: str
    source: str
    strength: float

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Evidence description cannot be empty")

        if not self.source.strip():
            raise ValueError("Evidence source cannot be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Evidence strength must be between 0.0 and 1.0")


def assessment_level(score: float) -> AssessmentLevel:
    """Convert a normalized score into a qualitative assessment level."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("Assessment score must be between 0.0 and 1.0")

    if score < 0.2:
        return AssessmentLevel.VERY_LOW
    if score < 0.4:
        return AssessmentLevel.LOW
    if score < 0.6:
        return AssessmentLevel.MODERATE
    if score < 0.8:
        return AssessmentLevel.HIGH

    return AssessmentLevel.VERY_HIGH
