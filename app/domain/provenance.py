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

    #: True when the source could not be reached and this is the most
    #: recent reading there is.
    #:
    #: Age alone cannot tell these apart. Fundamentals read yesterday
    #: because that is their cadence and fundamentals read yesterday
    #: because the provider did not answer this morning are the same date
    #: and a different situation — the second means the platform is
    #: running on memory, and the investor should be told so rather than
    #: discovering it.
    last_known: bool = False

    #: False when `observed_at` is the moment MOVRvest *received* the
    #: figure rather than a moment the source states it was observed.
    #:
    #: A receipt clock, named as one, on #223's precedent: the same
    #: ruling `PortfolioObservation` makes about eToro, arriving through
    #: the provider door instead of the broker one. It is set only where
    #: the source has been *measured* to state no observation time for
    #: the value it publishes — never as a convenience when a timestamp
    #: is merely inconvenient, because substituting the fetch moment for
    #: a stated one is the defect this flag exists to make impossible to
    #: commit silently.
    #:
    #: The default is True, so every reading whose source does state an
    #: observation time is unchanged and unqualified.
    observation_stated: bool = True

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

        # "received" rather than a bare age wherever the clock is a
        # receipt clock. The word is the whole disclosure at this
        # length: it says when the figure reached MOVRvest and claims
        # nothing about when the source observed it.
        if not self.observation_stated:
            when = f"received {when}"

        # Not "unreachable since": all that is known is that the most
        # recent attempt failed, not that every attempt between would have.
        if self.last_known:
            return f"{self.source} did not answer — last reading, {when}"

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


def least_reliable(
    *readings: Provenance | None,
) -> Provenance | None:
    """
    The reading that most qualifies a conclusion drawn from all of them.

    A source that did not answer outranks mere age. It is tempting to
    assume the degraded reading is also the stalest and let `oldest` carry
    it, and that is wrong: a last-known reading keeps the time it was
    originally taken, so moments after a failure it can be *newer* than a
    freshly fetched price sitting beside it. The flag would vanish exactly
    when it started mattering.

    Whichever reading is returned is returned intact, never relabelled —
    stamping "did not answer" onto the stalest reading would attribute a
    failure to whichever source happened to be oldest.
    """

    present = [item for item in readings if item is not None]

    if not present:
        return None

    degraded = [item for item in present if item.last_known]

    return min(degraded or present, key=lambda item: item.observed_at)


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
