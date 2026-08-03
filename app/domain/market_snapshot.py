from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketQuote:
    symbol: str
    name: str
    price: float
    change_percent: float
    currency: str = "USD"

    #: Annualised standard deviation of daily returns, as a ratio (0.28 is
    #: 28%). None when the series was too short to measure it.
    realized_volatility: float | None = None

    #: Deepest peak-to-trough fall over the observed window, as a positive
    #: ratio (0.34 is a 34% fall). None when unmeasured.
    max_drawdown: float | None = None


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
