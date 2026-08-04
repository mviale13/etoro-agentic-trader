from fastapi import APIRouter, Depends

from app.api.dependencies import get_account_service
from app.api.models.portfolio import (
    AllocationResponse,
    PortfolioResponse,
)
from app.services.account_service import AccountService
from app.services.portfolio_service import PortfolioService

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)


@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    account_service: AccountService = Depends(get_account_service),
) -> PortfolioResponse:
    account = await account_service.snapshot()
    portfolio = PortfolioService().analyze(account)

    return PortfolioResponse(
        total_value=portfolio.total_value,
        total_value_eur=portfolio.total_value_eur,
        available_cash_usd=portfolio.available_cash_usd,
        available_cash_eur=portfolio.available_cash_eur,
        invested_usd=portfolio.invested_usd,
        invested_eur=portfolio.invested_eur,
        liquidity_pct=portfolio.liquidity_pct,
        positions=portfolio.positions,
        allocation=AllocationResponse(
            cash=portfolio.allocation.cash,
            stocks=portfolio.allocation.stocks,
            etfs=portfolio.allocation.etfs,
            crypto=portfolio.allocation.crypto,
            unclassified=portfolio.allocation.unclassified,
        ),
        risk_flags=list(portfolio.risk_flags),
        last_sync=portfolio.last_sync,
        source=f"{account.broker} {account.mode.title()}",
    )
