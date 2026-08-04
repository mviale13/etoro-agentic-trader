from fastapi import APIRouter

from app.api.models.portfolio_health import PortfolioHealthResponse
from app.services.portfolio_health_service import PortfolioHealthService

router = APIRouter(
    prefix="/portfolio-health",
    tags=["portfolio-health"],
)


@router.get("/", response_model=PortfolioHealthResponse)
def get_portfolio_health() -> PortfolioHealthResponse:
    health = PortfolioHealthService().build()

    return PortfolioHealthResponse(
        score=health.overall_score,
        summary=health.recommendation,
    )
