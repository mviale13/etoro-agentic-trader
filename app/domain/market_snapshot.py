import math
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.market_sensitivity import MarketSensitivity
from app.domain.provenance import Provenance
from app.domain.provider_claim import ClaimAbsence
from app.domain.sentiment_snapshot import SentimentSnapshot

#: A day at least this many times the instrument's own typical day is
#: reported as unusual. Two typical days' worth of movement in one day is
#: the same statement about an index fund and about Bitcoin, which is the
#: point: raw percentages are not.
UNUSUAL_MOVE_RATIO = 2.0

#: Trading days in a year, for de-annualising realized volatility.
TRADING_DAYS = 252


@dataclass(frozen=True, slots=True)
class MarketQuote:
    symbol: str
    name: str
    price: float
    change_percent: float
    currency: str = "USD"

    #: Why `change_percent` carries no measurement, where it does not.
    #:
    #: The legacy type is the defect and this field is its disclosure.
    #: `change_percent` is a bare `float`, so it has no way to say
    #: *unmeasured* — and the adapter, needing a number, writes 0.0
    #: when a history is too short to compare or a stored reading
    #: cannot be read back. Downstream that zero reads as "the
    #: security did not move today" at confidence 60, where an honest
    #: absence would read UNKNOWN at 20.
    #:
    #: Nothing consumes this yet, deliberately: widening the type is a
    #: consumer-facing change and this slice moves no decision. What it
    #: does is make the substitution *visible* — a quote can now be
    #: asked whether its zero was observed, and the answer is no
    #: longer indistinguishable from a real flat day.
    change_absence: "ClaimAbsence | None" = None

    #: The date of the last close this quote was read from, where the
    #: provider's series carried one.
    #:
    #: #133 measured that this was available and discarded: the adapter
    #: read the closing series for alignment and stamped the quote with
    #: the moment MOVRvest asked. A Friday close served on a Sunday was
    #: then described as today's move. Kept for the momentum path,
    #: which is the one place a sentence names a period; nothing else
    #: reads it, and no trading calendar is consulted anywhere.
    session_date: "date | None" = None

    #: Whether `currency` is the provider's own word or this platform's
    #: assumption. Every Yahoo quote is the latter: the adapter writes
    #: "USD" for every instrument, so BP.L's price in pence and a New
    #: York close wear the same label. Recorded rather than repaired —
    #: converting by an assumed currency is the 100× error this flag
    #: exists to stop somebody making.
    currency_is_assumed: bool = False

    #: Annualised standard deviation of daily returns, as a ratio (0.28 is
    #: 28%). None when the series was too short to measure it.
    realized_volatility: float | None = None

    #: Deepest peak-to-trough fall over the observed window, as a positive
    #: ratio (0.34 is a 34% fall). None when unmeasured.
    max_drawdown: float | None = None

    #: How much this security moves with the market, measured against a
    #: benchmark from the same price history the two figures above are read
    #: off. None when the window was too short, or the benchmark could not
    #: be read to measure against. An asset-class label is not this.
    market_sensitivity: MarketSensitivity | None = None

    #: When this price was read, and from where.
    #:
    #: A quote replayed from cache keeps the time it was actually taken. A
    #: price is a claim about now, and without this a fifteen-minute-old
    #: one was indistinguishable from a live one to everything downstream.
    reading: Provenance | None = None

    @property
    def change_is_measured(self) -> bool:
        """Whether `change_percent` is an observation at all.

        The question no consumer could ask before: a zero written
        because the security did not move and a zero written because
        nothing could be computed are the same float, and only this
        answers which one is in hand.
        """

        return self.change_absence is None

    @property
    def typical_daily_move_pct(self) -> float | None:
        """
        The size of this instrument's ordinary day, in percent.

        De-annualised from its own measured volatility. None where the
        volatility is unmeasured — an instrument whose history nobody
        could read does not have a known ordinary day.
        """

        if self.realized_volatility is None or self.realized_volatility <= 0:
            return None

        return self.realized_volatility / math.sqrt(TRADING_DAYS) * 100

    @property
    def move_ratio(self) -> float | None:
        """
        Today's move as a multiple of this instrument's typical day.

        The comparison raw percentages cannot make: a 2% day is routine
        for Bitcoin and remarkable for a bond index, and only the
        instrument's own history can say which.
        """

        typical = self.typical_daily_move_pct

        if typical is None:
            return None

        return abs(self.change_percent) / typical

    @property
    def moved_unusually(self) -> bool | None:
        """
        Whether today was at least twice this instrument's typical day.

        None where the typical day is unmeasured: unknown is not calm.
        """

        ratio = self.move_ratio

        if ratio is None:
            return None

        return ratio >= UNUSUAL_MOVE_RATIO


@dataclass(frozen=True, slots=True)
class MarketData:
    quotes: tuple[MarketQuote, ...]
    vix: float | None


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    quotes: tuple[MarketQuote, ...]
    market_mood: str
    volatility: str
    summary: str
    timestamp: datetime

    #: What the VIX actually read, beside the band it falls in.
    #:
    #: The number was fetched, classified into "low", "medium" or "high"
    #: and then dropped. An adjective cannot be compared with yesterday's
    #: adjective, and a reader who wants to know how frightened the market
    #: is deserves the figure that decided the word.
    vix: float | None = None

    #: Where these quotes came from and when, taken from the least
    #: reliable of them. Nothing could date the market snapshot before:
    #: its `timestamp` is when this object was assembled, which is not
    #: when anything in it was observed.
    reading: Provenance | None = None

    #: How the market feels, where anything publishes a reading of it.
    #:
    #: One reading, of crypto. It names its own subject, because the Brain
    #: holding it must not let it describe an asset class it was never
    #: taken of. None when the index could not be read.
    sentiment: SentimentSnapshot | None = None

    def quote(self, symbol: str) -> MarketQuote | None:
        normalized = symbol.upper().strip()

        for item in self.quotes:
            if item.symbol.upper() == normalized:
                return item

        return None
