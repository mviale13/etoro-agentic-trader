import asyncio
from datetime import UTC, datetime
from typing import Protocol

from app.domain.company_facts import CompanyFacts
from app.domain.market_snapshot import MarketQuote
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.yahoo_market_provider import YahooInstrument


class MarketQuoteProvider(Protocol):
    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]: ...


class ValuationProvider(Protocol):
    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot: ...


class CompanyFactsService:
    def __init__(
        self,
        market_provider: MarketQuoteProvider | None = None,
        valuation_provider: ValuationProvider | None = None,
    ) -> None:
        self._market_provider = market_provider or CachedMarketProvider()
        self._valuation_provider = valuation_provider or CachedValueProvider()

    async def build(
        self,
        item: WatchlistItem,
    ) -> CompanyFacts:
        instrument = YahooInstrument(
            yahoo_symbol=item.symbol,
            movrvest_symbol=item.symbol,
            name=item.name,
        )

        quotes_task = asyncio.create_task(self._market_provider.quotes((instrument,)))

        valuation_task = asyncio.to_thread(
            self._valuation_provider.snapshot,
            item.symbol,
        )

        quotes, valuation = await asyncio.gather(
            quotes_task,
            valuation_task,
        )

        quote = self._find_quote(
            quotes,
            item.symbol,
        )

        return CompanyFacts(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            name=item.name,
            asset_type=str(item.asset_type_id),
            exchange=str(item.exchange_id),
            # The oldest reading in here, so nothing is dated fresher than
            # the evidence actually is.
            observed_at=valuation.observed_at or datetime.now(UTC),
            # Market
            current_price=quote.price if quote is not None else None,
            daily_change_pct=(quote.change_percent if quote is not None else None),
            market_cap=valuation.market_cap,
            # Valuation
            forward_pe=valuation.forward_pe,
            # Growth
            revenue_growth=None,
            earnings_growth=None,
            # Profitability
            gross_margin=None,
            operating_margin=None,
            net_margin=None,
            # Capital efficiency
            roe=None,
            roic=None,
            # Balance sheet
            debt_to_equity=None,
            current_ratio=None,
            # Cash generation
            operating_cash_flow=None,
            free_cash_flow=None,
            # Shareholder returns
            eps=valuation.eps,
            dividend_yield=valuation.dividend_yield,
            # Classification
            sector=None,
            industry=None,
        )

    @staticmethod
    def _find_quote(
        quotes: tuple[MarketQuote, ...],
        symbol: str,
    ) -> MarketQuote | None:
        normalized = symbol.upper().strip()

        for quote in quotes:
            if quote.symbol.upper() == normalized:
                return quote

        return None
