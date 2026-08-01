from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    symbol: str
    quantity: float
    invested_usd: float
    market_value_usd: float
    unrealized_pnl_usd: float
    asset_class: str | None = None

    #: Broker instrument identifier. Symbols are resolved from this during
    #: perception, so an unresolved holding still reports a real identity.
    instrument_id: int = 0

    @property
    def is_resolved(self) -> bool:
        """True when the holding carries a tradeable ticker symbol."""
        return bool(self.symbol) and not self.symbol.startswith("#")
