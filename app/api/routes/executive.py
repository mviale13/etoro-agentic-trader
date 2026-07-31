from fastapi import APIRouter

from app.api.models.executive_brief import (
    ExecutiveBriefResponse,
    ExecutivePriorityResponse,
    InvestmentCaseResponse,
)
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.executive import ExecutiveService
from app.renderers import ExecutiveBriefRenderer

router = APIRouter(
    prefix="/executive",
    tags=["executive"],
)


@router.get(
    "/{symbol}",
    response_model=ExecutiveBriefResponse,
)
async def executive_brief(
    symbol: str,
) -> ExecutiveBriefResponse:
    """
    Explain the Artificial CIO decision for one symbol.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    normalized_symbol = symbol.upper().strip()

    brain = await BrainBuilderService().build()

    brief = ExecutiveService().brief(
        symbol=normalized_symbol,
        brain=brain,
    )

    view = ExecutiveBriefRenderer().render(
        brief,
    )

    return ExecutiveBriefResponse(
        symbol=normalized_symbol,
        headline=view.headline,
        summary=view.summary,
        confidence=view.confidence,
        portfolio_health=view.portfolio_health,
        priorities=[
            ExecutivePriorityResponse(
                title=priority.title,
                description=priority.description,
                urgency=priority.urgency,
            )
            for priority in view.priorities
        ],
        investment_cases=[
            InvestmentCaseResponse(
                symbol=case.symbol,
                recommendation=case.recommendation,
                confidence=case.confidence,
                summary=case.summary,
            )
            for case in view.investment_cases
        ],
    )
