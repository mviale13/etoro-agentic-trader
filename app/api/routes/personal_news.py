"""Personal Ticker News, served to the dossier that displays it.

The payload carries only what may be shown: no provider sentiment, no
sentiment reasoning, no provider request id, no authenticated URL, no
`next_url`, and no raw provider payload. The wording travels with the
data — the frontend prints this platform's sentences and composes none
of its own, which is the same rule the crypto dossier follows.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.domain.personal_news import NewsOutcome
from app.services.personal_ticker_news_service import PersonalTickerNewsService

router = APIRouter(prefix="/personal-news", tags=["personal-news"])


@router.get("/{symbol}")
async def get_personal_ticker_news(symbol: str) -> dict[str, Any]:
    """Recent articles Massive associates with this ticker.

    Never 404s and never raises: an unavailable feature, an unreadable
    provider and an unidentifiable issuer are all worded results, because
    a surface that got an error could only say *something went wrong*
    where this can say which of them happened.
    """

    result = PersonalTickerNewsService().news_for(symbol)

    return {
        "queried_ticker": result.queried_ticker,
        "outcome": result.outcome.value,
        "stated": result.stated,
        "coverage_notice": result.coverage_notice,
        "retrieved_at": result.retrieved_at.isoformat(),
        "heading": "Ticker News",
        "explanation": (
            "Recent articles Massive associates with this ticker. These "
            "items have not been assessed or verified by MOVRvest."
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
                "status": lead.status.value,
            }
            for lead in result.leads
        ],
    }
