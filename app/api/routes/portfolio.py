from fastapi import APIRouter

from app.api.models.portfolio import (
    AllocationResponse,
    PortfolioResponse,
)
from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.services.account_service import AccountService
from app.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio() -> PortfolioResponse:
    settings = Settings()
    broker = EtoroAccountBroker(settings)

    account = await AccountService(broker).snapshot()
    portfolio = PortfolioService().analyze(account)

    return PortfolioResponse(
        total_value=portfolio.total_value,
        positions=portfolio.positions,
        allocation=AllocationResponse(
            cash=portfolio.allocation.cash,
            stocks=portfolio.allocation.stocks,
            etfs=portfolio.allocation.etfs,
            crypto=portfolio.allocation.crypto,
            unclassified=portfolio.allocation.unclassified,
        ),
        risk_flags=list(portfolio.risk_flags),
    )
