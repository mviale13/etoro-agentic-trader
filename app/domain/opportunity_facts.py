from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpportunityFacts:
    symbol: str

    asset_type: str

    current_price: float

    daily_change_percent: float

    source: str
