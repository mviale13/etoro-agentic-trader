import asyncio
from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.earnings_schedule import EarningsSchedule
from app.domain.market_snapshot import MarketQuote
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.earnings_provider import CachedEarningsProvider, ReadDates
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


class EarningsProvider(Protocol):
    def read(
        self,
        symbol: str,
    ) -> ReadDates: ...


class CompanyFactsService:
    def __init__(
        self,
        market_provider: MarketQuoteProvider | None = None,
        valuation_provider: ValuationProvider | None = None,
        earnings_provider: EarningsProvider | None = None,
    ) -> None:
        # The read-only doors, because this runs once per security on
        # every page view. Acquiring here made opening a page the act
        # that spends a rate limit and waits for a provider: a single
        # dossier downloaded a year of daily closes for every holding
        # and `SPY` thirteen times over, and the investor waited.
        #
        # A caller that means to acquire says so by passing the
        # acquiring door — `MarketAcquisitionService` is the one that
        # does, and it asks for the whole book in one batch.
        self._market_provider = market_provider or CachedMarketProvider.stored()
        self._valuation_provider = valuation_provider or CachedValueProvider.stored()
        self._earnings_provider = earnings_provider or CachedEarningsProvider.stored()

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
        quotes, valuation, earnings = await asyncio.gather(
            quotes_task,
            self._valuation(instrument.yahoo_symbol),
            self._earnings(item.symbol, asset_class),
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
            # The identity's own reading, carried from the watchlist fetch
            # that named this instrument. It ages on its own cadence, apart
            # from the quote and the fundamentals beside it.
            identity_reading=item.reading,
            # Market
            current_price=quote.price if quote is not None else None,
            daily_change_pct=(quote.change_percent if quote is not None else None),
            market_cap=valuation.market_cap,
            realized_volatility=(
                quote.realized_volatility if quote is not None else None
            ),
            max_drawdown=(quote.max_drawdown if quote is not None else None),
            market_sensitivity=(
                quote.market_sensitivity if quote is not None else None
            ),
            # When this company next reports. Absent entirely for anything
            # that does not report, because it was never asked.
            earnings=earnings,
            # What a token has. Absent for a company, which has the
            # balance-sheet fields below instead.
            circulating_supply=(valuation.circulating_supply if is_token else None),
            max_supply=valuation.max_supply if is_token else None,
            volume_24h=valuation.volume_24h if is_token else None,
            inception=valuation.inception if is_token else None,
            # Valuation. A token has no earnings to be priced against, so
            # these stay absent however populated the response was.
            forward_pe=valuation.forward_pe if not is_token else None,
            # Growth, profitability, balance sheet and cash generation, read
            # from the same call as the valuation above. A token has none of
            # these — it has the supply fields instead — so they are populated
            # for a company only, and stay absent rather than zero elsewhere.
            revenue_growth=valuation.revenue_growth if not is_token else None,
            earnings_growth=valuation.earnings_growth if not is_token else None,
            gross_margin=valuation.gross_margin if not is_token else None,
            operating_margin=valuation.operating_margin if not is_token else None,
            net_margin=valuation.net_margin if not is_token else None,
            # Return on equity is reported; return on invested capital is not,
            # so it stays absent rather than being derived from figures the
            # provider did not give.
            roe=valuation.return_on_equity if not is_token else None,
            roic=None,
            debt_to_equity=valuation.debt_to_equity if not is_token else None,
            current_ratio=valuation.current_ratio if not is_token else None,
            operating_cash_flow=(
                valuation.operating_cash_flow if not is_token else None
            ),
            free_cash_flow=valuation.free_cash_flow if not is_token else None,
            # Shareholder returns
            eps=valuation.eps if not is_token else None,
            dividend_yield=valuation.dividend_yield if not is_token else None,
            # Classification
            sector=valuation.sector if not is_token else None,
            industry=valuation.industry if not is_token else None,
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

    async def _earnings(
        self,
        symbol: str,
        asset_class: AssetClass,
    ) -> EarningsSchedule | None:
        """
        When this company next reports, or nothing where the question
        does not apply.

        Only a company is asked. A fund or a token has no earnings call,
        and asking would manufacture an absence for an instrument the
        question was never valid for — the same reason the book's calendar
        asks companies only.

        The read is the one the book's calendar already takes, from the
        same daily cache under the same key, so a company that appears on
        both the Markets page and its own dossier reports on one date.
        """

        if asset_class is not AssetClass.STOCK:
            return None

        try:
            read = await asyncio.to_thread(self._earnings_provider.read, symbol)
        except Exception:
            # A calendar that could not be read is not a company with no
            # date out. The investment case says which of the two it is.
            return EarningsSchedule(unread=True)

        return EarningsSchedule(window=read.window())

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
