"""What moved, across the whole market rather than one index."""

from app.application.services.market_service import MarketService
from app.domain.market_breadth import MarketBreadth
from app.domain.market_snapshot import MarketSnapshot


class MarketBreadthService:
    """
    Classify each corner of the market the platform actually prices.

    The Brain's market view is a single mood: the average move of nine
    instruments, which nets a crypto rally against a bond sell-off and
    reports neither. This says which of them moved, so "markets are
    broadly neutral today" can be read for what it hides.

    Every group is named, including the ones nothing could price. A
    corner of the market this platform did not see is reported unknown
    rather than left out of a picture claiming to be whole.
    """

    #: A move smaller than this is not a direction, it is noise. The same
    #: line the market mood is drawn at, because a day that counts as
    #: positive for the market cannot count as flat for equities.
    POSITIVE_THRESHOLD = MarketService.POSITIVE_THRESHOLD
    NEGATIVE_THRESHOLD = MarketService.NEGATIVE_THRESHOLD

    def build(
        self,
        market: MarketSnapshot,
    ) -> MarketBreadth:
        return MarketBreadth(
            equities=self._group(market, "SPY", "QQQ", "IWM"),
            technology=self._group(market, "QQQ"),
            small_caps=self._group(market, "IWM"),
            crypto=self._group(market, "BTC", "ETH"),
            commodities=self._group(market, "GLD", "WTI"),
            # The band the VIX falls in, classified once, in the service
            # that owns what "high volatility" means here.
            volatility=MarketService.classify_volatility(market.vix),
            dollar=self._group(market, "DXY"),
            rates=self._group(market, "TNX"),
        )

    def _group(
        self,
        market: MarketSnapshot,
        *symbols: str,
    ) -> str:
        """
        Which way a group of instruments moved, or that nobody knows.

        Averaged over the instruments that were priced. One missing
        member weakens the reading; none priced makes it unknown, which
        is said rather than shown as flat.
        """

        changes = [
            quote.change_percent
            for quote in (market.quote(symbol) for symbol in symbols)
            if quote is not None
        ]

        if not changes:
            return "unknown"

        return self._classify(sum(changes) / len(changes))

    def _classify(
        self,
        change: float,
    ) -> str:
        if change >= self.POSITIVE_THRESHOLD:
            return "positive"

        if change <= self.NEGATIVE_THRESHOLD:
            return "negative"

        return "neutral"
