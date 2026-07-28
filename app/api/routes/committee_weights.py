from fastapi import APIRouter

from app.api.models.committee_weights import (
    CommitteeWeightsResponse,
)
from app.domain.market_regime import MarketRegimeType
from app.repositories.json_event_repository import (
    JsonEventRepository,
)
from app.services.regime_weight_service import (
    RegimeWeightService,
)

router = APIRouter(
    prefix="/committee",
    tags=["committee"],
)


@router.get(
    "/weights",
    response_model=CommitteeWeightsResponse,
)
async def weights() -> CommitteeWeightsResponse:
    regime = MarketRegimeType.BULL

    return CommitteeWeightsResponse(
        regime=regime.value,
        weights=RegimeWeightService(
            JsonEventRepository(),
        ).weights(regime),
    )
