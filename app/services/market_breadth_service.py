from app.domain.market_breadth import (
    MarketBreadth,
)
from app.domain.market_facts import MarketFacts


class MarketBreadthService:
    POSITIVE_THRESHOLD = 0.25
    NEGATIVE_THRESHOLD = -0.25

    def build(
        self,
        facts: MarketFacts,
    ) -> MarketBreadth:
        spy = self._change(
            facts,
            "SPY",
        )
        qqq = self._change(
            facts,
            "QQQ",
        )
        iwm = self._change(
            facts,
            "IWM",
        )
        btc = self._change(
            facts,
            "BTC",
        )
        eth = self._change(
            facts,
            "ETH",
        )
        gold = self._change(
            facts,
            "GLD",
        )
        oil = self._change(
            facts,
            "WTI",
        )
        dollar = self._change(
            facts,
            "DXY",
        )
        rates = self._change(
            facts,
            "TNX",
        )

        return MarketBreadth(
            equities=self._classify_group(
                (
                    spy,
                    qqq,
                    iwm,
                )
            ),
            technology=self._classify_change(qqq),
            small_caps=self._classify_change(iwm),
            crypto=self._classify_group(
                (
                    btc,
                    eth,
                )
            ),
            commodities=self._classify_group(
                (
                    gold,
                    oil,
                )
            ),
            volatility=self._classify_vix(facts.vix),
            dollar=self._classify_change(dollar),
            rates=self._classify_change(rates),
        )

    def _change(
        self,
        facts: MarketFacts,
        symbol: str,
    ) -> float | None:
        quote = facts.quote(symbol)

        if quote is None:
            return None

        return quote.change_percent

    def _classify_group(
        self,
        changes: tuple[
            float | None,
            ...,
        ],
    ) -> str:
        available = [change for change in changes if change is not None]

        if not available:
            return "unknown"

        average = sum(available) / len(available)

        return self._classify_change(average)

    def _classify_change(
        self,
        change: float | None,
    ) -> str:
        if change is None:
            return "unknown"

        if change >= self.POSITIVE_THRESHOLD:
            return "positive"

        if change <= self.NEGATIVE_THRESHOLD:
            return "negative"

        return "neutral"

    @staticmethod
    def _classify_vix(
        vix: float | None,
    ) -> str:
        if vix is None:
            return "unknown"

        if vix < 15:
            return "low"

        if vix <= 25:
            return "medium"

        return "high"
