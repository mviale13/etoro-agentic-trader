"""When the companies the investor holds or watches report next."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class EarningsDate:
    """
    One company's next published report window.

    The window is what the provider publishes: usually a single expected
    day, sometimes a first-to-last pair when the company has not fixed
    the date. It is scheduling fact, not prediction — nothing here says
    what the report will contain, only when it is expected.
    """

    symbol: str
    name: str

    #: The published day, or the window's first day.
    starts_on: date

    #: The window's last day, or None when a single day was published.
    ends_on: date | None

    #: Whether the account holds this company, as opposed to only
    #: watching it. Stated so the page can say which is which rather
    #: than leaving the reader to remember their own book.
    held: bool

    reading: Provenance


@dataclass(frozen=True, slots=True)
class EarningsCalendar:
    """
    The book's own earnings calendar — never the whole market's.

    Only companies the investor holds or watches appear, because those
    are the reports that can bear on a decision this platform makes.
    The two absences are kept apart: a company the provider publishes
    no upcoming date for is `unscheduled`, and one whose calendar could
    not be read this cycle is `unread`. Merging them would report a
    provider failure as a quiet quarter.
    """

    #: Reports still ahead, soonest first.
    upcoming: tuple[EarningsDate, ...]

    #: Windows the provider still publishes although they have passed —
    #: the company just reported and the next date is not out yet. Shown
    #: as what they are, most recent first, rather than sorted ahead of
    #: the reports that are actually coming.
    reported: tuple[EarningsDate, ...]

    #: Companies with no upcoming date published.
    unscheduled: tuple[str, ...]

    #: Companies whose calendar could not be read this cycle.
    unread: tuple[str, ...]
