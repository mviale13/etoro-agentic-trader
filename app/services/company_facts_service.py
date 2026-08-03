import asyncio
from typing import Protocol

from app.domain.asset_class import AssetClass
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
        asset_class = AssetClass.from_etoro(item.asset_type_id)

        instrument = YahooInstrument.for_security(
            item.symbol,
            item.name,
            asset_class,
        )

        quotes_task = asyncio.create_task(self._market_provider.quotes((instrument,)))

        # The resolved ticker, not the broker's. `BTC` returns nothing
        # from the fundamentals endpoint for the same reason it returns
        # nothing from the quote one; this path only escaped it while
        # crypto fundamentals were being skipped altogether.
        quotes, valuation = await asyncio.gather(
            quotes_task,
            self._valuation(instrument.yahoo_symbol),
        )

        quote = self._find_quote(
            quotes,
            item.symbol,
        )

        # `marketCap` means a network's total value for a token and a
        # company's equity value for a business. The same field, two
        # different claims, so which fields are read is decided by which
        # kind of thing this is.
        is_token = asset_class.has_no_company

        return CompanyFacts(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            name=item.name,
            asset_type=asset_class.value,
            exchange=str(item.exchange_id),
            # Each half dated by the call that produced it. These are two
            # requests to one provider and they age separately: a quote is
            # good for fifteen minutes, fundamentals for a day.
            price_reading=quote.reading if quote is not None else None,
            fundamentals_reading=valuation.reading,
            # Market
            current_price=quote.price if quote is not None else None,
            daily_change_pct=(quote.change_percent if quote is not None else None),
            market_cap=valuation.market_cap,
            realized_volatility=(
                quote.realized_volatility if quote is not None else None
            ),
            max_drawdown=(quote.max_drawdown if quote is not None else None),
            # What a token has. Absent for a company, which has the
            # balance-sheet fields below instead.
            circulating_supply=(valuation.circulating_supply if is_token else None),
            max_supply=valuation.max_supply if is_token else None,
            volume_24h=valuation.volume_24h if is_token else None,
            inception=valuation.inception if is_token else None,
            # Valuation. A token has no earnings to be priced against, so
            # these stay absent however populated the response was.
            forward_pe=valuation.forward_pe if not is_token else None,
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
            eps=valuation.eps if not is_token else None,
            dividend_yield=valuation.dividend_yield if not is_token else None,
            # Classification
            sector=None,
            industry=None,
        )

    async def _valuation(
        self,
        yahoo_symbol: str,
    ) -> ValuationSnapshot:
        """
        Whatever the provider knows about this security.

        The response is not read as company facts regardless of what the
        security is. A cryptocurrency has no earnings, no dividend and no
        price/earnings ratio, and the provider reports a network's total
        value under the same `marketCap` field a business reports its
        equity value under — read as company quality, that made Bitcoin a
        large-cap company. What it does have, this call already returns:
        supply, issuance cap, turnover and age. Which of those reach the
        facts is decided below, by what the asset is.
        """

        return await asyncio.to_thread(
            self._valuation_provider.snapshot,
            yahoo_symbol,
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
