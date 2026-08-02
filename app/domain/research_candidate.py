"""A security the investor could research but does not own."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchCandidate:
    """
    One instrument the investor's watchlists name and the portfolio lacks.

    A candidate is a fact about attention, not a judgement: it says the
    investor is watching this security, not that it is worth buying.
    """

    symbol: str
    name: str

    #: The watchlist that names it.
    source: str

    instrument_id: int
