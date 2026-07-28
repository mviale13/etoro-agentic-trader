from fastapi import APIRouter

from app.api.models.opportunity import OpportunityResponse
from app.services.opportunity_service import OpportunityService

router = APIRouter(
    prefix="/opportunities",
    tags=["opportunities"],
)


@router.get(
    "/",
    response_model=list[OpportunityResponse],
)
def get_top_opportunities() -> list[OpportunityResponse]:
    opportunities = OpportunityService().top_opportunities()

    return [
        OpportunityResponse(
            symbol=o.symbol,
            action=o.action,
            score=o.score,
            policy_fit=o.policy_fit,
            committee_confidence=o.committee_confidence,
            market_score=o.market_score,
            diversification_score=o.diversification_score,
            reason=o.reason,
        )
        for o in opportunities
    ]
