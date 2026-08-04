from fastapi import APIRouter

from app.api.models.explanation import ExplanationResponse
from app.services.explanation_service import ExplanationService

router = APIRouter(prefix="/explain", tags=["explain"])


@router.get("", response_model=ExplanationResponse)
def get_explanation() -> ExplanationResponse:
    explanation = ExplanationService().build()

    return ExplanationResponse(
        recommendation=explanation.recommendation,
        confidence=explanation.confidence,
        reasons=list(explanation.reasons),
    )
