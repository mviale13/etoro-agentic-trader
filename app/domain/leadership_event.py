"""Regulator-filed changes in a company's executive leadership.

This is evidence, not an opinion about management quality.  A chief
executive can announce a planned transition without making the company
weaker, and a permanent appointment can close a search without proving
the appointment is good.  The event layer records the narrower facts:
who changed role, which role changed, what kind of change was filed, and
where the filing can be checked.

The first source is SEC Form 8-K Item 5.02.  That item is broader than
leadership continuity -- it also carries director elections and executive
compensation -- so an Item 5.02 filing is only a candidate.  It becomes a
``LeadershipEvent`` when a sentence names a covered executive role and a
transition action.  Everything else is declined rather than silently
treated as evidence about management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from app.domain.primary_source import SourceAuthority


class ExecutiveRole(StrEnum):
    """The executive offices the first measured source names reliably."""

    CHIEF_EXECUTIVE = "chief_executive"
    CHIEF_FINANCIAL = "chief_financial"
    CHIEF_OPERATING = "chief_operating"
    PRESIDENT = "president"

    @property
    def stated(self) -> str:
        return {
            ExecutiveRole.CHIEF_EXECUTIVE: "Chief Executive Officer",
            ExecutiveRole.CHIEF_FINANCIAL: "Chief Financial Officer",
            ExecutiveRole.CHIEF_OPERATING: "Chief Operating Officer",
            ExecutiveRole.PRESIDENT: "President",
        }[self]


class LeadershipEventKind(StrEnum):
    """What changed, without grading whether the change is beneficial."""

    PLANNED_TRANSITION = "planned_transition"
    SUCCESSION_SEARCH = "succession_search"
    DEPARTURE = "departure"
    INTERIM_APPOINTMENT = "interim_appointment"
    APPOINTMENT = "appointment"

    @property
    def stated(self) -> str:
        return {
            LeadershipEventKind.PLANNED_TRANSITION: "Planned transition",
            LeadershipEventKind.SUCCESSION_SEARCH: "Succession search",
            LeadershipEventKind.DEPARTURE: "Departure",
            LeadershipEventKind.INTERIM_APPOINTMENT: "Interim appointment",
            LeadershipEventKind.APPOINTMENT: "Appointment",
        }[self]

    @property
    def names_no_permanent_successor(self) -> bool:
        """Whether this event itself names no permanent successor.

        This is not a risk judgment.  A search has no named successor and
        an interim appointment says, in its own title, that it is temporary.
        A later event can close the transition.  This property says only
        what this event establishes and deliberately makes no claim about
        the company's current state.
        """

        return self in (
            LeadershipEventKind.PLANNED_TRANSITION,
            LeadershipEventKind.SUCCESSION_SEARCH,
            LeadershipEventKind.INTERIM_APPOINTMENT,
        )


@dataclass(frozen=True, slots=True)
class RegulatoryEventSource:
    """The immutable filing that reported one leadership change."""

    regulator: str
    form: str
    item: str
    accession: str
    filed_on: date
    url: str
    authority: SourceAuthority = SourceAuthority.REGULATOR_FILED


@dataclass(frozen=True, slots=True)
class LeadershipEvent:
    """One executive-role change read from one regulator-filed report."""

    identity: str
    symbol: str
    company: str
    role: ExecutiveRole
    person: str
    kind: LeadershipEventKind

    #: When the company says the action occurred.  The filing date is used
    #: only where the filed sentence states no separate date.
    occurred_on: date

    #: When a departure or appointment takes effect, if the filing states it.
    #: None is absence, never "immediately" inferred from the filing date.
    effective_on: date | None

    source: RegulatoryEventSource

    #: Exact filed sentences bearing on this event.  The parser may select
    #: them, but never rewrites or summarises them.
    facts: tuple[str, ...]

    @property
    def stated(self) -> str:
        return f"{self.kind.stated}: {self.role.stated} — {self.person}"


@dataclass(frozen=True, slots=True)
class LeadershipFeedHealth:
    """What the SEC surface returned and what the parser could use."""

    source: str
    reached: bool
    reports_seen: int = 0
    reports_read: int = 0
    events_kept: int = 0
    declined: tuple[str, ...] = ()
    unreadable: tuple[str, ...] = ()
    because: str | None = None

    @property
    def is_degraded(self) -> bool:
        return bool(self.unreadable) or not self.reached

    @property
    def stated(self) -> str:
        if not self.reached:
            tail = f" — {self.because}" if self.because else ""
            return f"{self.source} could not be read{tail}"

        parts = [
            f"{self.source}: {self.reports_read} of {self.reports_seen} "
            "Item 5.02 reports read",
            f"{self.events_kept} leadership events kept",
        ]

        if self.declined:
            parts.append(f"{len(self.declined)} reports declined")

        if self.unreadable:
            parts.append(f"{len(self.unreadable)} reports unreadable")

        return ", ".join(parts)


@dataclass(frozen=True, slots=True)
class LeadershipEventFeed:
    """The leadership events held for one company, newest first."""

    events: tuple[LeadershipEvent, ...] = ()
    health: LeadershipFeedHealth = field(
        default_factory=lambda: LeadershipFeedHealth(
            source="SEC EDGAR",
            reached=False,
            because="the source has not been read",
        )
    )

    @property
    def is_read(self) -> bool:
        return self.health.reached
