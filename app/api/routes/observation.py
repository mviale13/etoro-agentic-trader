from fastapi import APIRouter

from app.api.models.observation import ObservationResponse
from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.services.account_service import AccountService
from app.services.investor_observation_service import (
    InvestorObservationService,
)
from app.services.portfolio_service import PortfolioService
from app.services.signal_service import SignalService

router = APIRouter(
    prefix="/observation",
    tags=["observation"],
)


@router.get("/", response_model=ObservationResponse)
async def get_observation() -> ObservationResponse:
    settings = Settings()
    broker = EtoroAccountBroker(settings)

    account = await AccountService(broker).snapshot()
    portfolio = PortfolioService().analyze(account)

    signals = SignalService().analyze(
        current=portfolio,
        previous=None,
    )
    observation = InvestorObservationService().observe(signals)

    return ObservationResponse(
        title=observation.title,
        message=observation.message,
        category=observation.category,
    )
