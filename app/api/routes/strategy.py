from typing import Any

from fastapi import APIRouter

from app.services.investor_strategy_service import (
    InvestorStrategyService,
)

router = APIRouter(
    prefix="/strategy",
    tags=["strategy"],
)


@router.get("/readiness")
def get_strategy_readiness() -> dict[str, object]:
    return InvestorStrategyService().readiness()


@router.get("/")
def get_strategy() -> dict[str, Any]:
    return InvestorStrategyService().load()


@router.put("/")
def update_strategy(
    strategy: dict[str, Any],
) -> dict[str, Any]:
    return InvestorStrategyService().save(
        strategy,
    )
