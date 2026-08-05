"""When the companies the investor holds or watches report next."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.earnings_schedule import EarningsWindow


@dataclass(frozen=True, slots=True)
class EarningsDate:
    """
    One company's place in the book's calendar.

    The window itself is an `EarningsWindow` — the same object the
    security's own investment case carries, so "when does this company
    report" has one implementation whether it is asked of the book or of
    a single holding.
    """

    symbol: str
    name: str

    #: Whether the account holds this company, as opposed to only
    #: watching it. Stated so the page can say which is which rather
    #: than leaving the reader to remember their own book.
    held: bool

    #: When this company is expected to report, and where that was read.
    window: EarningsWindow


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
