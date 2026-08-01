from fastapi import APIRouter, HTTPException

from app.api.models.executive_brief import (
    ExecutiveBriefResponse,
    ExecutivePriorityResponse,
    InvestmentCaseResponse,
)
from app.api.models.portfolio_briefing import (
    PortfolioBriefingResponse,
    RankedInvestmentCaseResponse,
)
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.executive.executive_service import ExecutiveService
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.renderers import ExecutiveBriefRenderer

router = APIRouter(
    prefix="/executive",
    tags=["executive"],
)


def _committee_agreement(
    workspace: ExecutiveWorkspace,
) -> int:
    """Mean committee confidence, as a whole percentage."""

    opinions = workspace.committee_opinions

    if not opinions:
        return 0

    mean = sum(opinion.confidence for opinion in opinions) / len(opinions)

    return max(0, min(100, round(mean * 100)))


@router.get(
    "/portfolio",
    response_model=PortfolioBriefingResponse,
)
async def portfolio_briefing() -> PortfolioBriefingResponse:
    """
    Explain every holding in the portfolio, ranked by conviction.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    brain = await BrainBuilderService().build()

    briefing = PortfolioBriefingService().build(brain)

    if briefing is None:
        raise HTTPException(
            status_code=404,
            detail="The portfolio holds no positions to evaluate.",
        )

    brief = briefing.brief

    cases: list[RankedInvestmentCaseResponse] = []

    for rank, workspace in enumerate(briefing.workspaces, start=1):
        decision = workspace.decision
        thesis = workspace.thesis
        reasoning = workspace.reasoning

        if decision is None or thesis is None or reasoning is None:
            continue

        cases.append(
            RankedInvestmentCaseResponse(
                rank=rank,
                symbol=workspace.symbol,
                recommendation=decision.state.value,
                conviction=decision.conviction,
                committee_agreement=_committee_agreement(workspace),
                risk_level=reasoning.risk.risk_level.value,
                summary=thesis.summary,
                why_now=list(thesis.catalysts),
                risks=list(thesis.risks),
                expected_holding_period=thesis.expected_holding_period,
            )
        )

    return PortfolioBriefingResponse(
        headline=brief.headline,
        summary=brief.summary,
        confidence=brief.confidence,
        portfolio_health=brief.portfolio_health,
        priorities=[
            ExecutivePriorityResponse(
                title=priority.title,
                description=priority.description,
                urgency=priority.urgency,
            )
            for priority in brief.priorities
        ],
        investment_cases=cases,
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
