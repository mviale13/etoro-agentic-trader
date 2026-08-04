"""The worst fall this account has actually taken."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class PortfolioDrawdown:
    """
    A measurement of the account's own equity curve.

    Not the average of the drawdowns of the things it holds. Positions
    fall at different times, and an account that lost 40% is a different
    account from one holding four securities that each lost 40% in a
    different quarter.

    Every field is read off an observed window, which is named here rather
    than implied: a 12% fall over five weeks and a 12% fall over five years
    are not the same statement about an account.
    """

    #: Deepest peak-to-trough fall in the window, as a positive ratio.
    depth: float

    peak_on: date
    peak_value_usd: float

    trough_on: date
    trough_value_usd: float

    #: How far below its running peak the account ended the window.
    #: Zero when it ended at a new high.
    current_depth: float

    #: The window this was measured over, and how many days it holds.
    starts_on: date
    ends_on: date
    observations: int

    #: Who reported the underlying balances, and when they were read.
    reading: Provenance

    @property
    def recovered(self) -> bool:
        """Whether the account has since climbed back to its peak."""

        return self.current_depth <= 0.0
