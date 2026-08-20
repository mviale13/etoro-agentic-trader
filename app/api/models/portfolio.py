from datetime import datetime

from pydantic import BaseModel


class AllocationResponse(BaseModel):
    #: None where the broker stated no cash figure.
    cash: float | None
    stocks: float
    etfs: float
    crypto: float
    unclassified: float


class PortfolioResponse(BaseModel):
    total_value: float
    total_value_eur: float | None
    available_cash_usd: float | None
    available_cash_eur: float | None
    invested_usd: float
    invested_eur: float | None
    liquidity_pct: float | None
    positions: int
    allocation: AllocationResponse
    risk_flags: list[str]
    last_sync: datetime | None
    source: str
