"""A genuinely fresh, display-only market quote — and nothing more.

The Fresh Quote Ribbon exists because a 22-hour-old established price
may remain historical evidence and must not be the headline market
price. This object is the whole contract of that display: what the
provider stated, when it stated it, when this platform received it, and
what may honestly be said about the gap between those clocks.

Three boundaries, each structural rather than aspirational:

- **display-only.** Nothing here reaches a decision, an envelope, a
  score, the evidence store, the cycle journal or the knowledge layer.
  The CIO's review used the prices its cycle recorded, and a fresh
  display quote never implies otherwise.
- **unknown stays unknown.** Stage 0 measured the provider's rates
  route: it states a per-instrument clock and states neither a currency
  name, a delay classification nor a market status. So `currency` is
  None rather than inferred from a conversion rate, and the two
  classifications carry UNKNOWN unless a provider some day states them.
- **a receipt time is never a market observation time.** `received_at`
  is this platform's clock; `source_as_of` is the provider's own, and
  `clock_kind` says which of the two the freshness claim rests on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class AssetClass(Enum):
    SECURITY = "security"
    CRYPTO = "crypto"


class ClockKind(Enum):
    """Whose clock the freshness claim rests on."""

    #: The provider stated an observation time of its own.
    SOURCE_STATED = "source_stated"

    #: Only this platform's receipt time exists. A quote on this clock
    #: is never marked CURRENT: recency of receipt is not recency of
    #: observation.
    RECEIPT_ONLY = "receipt_only"


class DelayStatus(Enum):
    REAL_TIME = "real_time"
    DELAYED = "delayed"
    UNKNOWN = "unknown"


class MarketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class QuoteStatus(Enum):
    #: The source's own clock puts the quote inside the currency window.
    CURRENT = "current"

    #: Held, but its source clock has aged past the window — or only a
    #: receipt clock exists, which can never establish currency.
    STALE = "stale"

    #: This platform holds no provider identity for the symbol, so no
    #: quote was asked for. A statement about this platform's catalog,
    #: never about the asset.
    IDENTITY_REFUSED = "identity_refused"

    #: Asked for and not answered — the provider omitted the row, the
    #: request failed, or the answer did not parse.
    UNAVAILABLE = "unavailable"


#: How old a source-stated quote may be and still be called current.
#: The acceptance bound: a headline quote is no more than two minutes
#: old when marked current. One rule for every asset class — a stock's
#: staleness is not more forgivable than a token's.
CURRENT_WINDOW = timedelta(seconds=120)


@dataclass(frozen=True, slots=True)
class FreshQuote:
    """One symbol's display quote, with both clocks and its own sentence."""

    movrvest_symbol: str
    asset_class: AssetClass
    provider: str

    #: The provider's stable identity for the instrument — eToro's
    #: numeric instrumentId, carried as text so no arithmetic is ever
    #: performed on an identifier. None where identity was refused.
    provider_instrument_identity: str | None

    #: The provider's own display name for the instrument ("Walt
    #: Disney", "Hyperliquid"). A label, not an identity claim.
    provider_label: str | None

    #: The traded price the provider reported (`lastExecution`).
    price: float | None
    #: Never inferred. Stage 0: the rates route names no currency —
    #: a conversion rate of 1.16725 shows the native quote is not the
    #: account's currency and still does not say what it is.
    currency: str | None
    bid: float | None
    ask: float | None

    #: The provider's own clock for this instrument, tz-aware.
    source_as_of: datetime | None
    #: This platform's clock, stamped at receipt. Always present on an
    #: answered quote; never a substitute for the source's.
    received_at: datetime | None

    clock_kind: ClockKind
    delay_status: DelayStatus
    market_status: MarketStatus
    status: QuoteStatus

    #: The one sentence a surface may print about this quote's standing,
    #: worded here so no page invents a stronger claim.
    stated: str

    @staticmethod
    def status_of(
        source_as_of: datetime | None,
        received_at: datetime,
        clock_kind: ClockKind,
    ) -> QuoteStatus:
        """CURRENT only on the source's own clock, inside the window.

        A receipt-only quote is STALE by construction: this platform
        knowing when it *received* a number establishes nothing about
        when the market produced it.
        """

        if clock_kind is not ClockKind.SOURCE_STATED or source_as_of is None:
            return QuoteStatus.STALE

        if received_at - source_as_of <= CURRENT_WINDOW:
            return QuoteStatus.CURRENT

        return QuoteStatus.STALE

    @classmethod
    def identity_refused(
        cls, symbol: str, asset_class: AssetClass, provider: str
    ) -> FreshQuote:
        return cls(
            movrvest_symbol=symbol,
            asset_class=asset_class,
            provider=provider,
            provider_instrument_identity=None,
            provider_label=None,
            price=None,
            currency=None,
            bid=None,
            ask=None,
            source_as_of=None,
            received_at=None,
            clock_kind=ClockKind.RECEIPT_ONLY,
            delay_status=DelayStatus.UNKNOWN,
            market_status=MarketStatus.UNKNOWN,
            status=QuoteStatus.IDENTITY_REFUSED,
            stated=(
                f"No provider identity is established for {symbol} in this "
                "platform's stored broker catalog, so no quote was requested."
            ),
        )

    @classmethod
    def unavailable(
        cls,
        symbol: str,
        asset_class: AssetClass,
        provider: str,
        identity: str | None,
        label: str | None,
        because: str,
    ) -> FreshQuote:
        return cls(
            movrvest_symbol=symbol,
            asset_class=asset_class,
            provider=provider,
            provider_instrument_identity=identity,
            provider_label=label,
            price=None,
            currency=None,
            bid=None,
            ask=None,
            source_as_of=None,
            received_at=datetime.now(UTC),
            clock_kind=ClockKind.RECEIPT_ONLY,
            delay_status=DelayStatus.UNKNOWN,
            market_status=MarketStatus.UNKNOWN,
            status=QuoteStatus.UNAVAILABLE,
            stated=because,
        )

    @classmethod
    def answered(
        cls,
        *,
        symbol: str,
        asset_class: AssetClass,
        provider: str,
        identity: str,
        label: str | None,
        price: float | None,
        bid: float | None,
        ask: float | None,
        source_as_of: datetime | None,
        received_at: datetime,
    ) -> FreshQuote:
        clock = (
            ClockKind.SOURCE_STATED
            if source_as_of is not None
            else ClockKind.RECEIPT_ONLY
        )
        status = cls.status_of(source_as_of, received_at, clock)

        if status is QuoteStatus.CURRENT:
            stated = f"As {provider} stated it, on the source's own clock."
        elif clock is ClockKind.SOURCE_STATED:
            stated = (
                f"{provider}'s own clock for this quote has aged past the "
                "two-minute window this platform calls current."
            )
        else:
            stated = (
                f"{provider} stated no observation time for this quote; only "
                "this platform's receipt time exists, which cannot establish "
                "currency."
            )

        return cls(
            movrvest_symbol=symbol,
            asset_class=asset_class,
            provider=provider,
            provider_instrument_identity=identity,
            provider_label=label,
            price=price,
            currency=None,
            bid=bid,
            ask=ask,
            source_as_of=source_as_of,
            received_at=received_at,
            clock_kind=clock,
            delay_status=DelayStatus.UNKNOWN,
            market_status=MarketStatus.UNKNOWN,
            status=status,
            stated=stated,
        )
