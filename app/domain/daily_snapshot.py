from dataclasses import dataclass
from datetime import date

from app.domain.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class DailySnapshot:
    date: date
    portfolio: PortfolioSnapshot
