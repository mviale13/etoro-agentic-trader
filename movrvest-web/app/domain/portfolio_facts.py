from dataclasses import dataclass

from app.models.account import Position


@dataclass(frozen=True)
class PortfolioFacts:
    """
    Pure facts about the investor's portfolio.

    This object contains observations only.
    No interpretation or recommendations belong here.
    """

    total_value: float

    invested_value: float

    available_cash: float

    number_of_positions: int

    cash_percentage: float

    largest_position: str | None

    largest_position_weight: float

    positions: list[Position]
