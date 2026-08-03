from fastapi import APIRouter, HTTPException

from app.api.models.executive_brief import (
    ExecutiveBriefResponse,
    ExecutivePriorityResponse,
    InvestmentCaseResponse,
)
from app.api.models.portfolio_briefing import (
    ChangeResponse,
    PortfolioBriefingResponse,
    RankedInvestmentCaseResponse,
)
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.change_feed.change_feed_service import ChangeFeedService
from app.application.executive.executive_service import ExecutiveService
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.renderers import ExecutiveBriefRenderer
from app.repositories.json_event_repository import JsonEventRepository

router = APIRouter(
    prefix="/executive",
    tags=["executive"],
)


def _committee_agreement(
    workspace: ExecutiveWorkspace,
) -> int:
    """Mean committee confidence, as a whole percentage."""

    # A committee that could not form a view is silent, not opposed.
    stated = [
        opinion.confidence
        for opinion in workspace.committee_opinions
        if opinion.confidence is not None
    ]

    if not stated:
        return 0

    return max(0, min(100, round(sum(stated) / len(stated) * 100)))


@router.get(
    "/portfolio",
    response_model=PortfolioBriefingResponse,
)
async def portfolio_briefing() -> PortfolioBriefingResponse:
    """
    Explain every holding in the portfolio, ranked by conviction.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    journal = DecisionJournal(
        repository=JsonEventRepository(),
    )

    brain = await BrainBuilderService().build()

    briefing = PortfolioBriefingService(
        pipeline=ExecutivePipeline(journal=journal),
    ).build(brain)

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
                risk_level=(
                    reasoning.risk.risk_level.value
                    if reasoning.risk.risk_level is not None
                    else "Not measured"
                ),
                summary=thesis.summary,
                why_now=list(thesis.catalysts),
                risks=list(thesis.risks),
                expected_holding_period=thesis.expected_holding_period,
                previous_decisions=thesis.previous_decisions,
            )
        )

    # Built after the briefing, so a decision that changed during this
    # review is already recorded and reported.
    changes = ChangeFeedService(journal=journal).build(
        symbols=[workspace.symbol for workspace in briefing.workspaces],
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
        changes=[
            ChangeResponse(
                title=change.title,
                description=change.description,
                category=change.category.value,
                severity=change.severity.value,
                timestamp=change.timestamp,
                action_required=change.action_required,
            )
            for change in changes.events
        ],
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

    brain = await BrainBuilderService().build(
        focus_symbols=(normalized_symbol,),
    )

    brief = ExecutiveService(
        pipeline=ExecutivePipeline.with_memory(),
    ).brief(
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
                previous_decisions=case.previous_decisions,
            )
            for case in view.investment_cases
        ],
    )
