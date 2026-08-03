"""What the platform can say about the market itself."""

from fastapi import APIRouter

from app.application.brain.perception.market_perception import MarketPerception
from app.domain.market_snapshot import MarketSnapshot
from app.services.market_breadth_service import MarketBreadthService

router = APIRouter(
    prefix="/market",
    tags=["market"],
)


def _payload(
    market: MarketSnapshot,
) -> dict[str, object]:
    """
    The snapshot and its breadth, as the page needs to read them.

    The mood and the breadth are served together on purpose. "Markets are
    broadly neutral today" is the average of nine instruments, and the
    breadth beside it is what that average netted out.
    """

    breadth = MarketBreadthService().build(market)

    return {
        "mood": market.market_mood,
        "summary": market.summary,
        "volatility": market.volatility,
        # The figure the band was decided by, not only the band.
        "vix": market.vix,
        "observed": market.reading.stated() if market.reading is not None else None,
        # Named by subject, never as "market sentiment". The only index
        # read here is a crypto one, and a page that drops the subject
        # invites the reader to apply it to everything they hold.
        "sentiment": (
            {
                "score": market.sentiment.score,
                "label": market.sentiment.label,
                "subject": market.sentiment.subject.value,
                "observed": market.sentiment.reading.stated(),
            }
            if market.sentiment is not None
            else None
        ),
        "breadth": {
            "equities": breadth.equities,
            "technology": breadth.technology,
            "small_caps": breadth.small_caps,
            "crypto": breadth.crypto,
            "commodities": breadth.commodities,
            "volatility": breadth.volatility,
            "dollar": breadth.dollar,
            "rates": breadth.rates,
        },
        "quotes": [
            {
                "symbol": quote.symbol,
                "name": quote.name,
                "price": quote.price,
                "change_percent": quote.change_percent,
                # Measured over a year of closes, or absent. Never zero:
                # a series too short to measure is not a calm one.
                "realized_volatility": quote.realized_volatility,
                "max_drawdown": quote.max_drawdown,
                "observed": (
                    quote.reading.stated() if quote.reading is not None else None
                ),
            }
            for quote in market.quotes
        ],
    }


@router.get("/")
async def get_market() -> dict[str, object]:
    """
    The current market snapshot, priced once and shared.

    Built by `MarketPerception`, which is the one place a market snapshot
    is assembled. This route used to assemble its own from the same three
    collaborators, so the page and the Brain read the market through two
    implementations of one concept — and only one of them would have
    gained anything added to the other.
    """

    return _payload(await MarketPerception().execute())
