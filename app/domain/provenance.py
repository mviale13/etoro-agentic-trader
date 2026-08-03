"""Where a measurement came from, and when."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, slots=True)
class Provenance:
    """
    The origin of one reading.

    Evidence used to arrive undated and unattributed, and a single date on
    a bag of readings described whichever one happened to set it. A price
    fetched a second ago and a price replayed from a fifteen-minute cache
    were indistinguishable objects, so nothing downstream could ask how old
    a number was, and nothing on screen could tell the investor.

    Reliability is a claim about a particular number at a particular time.
    It cannot be made about a value that does not know when it was taken or
    who reported it.
    """

    #: The service that reported it, named as the investor would see it.
    source: str

    observed_at: datetime

    def age(
        self,
        now: datetime | None = None,
    ) -> timedelta:
        """How long ago this was read."""

        return (now or datetime.now(UTC)) - self.observed_at

    def stated(
        self,
        now: datetime | None = None,
    ) -> str:
        """
        The age as the investor should read it.

        Coarse on purpose. "14 minutes ago" is what matters about a price;
        the second it was taken is not, and printing it would suggest a
        precision the number does not have.
        """

        age = self.age(now)
        minutes = int(age.total_seconds() // 60)

        if minutes < 1:
            when = "just now"
        elif minutes < 60:
            when = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif age.days < 1:
            hours = minutes // 60
            when = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif age.days == 1:
            when = "yesterday"
        else:
            when = f"{age.days} days ago"

        return f"{self.source}, {when}"

    def is_older_than(
        self,
        limit: timedelta,
        now: datetime | None = None,
    ) -> bool:
        """
        Whether this reading has aged past what the caller will accept.

        Freshness belongs where a reading is used, not where it is fetched.
        A price is worthless at fifteen minutes and an asset class is good
        for months; only the caller knows which it is holding.
        """

        return self.age(now) > limit


def oldest(
    *readings: Provenance | None,
) -> Provenance | None:
    """
    The least recent of several readings, ignoring those absent.

    What a collection of evidence can honestly be dated to is the age of
    its stalest part, not the age of whichever part was written last.
    """

    present = [item for item in readings if item is not None]

    if not present:
        return None

    return min(present, key=lambda item: item.observed_at)
