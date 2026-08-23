"""Personal Ticker News, served to the dossier that displays it.

The payload carries only what may be shown: **no sentiment reasoning**,
no provider request id, no authenticated URL, no `next_url`, and no raw
provider payload. Massive's own sentiment classification for the queried
ticker travels as a bare direction or as nothing at all, with its
disclosure beside it — the icon is a quotation, and the sentence naming
whose it is comes from the backend for the same reason every other
sentence does.

The wording travels with the data: the frontend prints this platform's
sentences and composes none of its own, which is the rule the crypto
dossier already follows.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.domain.personal_news import NewsOutcome
from app.services.personal_ticker_news_service import PersonalTickerNewsService

router = APIRouter(prefix="/personal-news", tags=["personal-news"])


@router.get("/{symbol}")
def get_personal_ticker_news(symbol: str) -> dict[str, Any]:
    """Recent articles Massive associates with this ticker.

    **Declared `def` rather than `async def`, and that is what this line
    is for.** One reading is three paced requests, and the pacing is a
    blocking sleep on a process-wide scheduler — around twenty-six
    seconds of it. On an `async def` path operation that runs *on the
    event loop* and stops the whole API for the duration. A synchronous
    path operation is handed to FastAPI's worker threadpool instead,
    where blocking is what the threads are for.

    The scheduler stays synchronous and stays shared. Making it `async`
    would pace one loop's callers and leave anything outside that loop
    free to burst, and a second scheduler would divide one allowance in
    two — which is the same defect twice, since the allowance belongs to
    the key.

    Never 404s and never raises: an unavailable feature, an unreadable
    provider and an unidentifiable issuer are all worded results,
    because a surface handed an error could only say *something went
    wrong* where this can say which of them happened.
    """

    result = PersonalTickerNewsService().news_for(symbol)

    return {
        "queried_ticker": result.queried_ticker,
        "outcome": result.outcome.value,
        "stated": result.stated,
        "coverage_notice": result.coverage_notice,
        "sentiment_notice": result.sentiment_notice,
        "retrieved_at": result.retrieved_at.isoformat(),
        "heading": "Ticker News",
        "explanation": (
            "The latest articles Massive associates with this ticker, at "
            "most three. These items have not been assessed or verified "
            "by MOVRvest."
        ),
        "displayable": result.outcome is NewsOutcome.DISPLAY_ONLY,
        "leads": [
            {
                "provider_article_id": lead.provider_article_id,
                "queried_ticker": lead.queried_ticker,
                "associated_tickers": list(lead.associated_tickers),
                "associated_ticker_count": lead.associated_ticker_count,
                "association_note": lead.stated_association(),
                "headline": lead.headline,
                "provider_summary": lead.provider_summary,
                "publisher_name": lead.publisher_name,
                "author": lead.author,
                "published_at": lead.published_at.isoformat(),
                "article_url": lead.article_url,
                # A direction or null. The provider's reasoning is not
                # here, and there is no field it could arrive through.
                "provider_sentiment": (
                    lead.provider_sentiment.value
                    if lead.provider_sentiment is not None
                    else None
                ),
                "sentiment_label": lead.stated_sentiment(),
                "status": lead.status.value,
            }
            for lead in result.leads
        ],
    }
