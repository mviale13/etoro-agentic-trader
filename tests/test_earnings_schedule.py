"""One company's report window, and the sentence it is entitled to."""

from datetime import UTC, date, datetime

from app.domain.earnings_schedule import EarningsSchedule, EarningsWindow
from app.domain.provenance import Provenance

TODAY = date(2026, 8, 5)

READING = Provenance(
    source="Yahoo Finance",
    observed_at=datetime(2026, 8, 5, 6, 0, tzinfo=UTC),
)


def window(starts_on: date, ends_on: date | None = None) -> EarningsWindow:
    return EarningsWindow(starts_on=starts_on, ends_on=ends_on, reading=READING)


def test_a_report_ahead_is_stated_with_its_countdown_and_its_date() -> None:
    """
    Both, deliberately. "In 6 days" is what an investor acts on; the date
    is what makes the claim checkable, and a countdown without one ages
    into a lie the moment the page is left open.
    """

    stated = window(date(2026, 8, 11)).stated(TODAY)

    assert stated == "Reports earnings in 6 days (Aug 11)."


def test_today_and_tomorrow_are_named_rather_than_counted() -> None:
    assert window(TODAY).stated(TODAY) == "Reports earnings today (Aug 5)."

    assert (
        window(date(2026, 8, 6)).stated(TODAY) == "Reports earnings tomorrow (Aug 6)."
    )


def test_a_report_the_other_side_of_the_year_carries_its_year() -> None:
    """A bare "Feb 3" read in December could name either of two days."""

    assert (
        window(date(2027, 2, 3)).stated(date(2026, 12, 20))
        == "Reports earnings in 45 days (Feb 3, 2027)."
    )


def test_an_unfixed_date_keeps_both_ends_of_its_window() -> None:
    """The company published a range, so the sentence states a range."""

    stated = window(date(2026, 8, 11), date(2026, 8, 13)).stated(TODAY)

    assert stated == "Reports earnings in 6 days, between Aug 11 and Aug 13."


def test_a_window_already_open_is_not_counted_down_to() -> None:
    """It is not "in -1 days"; it is running."""

    stated = window(date(2026, 8, 4), date(2026, 8, 7)).stated(TODAY)

    assert stated == "Reports earnings between Aug 4 and Aug 7."


def test_a_report_already_given_is_stated_in_the_past() -> None:
    """
    The provider keeps publishing a window after the report ran.

    That is the last report, not the next one. Worded as the next one it
    would offer a date that has passed as a reason to act now.
    """

    assert window(date(2026, 8, 1)).stated(TODAY) == "Reported earnings on Aug 1."


def test_a_window_knows_whether_it_is_still_ahead() -> None:
    assert window(TODAY).is_ahead_of(TODAY) is True

    assert window(date(2026, 8, 1)).is_ahead_of(TODAY) is False

    # The last day of a range is what decides it, not the first.
    assert window(date(2026, 8, 3), date(2026, 8, 6)).is_ahead_of(TODAY) is True


def test_the_two_absences_are_different_objects() -> None:
    """
    Nothing published, and nothing readable, never share a value.

    A provider that did not answer reported as "no date published" would
    tell the investor the company has a quiet quarter ahead, which nobody
    established.
    """

    unscheduled = EarningsSchedule()
    unread = EarningsSchedule(unread=True)

    assert unscheduled.window is None and unscheduled.unread is False
    assert unread.window is None and unread.unread is True
