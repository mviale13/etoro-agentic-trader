"""A single thing a signal observed, and what it says."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Sense(StrEnum):
    """Whether a finding argues for the security, against it, or neither."""

    FAVOURABLE = "favourable"
    ADVERSE = "adverse"

    #: Measured, and it argues neither way. A price that moved 0.4% and a
    #: P/E in the middle of its range are observations, not arguments.
    #: So is an absence: "Forward P/E unavailable." reports that nothing
    #: could be read, which is never a point for or against.
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class Finding:
    """
    One observation, carrying the sense the signal read it with.

    Findings used to be bare strings, so nothing downstream could tell
    "Large-cap company." from "Negative earnings." — and an investment
    case could not state a security's strengths without also stating its
    weaknesses as if they were strengths. The signal knows the difference
    at the moment it scores; this is where that knowledge stopped being
    thrown away.
    """

    statement: str
    sense: Sense

    @classmethod
    def favourable(cls, statement: str) -> Finding:
        return cls(statement=statement, sense=Sense.FAVOURABLE)

    @classmethod
    def adverse(cls, statement: str) -> Finding:
        return cls(statement=statement, sense=Sense.ADVERSE)

    @classmethod
    def neutral(cls, statement: str) -> Finding:
        return cls(statement=statement, sense=Sense.NEUTRAL)


def statements(findings: tuple[Finding, ...]) -> tuple[str, ...]:
    """Every finding, as text, in the order it was observed."""

    return tuple(finding.statement for finding in findings)


def statements_where(
    findings: tuple[Finding, ...],
    sense: Sense,
) -> tuple[str, ...]:
    """The findings that argue one particular way, as text."""

    return tuple(finding.statement for finding in findings if finding.sense is sense)
