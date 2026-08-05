"""When one company next reports, as its own calendar publishes it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.provenance import Provenance


def written(day: date, today: date) -> str:
    """
    A date as an investor reads it, carrying the year only when it differs.

    "Aug 11" is unambiguous within the year it is read in; a report that
    falls the other side of December is not, so that one keeps its year.
    """

    if day.year != today.year:
        return f"{day:%b} {day.day}, {day.year}"

    return f"{day:%b} {day.day}"


@dataclass(frozen=True, slots=True)
class EarningsWindow:
    """
    One company's published report window.

    Usually a single expected day, sometimes a first-to-last pair when the
    company has not fixed the date. It is scheduling fact and nothing else:
    it says when the company is expected to report, and says nothing
    whatever about what the report will contain. Every sentence produced
    here is dated, and none of them anticipates an outcome.
    """

    #: The published day, or the window's first day.
    starts_on: date

    #: The window's last day, or None when a single day was published.
    ends_on: date | None

    reading: Provenance

    @property
    def last_day(self) -> date:
        """The last day the report could still land on."""

        return self.ends_on or self.starts_on

    @property
    def spans_days(self) -> bool:
        """Whether the company published a range rather than a day."""

        return self.ends_on is not None and self.ends_on != self.starts_on

    def is_ahead_of(self, today: date) -> bool:
        """
        Whether this report is still to come.

        The provider keeps publishing a window for a while after the report
        ran. That is the last report, not the next one, and telling them
        apart is what stops a past date being offered as a reason to act.
        """

        return self.last_day >= today

    def starts_in_days(self, today: date) -> int:
        """How many days until the window opens; negative once it has."""

        return (self.starts_on - today).days

    def stated(self, today: date) -> str:
        """One dated sentence an investor can read, and nothing beyond it."""

        opens = written(self.starts_on, today)

        if not self.is_ahead_of(today):
            if self.spans_days:
                return (
                    f"Reported earnings between {opens} and "
                    f"{written(self.last_day, today)}."
                )

            return f"Reported earnings on {opens}."

        days = self.starts_in_days(today)

        if self.spans_days:
            closes = written(self.last_day, today)

            # A window that has already opened gets no countdown: it is not
            # "in -1 days", it is running.
            if days <= 0:
                return f"Reports earnings between {opens} and {closes}."

            return (
                f"Reports earnings in {days} day{'s' if days != 1 else ''}, "
                f"between {opens} and {closes}."
            )

        if days == 0:
            return f"Reports earnings today ({opens})."

        if days == 1:
            return f"Reports earnings tomorrow ({opens})."

        return f"Reports earnings in {days} days ({opens})."


@dataclass(frozen=True, slots=True)
class EarningsSchedule:
    """
    What one reading of a company's calendar produced.

    The three answers are kept apart, because merging them would report a
    provider failure as a quiet quarter:

    - a window is published — `window` carries it;
    - nothing is published — `window` is None and `unread` is False;
    - the calendar could not be read — `unread` is True.

    A security with no company behind it is never asked, and carries no
    schedule at all. That fourth state is the absence of this object, not a
    value inside it: a fund has no earnings call, and manufacturing "no
    date published" for one would answer a question nobody may ask of it.
    """

    window: EarningsWindow | None = None

    #: True when the provider could not be read this cycle. Distinct from a
    #: company that simply has no date out: one is a gap in the platform,
    #: the other is a fact about the company.
    unread: bool = False
