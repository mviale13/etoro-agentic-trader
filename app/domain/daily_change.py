"""One day's price move, and whether this platform actually has one.

The input Momentum reads. It exists because `float` could not carry
the difference between *the security did not move* and *nothing was
measured*, and the adapter — needing a number — wrote `0.0` for both.
Downstream that read as NEUTRAL at confidence 60, which is an
analytical conclusion drawn from an acquisition failure.

Three questions travel with the number, and they fail independently:

- **Is it a measurement?** `absence` says which kind of nothing, using
  `ClaimAbsence` — the vocabulary #134 already built for exactly this.
- **Are we entitled to read it as a price change?** `warrant`, from
  the provider boundary. Not an ordering: `MomentumSignalService`
  states an explicit membership and says why.
- **What period does it describe?** `basis`. The change may be a
  perfectly valid last-session move while the word *today* is false,
  and the sentence must not claim more than the evidence carries.

A genuine `0.0` is a value and stays one: `is_measured` is true, the
band is entered, and NEUTRAL remains available. Missing is a state,
and it never reaches a band at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_translation import TranslationWarrant


class ChangeBasis(StrEnum):
    """What period a computed change actually covers.

    Derived from evidence the provider already supplies and this
    platform previously discarded: the closing series' own dates. No
    trading calendar is consulted and none is invented — the only
    comparison made is between the last close's date and the date the
    reading was taken.
    """

    #: The last close carries the same calendar date as the reading,
    #: so the move is this session's and "today" is established.
    SAME_SESSION = "same_session"

    #: The last close predates the reading. The change is a real move
    #: over the instrument's most recent session — and it is not
    #: today's, which is what a Friday close read on a Sunday is.
    LAST_AVAILABLE_SESSION = "last_available_session"

    #: No date survived to compare. The change may be either of the
    #: above and this platform cannot say which.
    UNKNOWN_SESSION = "unknown_session"

    @property
    def window(self) -> str:
        """How a sentence may refer to the period, worded here once.

        The whole point of the enum: only one member yields the word
        *today*, and it is the one where a date was actually checked.
        """

        return _WINDOWS[self]

    @property
    def establishes_today(self) -> bool:
        return self is ChangeBasis.SAME_SESSION


_WINDOWS = {
    ChangeBasis.SAME_SESSION: "today",
    ChangeBasis.LAST_AVAILABLE_SESSION: "in its last session",
    ChangeBasis.UNKNOWN_SESSION: "in its most recent reading",
}


@dataclass(frozen=True, slots=True)
class DailyChange:
    """A daily price move, with what is and is not established about it."""

    #: The move in percentage points. `None` where nothing was
    #: measured — never a sentinel, and never zero standing in for
    #: absence.
    percent: float | None

    #: The authority under which the underlying reading is translated.
    warrant: TranslationWarrant

    basis: ChangeBasis = ChangeBasis.UNKNOWN_SESSION

    #: Which kind of nothing, where there is one.
    absence: ClaimAbsence | None = None

    #: The last close's own date, where it survived the adapter.
    session_date: date | None = None

    def __post_init__(self) -> None:
        if self.percent is None and self.absence is None:
            raise ValueError(
                "a daily change with no value and no reason is the state "
                "that let a failed acquisition read as a flat session"
            )

        if self.percent is not None and self.absence is not None:
            raise ValueError(
                "a daily change carries a measurement or an absence, never both"
            )

    @property
    def is_measured(self) -> bool:
        """Whether a move was observed at all.

        True for a genuine `0.0`. That is the distinction the whole
        type exists for: zero is a value, missing is a state.
        """

        return self.percent is not None

    def admissible_under(
        self,
        warrants: frozenset[TranslationWarrant],
    ) -> bool:
        """Whether this may be banded by a consumer requiring `warrants`.

        Two different questions, both required: a number nobody
        measured cannot be banded, and neither can one whose
        translation the consumer does not accept.

        **The consumer supplies the membership.** This type does not
        know which warrants are good enough, because that is a property
        of the analysis being performed rather than of the number —
        Momentum can read a change under a warrant that would be
        useless to a consumer of magnitudes, and saying so is the
        consumer's job.
        """

        return self.is_measured and self.warrant in warrants

    @property
    def window(self) -> str:
        """The period a sentence may claim for this move."""

        return self.basis.window

    def refusal(
        self,
        warrants: frozenset[TranslationWarrant],
    ) -> str:
        """Why this establishes no movement, worded here once."""

        if self.admissible_under(warrants):
            return ""

        if self.absence is not None:
            return f"Daily price change is unavailable: {self.absence.stated}."

        return (
            "Daily price change cannot be read as a price move: the "
            f"translation behind it is {self.warrant.stated.lower()} — "
            f"{self.warrant.because}."
        )

    @classmethod
    def measured(
        cls,
        percent: float,
        *,
        warrant: TranslationWarrant,
        basis: ChangeBasis = ChangeBasis.UNKNOWN_SESSION,
        session_date: date | None = None,
    ) -> DailyChange:
        return cls(
            percent=percent,
            warrant=warrant,
            basis=basis,
            session_date=session_date,
        )

    @classmethod
    def unmeasured(
        cls,
        absence: ClaimAbsence,
        *,
        warrant: TranslationWarrant,
    ) -> DailyChange:
        return cls(percent=None, warrant=warrant, absence=absence)
