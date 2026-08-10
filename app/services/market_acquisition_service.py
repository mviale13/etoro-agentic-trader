"""Read the market once, for everything the pages will be asked about."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from app.domain.asset_class import AssetClass
from app.domain.exchange_rate import ExchangeRate
from app.domain.market_acquisition import (
    AcquiredSecurity,
    MarketAcquisition,
    MarketCycle,
)
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.protocol_entities import entities_for
from app.domain.research_candidate import ResearchCandidate
from app.domain.watchlist_item import WatchlistItem
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.coingecko_facts_provider import CachedCoinGeckoFactsProvider
from app.providers.coingecko_market_provider import CachedCoinGeckoMarketProvider
from app.providers.defillama_provider import CachedDefiLlamaProvider
from app.providers.earnings_provider import CachedEarningsProvider
from app.providers.exchange_rate_provider import CachedExchangeRateProvider
from app.providers.token_facts_provider import CachedTokenFactsProvider
from app.providers.token_insight_provider import CachedTokenInsightProvider
from app.providers.yahoo_market_provider import YahooInstrument, YahooMarketProvider
from app.services.crypto_market_service import acquisition_targets
from app.services.instrument_symbol_resolver import InstrumentSymbolResolver

#: How many watched-but-unheld securities one cycle prices.
#:
#: The research page's own default, deliberately the same number. A cycle
#: that acquired fewer would leave the page it exists to serve looking at
#: securities with no price; one that acquired every watchlist would spend
#: a rate limit on securities no surface asks about.
DEFAULT_CANDIDATE_BUDGET = 12


class MarketAcquisitionService:
    """
    The explicit act that fills the store the surfaces read from.

    Every page on this platform serves what has already been acquired and
    stops — the rule the knowledge layer follows for filings, applied to
    the provider half. This is the other side of that rule: the one place
    that reaches a provider on purpose.

    It asks for the whole book in a single batch, which is not an
    optimisation but the difference between two behaviours. Sensitivity is
    measured against one benchmark, and the provider reads that benchmark
    once per batch — so a page asking security by security downloaded a
    year of `SPY` closes thirteen times for one dossier, and this asks for
    it once.
    """

    def __init__(
        self,
        portfolio: Any | None = None,
        opportunities: Any | None = None,
        resolver: Any | None = None,
        quotes: Any | None = None,
        valuations: Any | None = None,
        calendars: Any | None = None,
        rates: Any | None = None,
        ratings: Any | None = None,
        token_facts: Any | None = None,
        coingecko_facts: Any | None = None,
        protocol_facts: Any | None = None,
        crypto_market: Any | None = None,
    ) -> None:
        # Imported where they are used: the perceptions reach the broker
        # stack, which reaches the providers this module imports.
        if portfolio is None:
            from app.application.brain.perception.portfolio_perception import (
                PortfolioPerception,
            )

            portfolio = PortfolioPerception()

        if opportunities is None:
            from app.application.brain.perception.opportunity_perception import (
                OpportunityPerception,
            )

            opportunities = OpportunityPerception()

        self._portfolio = portfolio
        self._opportunities = opportunities
        self._resolver = resolver or InstrumentSymbolResolver()

        # The acquiring doors, named here and nowhere a surface can reach.
        self._quotes = quotes or CachedMarketProvider()
        self._valuations = valuations or CachedValueProvider()
        self._calendars = calendars or CachedEarningsProvider()

        # The account is reported in dollars and read in euros, so the
        # rate is one more thing a page must find already read rather
        # than go and fetch.
        self._rates = rates or CachedExchangeRateProvider()

        # A third party's published crypto rating. Read here so a page
        # never spends a metered credit, exactly as with everything else.
        self._ratings = ratings or CachedTokenInsightProvider()

        # The factual market claims for a token — separate streams from
        # the rating, acquired here and judged by the validation gate
        # when read. Two independent claimants, because agreement
        # inside one provider is not corroboration. A page never
        # fetches any of them.
        self._token_facts = token_facts or CachedTokenFactsProvider()
        self._coingecko_facts = coingecko_facts or CachedCoinGeckoFactsProvider()

        # The economics of the systems behind the tokens — a separate
        # evidence family, read per mapped entity rather than per
        # security, because a security is not a protocol.
        self._protocol_facts = protocol_facts or CachedDefiLlamaProvider()

        # The crypto environment every token trades inside — read once
        # per cycle rather than once per security, because it is the
        # same market for all of them. Its own evidence family: nothing
        # here reaches token facts or protocol facts.
        self._crypto_market = crypto_market or CachedCoinGeckoMarketProvider()

    async def acquire(
        self,
        candidate_budget: int = DEFAULT_CANDIDATE_BUDGET,
    ) -> MarketAcquisition:
        """Read the market for the book, its candidates and the strip."""

        portfolio = await self._portfolio.execute()
        candidates = await self._opportunities.execute(portfolio)

        targets = await self._targets(portfolio, candidates, candidate_budget)

        # One batch for everything, the market strip included, so the
        # benchmark is downloaded once for the cycle rather than once per
        # security. The strip's instruments are already deduplicated
        # against the book's by yahoo symbol above.
        instruments = tuple(instrument for instrument, _ in targets)

        try:
            quotes = await self._quotes.quotes(instruments)
        except Exception:
            # The whole batch failed. Every security is reported unpriced,
            # which is what the pages will show, and the cycle still
            # reports rather than raising at an operator.
            quotes = ()

        priced = {quote.symbol.upper().strip() for quote in quotes}

        securities = await asyncio.gather(
            *(
                asyncio.to_thread(self._company, instrument, asset_class, priced)
                for instrument, asset_class in targets
                if asset_class is not None
            )
        )

        return MarketAcquisition(
            securities=tuple(securities),
            instruments=tuple(
                instrument.movrvest_symbol
                for instrument in YahooMarketProvider.DEFAULT_INSTRUMENTS
                if instrument.movrvest_symbol.upper().strip() in priced
            ),
            vix=await self._quotes.vix(),
            rate=await asyncio.to_thread(self._read_rate),
            crypto_market=await asyncio.to_thread(self._read_crypto_market),
        )

    def _read_crypto_market(self) -> MarketCycle | None:
        """One reading of the crypto environment, paced against the limit.

        Deterministic: the same calls in the same order every cycle, and
        a partial answer is stored as a partial answer. A page view never
        reaches this — it opens the stored door and stops.
        """

        coin_ids, category_keys = acquisition_targets()

        # /global, /coins/categories, the corpus's returns, the breadth
        # page, and one page per peer group in use.
        asked = 4 + len(category_keys)

        try:
            claims = self._crypto_market.claims(coin_ids, category_keys)
        except Exception:
            return MarketCycle(asked=asked, answered=0, peer_groups=category_keys)

        if claims is None:
            return MarketCycle(asked=asked, answered=0, peer_groups=category_keys)

        answered = sum(
            (
                claims.state is not None,
                bool(claims.categories),
                bool(claims.assets),
                claims.universe is not None,
            )
        ) + len(claims.category_universes)

        return MarketCycle(
            asked=asked,
            answered=answered,
            peer_groups=category_keys,
        )

    def _read_rate(self) -> ExchangeRate | None:
        """The currency rate the portfolio's euro figures are converted at."""

        try:
            return self._rates.usd_to_eur()
        except Exception:
            return None

    def _company(
        self,
        instrument: YahooInstrument,
        asset_class: AssetClass,
        priced: set[str],
    ) -> AcquiredSecurity:
        """
        Everything one security is asked for, in the order it is read.

        Both fundamentals and the calendar are read under the resolved
        ticker, because that is how the pages ask for them — a cycle that
        filled either under a different key would fill a store nothing
        reads from. The calendar used the broker's symbol until the
        readers moved to the provider's, which left Nestlé's cycle
        warming a key no page would ever look at.
        """

        return AcquiredSecurity(
            symbol=instrument.movrvest_symbol,
            priced=instrument.movrvest_symbol.upper().strip() in priced,
            fundamentals=self._fundamentals(instrument.yahoo_symbol),
            calendar=(
                self._calendar(instrument.yahoo_symbol)
                if asset_class is AssetClass.STOCK
                else None
            ),
            rating=(
                self._rating(instrument.movrvest_symbol)
                if asset_class is AssetClass.CRYPTO
                else None
            ),
            token_facts=(
                self._facts(instrument.movrvest_symbol)
                if asset_class is AssetClass.CRYPTO
                else None
            ),
            protocol_facts=(
                self._protocols(instrument.movrvest_symbol)
                if asset_class is AssetClass.CRYPTO
                else None
            ),
        )

    def _rating(self, symbol: str) -> bool:
        """Whether the store now holds a published rating for this token."""

        try:
            return self._ratings.rating(symbol) is not None
        except Exception:
            return False

    def _facts(self, symbol: str) -> bool:
        """Whether the stores now hold the token's market claims.

        Both claimants are asked; the report is the crypto-native
        store's, and a corroborator that could not be read leaves an
        honest single-claimant pool rather than failing the cycle.
        """

        try:
            self._coingecko_facts.claims(symbol)
        except Exception:
            pass

        try:
            return self._token_facts.claims(symbol) is not None
        except Exception:
            return False

    def _protocols(self, symbol: str) -> bool | None:
        """Whether the store now holds the economics behind this token.

        None where no economic system is mapped to the security — an
        unmapped token is not a token with nothing to read, and the two
        must not report the same word.
        """

        entities = entities_for(symbol)

        if not entities:
            return None

        read = False

        for entity in entities:
            try:
                read = self._protocol_facts.claims(entity.key) is not None or read
            except Exception:
                continue

        return read

    def _fundamentals(self, yahoo_symbol: str) -> bool:
        try:
            return self._valuations.snapshot(yahoo_symbol).reading is not None
        except Exception:
            return False

    def _calendar(self, symbol: str) -> bool:
        try:
            self._calendars.read(symbol)
        except Exception:
            return False

        return True

    async def _targets(
        self,
        portfolio: PortfolioSnapshot,
        candidates: Sequence[ResearchCandidate],
        candidate_budget: int,
    ) -> tuple[tuple[YahooInstrument, AssetClass | None], ...]:
        """
        Everything this cycle will ask a provider about, once each.

        Exactly what the Brain perceives — every holding, the candidates
        the research page can afford, and the instruments the market strip
        is made of. Acquiring anything else would fill the store with
        securities no surface reads, and acquiring less would leave a
        surface reading a security the store has nothing for.
        """

        items = await self._resolver.items_for(
            tuple(holding.instrument_id for holding in portfolio.holdings)
        )

        targets: dict[str, tuple[YahooInstrument, AssetClass | None]] = {}

        def add(item: WatchlistItem) -> None:
            asset_class = AssetClass.from_etoro(item.asset_type_id)

            instrument = YahooInstrument.for_security(
                item.symbol,
                item.name,
                asset_class,
            )

            targets.setdefault(instrument.yahoo_symbol, (instrument, asset_class))

        for holding in portfolio.holdings:
            item = items.get(holding.instrument_id)

            if holding.is_resolved and item is not None:
                add(item)

        watched = 0

        for candidate in candidates:
            if watched >= candidate_budget:
                break

            item = items.get(candidate.instrument_id)

            if item is not None:
                add(item)
                watched += 1

        # The strip last, so a holding that is also an index keeps the
        # asset class the book knows it by rather than the strip's.
        for instrument in YahooMarketProvider.DEFAULT_INSTRUMENTS:
            targets.setdefault(instrument.yahoo_symbol, (instrument, None))

        return tuple(targets.values())
