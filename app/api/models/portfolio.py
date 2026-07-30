from datetime import datetime

from pydantic import BaseModel


class AllocationResponse(BaseModel):
    cash: float
    stocks: float
    etfs: float
    crypto: float
    unclassified: float


class PortfolioResponse(BaseModel):
    total_value: float
    total_value_eur: float
    available_cash_usd: float
    available_cash_eur: float
    invested_usd: float
    invested_eur: float
    liquidity_pct: float
    positions: int
    allocation: AllocationResponse
    risk_flags: list[str]
    last_sync: datetime | None
    source: str
