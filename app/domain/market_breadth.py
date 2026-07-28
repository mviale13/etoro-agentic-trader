from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketBreadth:
    equities: str
    technology: str
    small_caps: str
    crypto: str
    commodities: str
    volatility: str
    dollar: str
    rates: str
