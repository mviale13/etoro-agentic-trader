from dataclasses import dataclass
from datetime import datetime

from app.domain.provenance import Provenance


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

    #: When this price was read, and from where.
    #:
    #: A quote replayed from cache keeps the time it was actually taken. A
    #: price is a claim about now, and without this a fifteen-minute-old
    #: one was indistinguishable from a live one to everything downstream.
    reading: Provenance | None = None


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

    #: What the VIX actually read, beside the band it falls in.
    #:
    #: The number was fetched, classified into "low", "medium" or "high"
    #: and then dropped. An adjective cannot be compared with yesterday's
    #: adjective, and a reader who wants to know how frightened the market
    #: is deserves the figure that decided the word.
    vix: float | None = None

    #: Where these quotes came from and when, taken from the least
    #: reliable of them. Nothing could date the market snapshot before:
    #: its `timestamp` is when this object was assembled, which is not
    #: when anything in it was observed.
    reading: Provenance | None = None

    def quote(self, symbol: str) -> MarketQuote | None:
        normalized = symbol.upper().strip()

        for item in self.quotes:
            if item.symbol.upper() == normalized:
                return item

        return None
