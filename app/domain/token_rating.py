"""Another analyst's published opinion of a token, carried as exactly that."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class RatingDimension:
    """One dimension of a published rating, as the rater scored it."""

    #: Worded for the investor, not the field name.
    label: str

    #: The rater's own percentage, 0-100.
    score: float


@dataclass(frozen=True, slots=True)
class TokenRating:
    """
    A third party's rating of a token, with its name attached.

    **This is not evidence and it is not this platform's judgement.** It
    is one named analyst's opinion, published on a stated date, carried
    so an investor can read it and go and check it. The rule it lives
    under is the one the Yahoo boundary already states: an observation
    label does not launder a copy into evidence. Nothing here may reach
    a playbook, a score or a decision — it is shown, attributed, and
    consumed by nothing.

    It exists because the platform's own crypto reading is thin and
    honest about being thin: scale, liquidity, issuance and age, and for
    a token the provider cannot price, almost nothing at all. A rater
    who publishes six dimensions and a review date says more than this
    platform can, and saying so is better than an empty card — provided
    the investor can see whose opinion it is.
    """

    symbol: str

    #: The rater's own name for the token, kept so a reader can see
    #: which security was actually rated.
    name: str

    #: AAA to D, as published.
    level: str

    #: The rater's overall score, 0-100.
    score: float

    dimensions: tuple[RatingDimension, ...]

    #: When the rater last reviewed it. A rating is reviewed
    #: periodically rather than continuously, so this is the date that
    #: matters — not when this platform happened to read it.
    reviewed_at: datetime | None

    #: Where the investor can read the rating and the report themselves.
    #: Printed with the rating, because an opinion an investor cannot
    #: go and check is one they have to take on trust.
    page_url: str | None
    report_url: str | None

    #: When *this platform* read it, and from whom.
    reading: Provenance

    @property
    def stated(self) -> str:
        """The rating as a sentence, naming whose it is."""

        return f"{self.level} ({self.score:.0f}/100) by {self.reading.source}"
