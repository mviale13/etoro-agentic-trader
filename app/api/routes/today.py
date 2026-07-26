from fastapi import APIRouter

from app.api.models.today import (
    HealthCheckResponse,
    HealthResponse,
    OpinionResponse,
    RecommendationResponse,
    TodayResponse,
)
from app.services.brief_service import BriefService

router = APIRouter(
    prefix="/api",
    tags=["Today"],
)


@router.get(
    "/today",
    response_model=TodayResponse,
    summary="Get today's MOVRvest Morning Brief",
)
async def get_today() -> TodayResponse:
    snapshot = await BriefService().build()

    return TodayResponse(
        greeting=snapshot.greeting,
        health=HealthResponse(
            score=snapshot.health.overall_score,
            checks=[
                HealthCheckResponse(
                    name=check.name,
                    score=check.score,
                    status=check.status,
                    message=check.message,
                )
                for check in snapshot.health.checks
            ],
        ),
        summary=snapshot.summary,
        changes=list(snapshot.changes),
        recommendation=RecommendationResponse(
            symbol=snapshot.recommendation.symbol,
            action=snapshot.recommendation.decision.recommendation,
            confidence=snapshot.recommendation.decision.confidence,
            opinions=[
                OpinionResponse(
                    member=opinion.member,
                    vote=opinion.vote,
                    confidence=opinion.confidence,
                    rationale=opinion.rationale,
                )
                for opinion in snapshot.recommendation.decision.opinions
            ],
        ),
        next_action=snapshot.next_action,
    )
