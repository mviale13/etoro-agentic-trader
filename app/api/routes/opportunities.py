from fastapi import APIRouter

from app.api.models.opportunity import OpportunityResponse
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/", response_model=list[OpportunityResponse])
def get_top_opportunities() -> list[OpportunityResponse]:
    opportunities = OpportunityService().top_opportunities()

    return [
        OpportunityResponse(
            company=o.company,
            action=o.action,
            confidence=o.confidence,
            summary=o.summary,
        )
        for o in opportunities
    ]
