from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_brain_builder_service
from app.api.models.research import (
    ResearchCandidateResponse,
    ResearchFunnelResponse,
    ResearchPipelineResponse,
    WatchedCandidateResponse,
)
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.candidate_research_service import (
    CandidateResearchService,
)
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.renderers.brief_language import conviction_label  # noqa: I001
from app.repositories.json_event_repository import JsonEventRepository

router = APIRouter(
    prefix="/research",
    tags=["research"],
)

#: How many watched securities one request may evidence. Each one costs a
#: fundamentals request against a rate-limited provider, so the page reports
#: how much of the universe it covered rather than pretending to cover it all.
DEFAULT_CANDIDATE_LIMIT = 12


@router.get(
    "/candidates",
    response_model=ResearchPipelineResponse,
)
async def research_candidates(
    limit: int = Query(
        default=DEFAULT_CANDIDATE_LIMIT,
        ge=1,
        le=40,
        description="How many watched securities to evidence this cycle.",
    ),
    builder: BrainBuilderService = Depends(get_brain_builder_service),
) -> ResearchPipelineResponse:
    """
    Judge the securities the investor watches but does not hold.

    Watchlists → Brain → Reasoning → Executive Committee → Artificial CIO
    """

    brain = await builder.build(candidate_limit=limit)

    research = CandidateResearchService(
        pipeline=ExecutivePipeline(
            journal=DecisionJournal(
                repository=JsonEventRepository(),
            ),
        ),
    ).build(brain)

    candidates: list[ResearchCandidateResponse] = []

    for rank, workspace in enumerate(research.workspaces, start=1):
        decision = workspace.decision
        evidence = workspace.evidence
        thesis = workspace.thesis

        if decision is None or evidence is None or thesis is None:
            continue

        candidate = research.candidates.get(workspace.symbol)

        candidates.append(
            ResearchCandidateResponse(
                rank=rank,
                symbol=workspace.symbol,
                name=candidate.name if candidate else workspace.symbol,
                source=candidate.source if candidate else "",
                recommendation=decision.state.value,
                conviction=decision.conviction,
                conviction_label=conviction_label(decision.conviction),
                quality_score=evidence.quality_score,
                valuation_score=evidence.valuation_score,
                risk_score=evidence.risk_score,
                portfolio_fit_score=evidence.portfolio_fit_score,
                evidence_score=evidence.evidence_score,
                evidence_as_of=(
                    decision.evidence_as_of.stated()
                    if decision.evidence_as_of is not None
                    else None
                ),
                evidence_weighed=list(decision.evidence_weighed),
                why_not_yet=decision.rationale,
                missing_evidence=list(decision.missing_evidence),
                catalysts=list(decision.catalysts),
                next_trigger=decision.next_trigger,
                previous_decisions=thesis.previous_decisions,
            )
        )

    funnel = research.funnel

    return ResearchPipelineResponse(
        funnel=ResearchFunnelResponse(
            candidates=funnel.candidates,
            reviewed=funnel.reviewed,
            evidenced=funnel.evidenced,
            unevidenced=funnel.unevidenced,
            not_reviewed=funnel.not_reviewed,
            judged=funnel.judged,
            actionable=funnel.actionable,
        ),
        candidates=candidates,
        unevidenced=[
            WatchedCandidateResponse(
                symbol=candidate.symbol,
                name=candidate.name,
                source=candidate.source,
            )
            for candidate in research.unevidenced
        ],
        not_reviewed=[
            WatchedCandidateResponse(
                symbol=candidate.symbol,
                name=candidate.name,
                source=candidate.source,
            )
            for candidate in research.not_reviewed
        ],
    )
