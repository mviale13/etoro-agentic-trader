from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Allocation:
    cash: float
    stocks: float
    etfs: float
    crypto: float
    unclassified: float


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    allocation: Allocation
    total_value: float
    positions: int
    largest_position: str | None
    largest_position_pct: float
    risk_flags: tuple[str, ...]
    total_value_eur: float = 0.0

    # Real dashboard values.
    available_cash_usd: float = 0.0
    available_cash_eur: float = 0.0
    invested_usd: float = 0.0
    invested_eur: float = 0.0
    liquidity_pct: float = 0.0
    last_sync: datetime | None = None

    @property
    def total_value_usd(self) -> float:
        return self.total_value
