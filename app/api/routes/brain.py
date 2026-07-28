from fastapi import APIRouter

from app.services.brain_service import BrainService
from app.services.fx_service import FXService

router = APIRouter(
    prefix="/brain",
    tags=["brain"],
)


@router.get("/")
async def get_brain() -> dict[str, object]:
    brain = await BrainService().build()

    fx = FXService().portfolio(
        brain.portfolio.total_value,
    )

    return {
        "summary": brain.summary,
        "portfolio": {
            "total_value": fx["total_value_usd"],
            "total_value_eur": fx["total_value_eur"],
            "positions": brain.portfolio.positions,
            "cash_allocation": brain.portfolio.allocation.cash,
        },
        "observation": {
            "title": brain.observation.title,
            "message": brain.observation.message,
        },
        "investor_dna": {
            "confidence": brain.investor_dna.confidence,
            "message": (
                "Learning your investment style..."
                if brain.investor_dna.confidence < 50
                else "Strong understanding of your investing style."
            ),
        },
        "recommendation": {
            "symbol": brain.recommendation.symbol,
            "action": brain.recommendation.decision.recommendation,
            "confidence": brain.recommendation.decision.confidence,
        },
    }
