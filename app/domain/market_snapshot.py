from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketQuote:
    symbol: str
    name: str
    price: float
    change_percent: float
    currency: str = "USD"

@dataclass(frozen=True, slots=True)
class MarketData:
    quotes: tuple[MarketQuote, ...]
    vix: float | None
    
@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    quotes: tuple[MarketQuote, ...]
    market_mood: str
    volatility: str
    summary: str
    timestamp: datetime

    def quote(self, symbol: str) -> MarketQuote | None:
        normalized = symbol.upper().strip()

        for item in self.quotes:
            if item.symbol.upper() == normalized:
                return item

        return None