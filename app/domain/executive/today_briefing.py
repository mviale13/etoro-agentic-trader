"""What the investor needs to know today, before anything else."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BriefingLine:
    """
    One counted fact about today.

    Counted, never characterised. "3 recommendations changed" can be
    checked against the feed below it; "significant activity" cannot be
    checked against anything, and a briefing whose lines cannot be
    verified is a mood, not a report.
    """

    statement: str

    #: True where the line is something to look at, false where it is the
    #: reassurance that there is nothing. Both are worth printing — a
    #: quiet day is information — but only one of them is news, and a
    #: surface that cannot tell them apart will style them the same.
    notable: bool = False


@dataclass(frozen=True, slots=True)
class TodayBriefing:
    """
    The first thing the investor reads, and on most days the only thing.

    A Chief Investment Officer does not open a dashboard to ask what they
    own. They ask what changed and what deserves their attention, and the
    answer is usually "nothing" — which this says, rather than promoting
    the day's least uneventful fact to fill the space.

    Nothing here is executed or acted upon by the platform. It counts what
    the Artificial CIO decided and what the book's own calendar publishes;
    what the investor did about it is not recorded anywhere, and is
    therefore not claimed.
    """

    lines: tuple[BriefingLine, ...]

    #: The single thing that most deserves attention, already worded by
    #: the change that produced it. None on a day where nothing does,
    #: which is a real answer and the most common one.
    headline: str | None = None

    @property
    def is_quiet(self) -> bool:
        """Whether nothing today asks anything of the investor."""

        return self.headline is None and not any(line.notable for line in self.lines)
