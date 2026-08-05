"""Shared primitives used by reasoning assessments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.asset_class import AssetClass


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

    #: The asset class this fact describes, where it describes only one.
    #:
    #: None means it describes the conditions every security faces — the
    #: average market move, the count of quoted instruments — and it goes
    #: to every case. A named subject is a fact about that class alone,
    #: and it belongs only to a case about that class.
    subject: AssetClass | None = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Evidence description cannot be empty")

        if not self.source.strip():
            raise ValueError("Evidence source cannot be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Evidence strength must be between 0.0 and 1.0")


def evidence_about(
    evidence: tuple[Evidence, ...],
    asset_class: AssetClass | None,
) -> tuple[Evidence, ...]:
    """
    The facts that bear on a security of this class.

    Evidence with no subject describes conditions every security faces and
    reaches every case. Evidence that names a subject reaches only a case
    about that class.

    The one sentiment index this platform reads is crypto's, and it was
    being listed among the facts weighed about a software company.
    Caveating it — "which describes crypto only" — stopped it being
    believed; it did not stop it being read, and a fact that cannot bear
    on the decision in front of you is noise wherever it is printed.

    A security whose class nobody established keeps the unsubjected
    evidence only. Assuming an unclassified instrument is the class the
    reading happens to describe is exactly the substitution this exists to
    prevent.
    """

    return tuple(
        item for item in evidence if item.subject is None or item.subject is asset_class
    )


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
