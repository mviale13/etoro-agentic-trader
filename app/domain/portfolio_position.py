from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    symbol: str
    quantity: float
    invested_usd: float
    market_value_usd: float
    unrealized_pnl_usd: float
    asset_class: str | None = None
