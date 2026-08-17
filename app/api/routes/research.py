from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_brain_builder_service
from app.api.models.portfolio_briefing import TrendResponse
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

    # A rank is a place in the conviction order, so only a case carrying
    # a conviction takes one. The unranked are still researched and still
    # explained; they are not numbered against each other on nothing.
    position = 0

    for workspace in research.workspaces:
        decision = workspace.decision
        evidence = workspace.evidence
        thesis = workspace.thesis

        # Evidence is deliberately not required. A digital asset produces
        # none — its judgment comes from recorded committee judgments
        # rather than from provider scores — and requiring it here would
        # drop a watched token from the research pipeline entirely
        # rather than show it with the answer this platform actually has.
        if decision is None or thesis is None:
            continue

        candidate = research.candidates.get(workspace.symbol)

        if decision.conviction is not None:
            position += 1

        candidates.append(
            ResearchCandidateResponse(
                rank=position if decision.conviction is not None else None,
                symbol=workspace.symbol,
                name=candidate.name if candidate else workspace.symbol,
                source=candidate.source if candidate else "",
                recommendation=decision.state.value,
                conviction=decision.conviction,
                conviction_label=conviction_label(decision.conviction),
                quality_score=evidence.quality_score if evidence else None,
                valuation_score=evidence.valuation_score if evidence else None,
                safety_score=evidence.safety_score if evidence else None,
                portfolio_fit_score=(
                    evidence.portfolio_fit_score if evidence else None
                ),
                evidence_score=evidence.evidence_score if evidence else None,
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
                trend=(
                    TrendResponse(
                        direction=thesis.trend.direction.value,
                        stated=thesis.trend.stated,
                    )
                    if thesis.trend is not None
                    else None
                ),
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
