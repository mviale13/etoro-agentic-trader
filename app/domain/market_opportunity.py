from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketOpportunity:
    symbol: str
    asset_type: str

    source: str
