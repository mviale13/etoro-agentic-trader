from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Allocation:
    cash: float
    stocks: float
    etfs: float
    crypto: float


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    allocation: Allocation

    total_value: float

    positions: int

    largest_position: str | None

    largest_position_pct: float

    risk_flags: list[str]
