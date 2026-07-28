from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MarketFact:
    symbol: str
    name: str
    price: float
    change_percent: float
    source: str
    as_of: datetime


@dataclass(frozen=True, slots=True)
class MarketFacts:
    instruments: tuple[MarketFact, ...]
    vix: float | None
    source: str
    as_of: datetime

    def quote(
        self,
        symbol: str,
    ) -> MarketFact | None:
        normalized = symbol.upper().strip()

        for instrument in self.instruments:
            if instrument.symbol.upper() == normalized:
                return instrument

        return None
