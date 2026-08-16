import asyncio
from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.daily_change import ChangeBasis, DailyChange
from app.domain.earnings_schedule import EarningsSchedule
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.market_snapshot import MarketQuote
from app.domain.monetary import MarketCapDenomination
from app.domain.provider_identity import CrossProviderIdentity, join_identity
from app.domain.provider_translation import TranslationWarrant
from app.domain.provider_translations import governed
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.earnings_provider import CachedEarningsProvider, ReadDates
from app.providers.yahoo_market_provider import YahooInstrument
from app.services.cross_provider_identity_service import (
    CrossProviderIdentityService,
)
from app.services.token_facts_service import TokenFactsService


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
        token_facts: TokenFactsService | None = None,
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

        # A token's market facts, judged through the validation gate on
        # read. Stored doors throughout, so this adds no fetch.
        self._token_facts = token_facts or TokenFactsService()

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
            self._earnings(instrument.yahoo_symbol, asset_class),
        )

        quote = self._find_quote(
            quotes,
            item.symbol,
        )

        # `marketCap` means a network's total value for a token and a
        # company's equity value for a business. The same field, two
        # different claims, so which fields are read is decided by which
        # kind of thing this is.
        #
        # Two different decisions, split after they were found conflated:
        # whether the *company* fields are read is the capability boundary
        # (`has_no_company` — a fund is not asked company questions, so
        # its structural dividend of zero can never reach a quality
        # factor), while whether the *token-shaped* fields are read kept
        # its original membership exactly — a fund is not a token, and
        # must not read a `circulating_supply` out of a payload merely
        # because it is not a company either.
        has_company = not asset_class.has_no_company
        is_token = asset_class in (AssetClass.CRYPTO, AssetClass.COMMODITY)

        # A cryptocurrency's market facts come through the validation
        # gate, never straight off a provider response: Yahoo priced an
        # $18bn token at $8,105 without failing, and a value an API
        # returned is a claim until something corroborates it. Only what
        # the gate established is served; what it rejected is retained,
        # with reasons, where the dossier can show it.
        tokens = (
            self._token_facts.established(item.symbol, item.name, asset_class)
            if asset_class is AssetClass.CRYPTO
            else None
        )

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
            # For a token, the fundamentals are the judged token facts,
            # and they are dated by that reading — never by a generalist
            # response the gate may have rejected.
            fundamentals_reading=(
                tokens.read if tokens is not None else valuation.reading
            ),
            # The identity's own reading, carried from the watchlist fetch
            # that named this instrument. It ages on its own cadence, apart
            # from the quote and the fundamentals beside it.
            identity_reading=item.reading,
            # Market
            current_price=quote.price if quote is not None else None,
            daily_change_pct=(quote.change_percent if quote is not None else None),
            # The same move, carrying whether it was measured, under
            # which warrant, and over which session. Momentum reads
            # this; `daily_change_pct` above stays for every other
            # caller and is filled from the same quote, so the two
            # cannot disagree.
            daily_change=self._daily_change(quote),
            market_cap=(
                tokens.established_value("market_cap")
                if tokens is not None
                else valuation.market_cap
            ),
            # The same figure, carrying whether it may be placed against
            # an absolute threshold. The currency is left absent
            # deliberately: this platform reads none for a market
            # capitalisation, and inventing one here would be the
            # assumption the magnitude consumer exists to refuse.
            market_cap_magnitude=self._market_cap_magnitude(
                tokens.established_value("market_cap")
                if tokens is not None
                else valuation.market_cap,
                # The token path carries no denomination here: quality
                # never reads a token's magnitude (F1), and the crypto
                # gate owns its own facts. The company path carries what
                # acquisition established, which is None for every
                # record written before the boundary.
                valuation.market_cap_denomination if tokens is None else None,
                # Whose figure this is — the #134 join over the broker's
                # claim and the vendor claim stored at acquisition,
                # derived here on read so the join logic can evolve
                # without re-acquiring. A record that predates the
                # capture joins on the broker's claim alone and reads
                # honestly assumed.
                join_identity(
                    item.symbol,
                    (
                        CrossProviderIdentityService.from_broker(item),
                        *(
                            (valuation.vendor_identity,)
                            if valuation.vendor_identity is not None
                            else ()
                        ),
                    ),
                ),
            ),
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
            # balance-sheet fields below instead. For a cryptocurrency,
            # served from the gate's established facts only — a claim
            # that did not survive validation reads as absent here.
            circulating_supply=(
                tokens.established_value("circulating_supply")
                if tokens is not None
                else (valuation.circulating_supply if is_token else None)
            ),
            max_supply=(
                tokens.established_value("max_supply")
                if tokens is not None
                else (valuation.max_supply if is_token else None)
            ),
            # The generalist's broader volume concept, kept as exactly
            # that — tracked spot volume is a different measurement and
            # is never mapped onto it. Consumed only where the same
            # source's market-cap claim was independently corroborated:
            # a provider shown wrong about this instrument does not keep
            # its other claims' authority.
            volume_24h=(
                (valuation.volume_24h if tokens.yahoo_market_cap_corroborated else None)
                if tokens is not None
                else (valuation.volume_24h if is_token else None)
            ),
            # Never the provider's inception field for a cryptocurrency:
            # what it measures for a token was never established, and it
            # claimed six years of history for a token that began trading
            # in 2024 — which scored a favourable age point. Project age
            # is unknown until a source with established semantics
            # exists, and unknown is preferable to an invented fact.
            inception=(
                None
                if asset_class is AssetClass.CRYPTO
                else (valuation.inception if is_token else None)
            ),
            # What a fund has: the cost of owning the wrapper, read from
            # the same response whose company fields stay absent for it.
            # ETF-only rather than has-no-company: a token or a commodity
            # has no expense ratio, and a provider field under that name
            # would be a claim about something else.
            expense_ratio=(
                valuation.expense_ratio if asset_class is AssetClass.ETF else None
            ),
            # Valuation. A token has no earnings to be priced against, so
            # these stay absent however populated the response was.
            forward_pe=valuation.forward_pe if has_company else None,
            # Growth, profitability, balance sheet and cash generation, read
            # from the same call as the valuation above. A token has none of
            # these — it has the supply fields instead — so they are populated
            # for a company only, and stay absent rather than zero elsewhere.
            revenue_growth=valuation.revenue_growth if has_company else None,
            earnings_growth=valuation.earnings_growth if has_company else None,
            gross_margin=valuation.gross_margin if has_company else None,
            operating_margin=valuation.operating_margin if has_company else None,
            net_margin=valuation.net_margin if has_company else None,
            # Return on equity is reported; return on invested capital is not,
            # so it stays absent rather than being derived from figures the
            # provider did not give.
            roe=valuation.return_on_equity if has_company else None,
            roic=None,
            debt_to_equity=valuation.debt_to_equity if has_company else None,
            current_ratio=valuation.current_ratio if has_company else None,
            operating_cash_flow=(
                valuation.operating_cash_flow if has_company else None
            ),
            free_cash_flow=valuation.free_cash_flow if has_company else None,
            # Shareholder returns
            eps=valuation.eps if has_company else None,
            dividend_yield=valuation.dividend_yield if has_company else None,
            # Classification
            sector=valuation.sector if has_company else None,
            industry=valuation.industry if has_company else None,
        )

    @staticmethod
    def _market_cap_magnitude(
        amount: float | None,
        denomination: MarketCapDenomination | None = None,
        identity: CrossProviderIdentity | None = None,
    ) -> MarketCapMagnitude | None:
        """The market capitalisation, with what is established about it.

        Three crossings travel with the number, and they are carried
        apart because they fail apart. The registry's warrant for
        reading `marketCap` as this company's market capitalisation is
        ASSUMED — and where acquisition corroborated the figure against
        the payload's own price × shares identity, the reading is
        **checked against corroborating evidence**, which is precisely
        `TranslationWarrant.VALIDATED`'s meaning, and the denomination
        that check derived travels with it. Where nothing corroborated,
        both stay unestablished and the magnitude stays incomparable.
        The #134 identity rides beside them untouched: establishing a
        denomination says nothing about whose figure it is, and the
        magnitude's own conjunction is where that stays true.
        """

        if amount is None:
            return None

        translation = governed("ValuationSnapshot.market_cap")

        registry_warrant = (
            translation.warrant
            if translation is not None
            else TranslationWarrant.UNKNOWN
        )

        if denomination is not None and denomination.established:
            return MarketCapMagnitude.measured(
                amount,
                warrant=TranslationWarrant.VALIDATED,
                currency=denomination.currency,
                currency_is_assumed=False,
                identity=identity,
            )

        return MarketCapMagnitude.measured(
            amount,
            warrant=registry_warrant,
            currency=None,
            currency_is_assumed=True,
            identity=identity,
        )

    @staticmethod
    def _daily_change(quote: MarketQuote | None) -> DailyChange | None:
        """The quote's move, with what is established about it.

        Three facts are carried through rather than collapsed: whether
        anything was measured (the quote now says), the warrant the
        registry holds for this crossing, and which session the closes
        actually cover.

        The session is decided by comparing the last close's own date
        with the date the reading was taken — the only two dates in
        hand. No trading calendar is consulted: an equal pair
        establishes *today*, an earlier close establishes *the last
        session*, and a missing date on either side establishes
        neither.
        """

        if quote is None:
            return None

        translation = governed("MarketQuote.change_percent")

        warrant = (
            translation.warrant
            if translation is not None
            else TranslationWarrant.UNKNOWN
        )

        if quote.change_absence is not None:
            return DailyChange.unmeasured(quote.change_absence, warrant=warrant)

        read_on = (
            quote.reading.observed_at.date() if quote.reading is not None else None
        )

        if quote.session_date is None or read_on is None:
            basis = ChangeBasis.UNKNOWN_SESSION
        elif quote.session_date == read_on:
            basis = ChangeBasis.SAME_SESSION
        else:
            basis = ChangeBasis.LAST_AVAILABLE_SESSION

        return DailyChange.measured(
            quote.change_percent,
            warrant=warrant,
            basis=basis,
            session_date=quote.session_date,
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

        That key is the ticker Yahoo lists the company under, not the
        broker's — asking a provider with a symbol it does not carry can
        only ever come back empty, which for Nestlé looked exactly like a
        company that publishes no date.
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
