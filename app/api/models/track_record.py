"""What the platform serves about its own decisions' outcomes."""

from pydantic import BaseModel


class OutcomeResponse(BaseModel):
    """One recorded decision, and the price move observed since."""

    symbol: str
    state: str

    #: Null where the decision carried none. The price move is still
    #: measured: what the security did does not depend on whether the
    #: platform put a number on the decision.
    conviction: int | None
    decided_on: str

    #: The close the move is measured from, and the day it belongs to —
    #: not necessarily the decision day; markets shut.
    priced_on: str

    change_pct: float
    days_elapsed: int

    #: Whether the move so far agrees with what the decision implied.
    #: Null where the decision implied nothing (MONITOR, INVESTIGATE) or
    #: the security has barely moved — evidence for nobody.
    agreed: bool | None

    #: The same finding in the platform's own words, worded once here so
    #: no surface invents its own: "as decided", "against the decision",
    #: "not a call".
    verdict: str

    #: Who priced this, and when.
    reading: str


class UnscoredReasonResponse(BaseModel):
    """Why a group of recorded decisions could not be measured yet."""

    reason: str
    count: int


class TrackRecordResponse(BaseModel):
    """
    Every recorded decision old enough to measure, and everything not.

    `hit_rate` is null until enough calls exist for a rate to mean
    anything; `minimum_calls` states the bar so the page can say how far
    away it is rather than showing an empty gauge.
    """

    recorded: int
    measured: int
    calls: int
    agreed: int
    hit_rate: float | None
    minimum_calls: int
    unscored_total: int
    outcomes: list[OutcomeResponse]
    unscored_reasons: list[UnscoredReasonResponse]
