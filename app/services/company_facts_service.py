import asyncio
from datetime import UTC, datetime
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

        quotes, valuation = await asyncio.gather(
            quotes_task,
            self._valuation(item.symbol, asset_class),
        )

        quote = self._find_quote(
            quotes,
            item.symbol,
        )

        return CompanyFacts(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            name=item.name,
            asset_type=asset_class.value,
            exchange=str(item.exchange_id),
            # The oldest reading in here, so nothing is dated fresher than
            # the evidence actually is. A security with no fundamentals to
            # read has only its quote, which is never served stale.
            observed_at=valuation.observed_at or datetime.now(UTC),
            # Market
            current_price=quote.price if quote is not None else None,
            daily_change_pct=(quote.change_percent if quote is not None else None),
            market_cap=valuation.market_cap,
            realized_volatility=(
                quote.realized_volatility if quote is not None else None
            ),
            max_drawdown=(quote.max_drawdown if quote is not None else None),
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

    async def _valuation(
        self,
        symbol: str,
        asset_class: AssetClass,
    ) -> ValuationSnapshot:
        """
        The company fundamentals behind this security, if it has a company.

        A cryptocurrency has no earnings, no dividend and no price/earnings
        ratio — but the provider answers anyway, reporting a network's total
        value under the same `marketCap` field a business reports its equity
        value under. Read as company facts, that number becomes evidence
        that Bitcoin is a large-cap company. So nothing is read at all: the
        fundamentals a crypto asset does not have are reported as absent,
        and the request is not spent.
        """

        if not asset_class.has_company_fundamentals:
            return ValuationSnapshot(
                forward_pe=None,
                trailing_pe=None,
                peg_ratio=None,
                dividend_yield=None,
            )

        return await asyncio.to_thread(
            self._valuation_provider.snapshot,
            symbol,
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
