"""Display quotes for the dossier heroes — read-only, never decisive.

`GET /quotes?symbols=DIS,HYPE` serves the Fresh Quote Ribbon. The
browser calls this backend and never a provider; the provider credential
lives in the backend's settings and appears in no response, no log line
this route writes, and no URL. A failure here is a failure of a display
ribbon: every fault is a typed per-symbol state, and nothing raises
past the route.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.config import Settings
from app.domain.fresh_quote import FreshQuote
from app.services.fresh_quote_service import FreshQuoteService

router = APIRouter(prefix="/quotes", tags=["quotes"])

#: How many symbols one request may ask for. The service fetches its
#: whole catalog per TTL regardless, so this bounds response size, not
#: provider load.
MAX_SYMBOLS = 20


class FreshQuoteResponse(BaseModel):
    movrvest_symbol: str
    asset_class: str
    provider: str
    provider_instrument_identity: str | None
    provider_label: str | None
    price: float | None
    currency: str | None
    bid: float | None
    ask: float | None
    source_as_of: str | None
    received_at: str | None
    clock_kind: str
    delay_status: str
    market_status: str
    status: str
    stated: str


class QuotesResponse(BaseModel):
    quotes: list[FreshQuoteResponse]


@lru_cache(maxsize=1)
def _service() -> FreshQuoteService:
    """One instance per process — the cache and its single-flight lock
    are only process-wide if the service is."""

    return FreshQuoteService(Settings())


def _response(quote: FreshQuote) -> FreshQuoteResponse:
    return FreshQuoteResponse(
        movrvest_symbol=quote.movrvest_symbol,
        asset_class=quote.asset_class.value,
        provider=quote.provider,
        provider_instrument_identity=quote.provider_instrument_identity,
        provider_label=quote.provider_label,
        price=quote.price,
        currency=quote.currency,
        bid=quote.bid,
        ask=quote.ask,
        source_as_of=(quote.source_as_of.isoformat() if quote.source_as_of else None),
        received_at=(quote.received_at.isoformat() if quote.received_at else None),
        clock_kind=quote.clock_kind.value,
        delay_status=quote.delay_status.value,
        market_status=quote.market_status.value,
        status=quote.status.value,
        stated=quote.stated,
    )


@router.get("", response_model=QuotesResponse)
async def quotes(
    symbols: str = Query(..., description="Comma-separated MOVRvest symbols"),
) -> QuotesResponse:
    asked = tuple(part.strip().upper() for part in symbols.split(",") if part.strip())[
        :MAX_SYMBOLS
    ]

    return QuotesResponse(
        quotes=[_response(quote) for quote in await _service().quotes(asked)],
    )
