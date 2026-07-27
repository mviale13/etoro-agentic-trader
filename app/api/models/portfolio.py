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
    positions: int
    allocation: AllocationResponse
    risk_flags: list[str]
