from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_brain_builder_service
from app.api.models.dossier import (
    CommitteeEvidenceResponse,
    CommitteeOpinionResponse,
    DossierResponse,
    EvidenceScoresResponse,
    NarrativeFindingResponse,
    NarrativeResponse,
    NarrativeSectionResponse,
    ProvenanceResponse,
    ScoreResponse,
)
from app.api.models.executive_brief import (
    ExecutiveBriefResponse,
    ExecutivePriorityResponse,
    InvestmentCaseResponse,
)
from app.api.models.portfolio_briefing import (
    ActionResponse,
    BriefingLineResponse,
    ChangeResponse,
    ConvictionChangeResponse,
    PortfolioBriefingResponse,
    RankedInvestmentCaseResponse,
    TodayBriefingResponse,
    TrendResponse,
)
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.brief.today_briefing_builder import TodayBriefingBuilder
from app.application.change_feed.change_feed_service import ChangeFeedService
from app.application.change_feed.holding_exposures import holding_exposures
from app.application.executive.executive_service import ExecutiveService
from app.application.learning.decision_journal import DecisionJournal
from app.application.market import MarketSnapshotArchive
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.domain.decision_history import ConvictionChange, DecisionTrend
from app.domain.executive.executive_action import ExecutiveAction
from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.provenance import Provenance
from app.domain.score_basis import ScoreBases, ScoreBasis
from app.renderers import ExecutiveBriefRenderer
from app.renderers.brief_language import (
    conviction_label,
    health_label,
    urgency_band,
)
from app.repositories.json_event_repository import JsonEventRepository
from app.services.executive_writer_service import ExecutiveWriterService

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
async def portfolio_briefing(
    builder: BrainBuilderService = Depends(get_brain_builder_service),
) -> PortfolioBriefingResponse:
    """
    Explain every holding in the portfolio, ranked by conviction.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    journal = DecisionJournal(
        repository=JsonEventRepository(),
    )

    brain = await builder.build()

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
        evidence = workspace.evidence

        if decision is None or thesis is None or reasoning is None:
            continue

        cases.append(
            RankedInvestmentCaseResponse(
                rank=rank,
                symbol=workspace.symbol,
                recommendation=decision.state.value,
                conviction=decision.conviction,
                conviction_label=conviction_label(decision.conviction),
                committee_agreement=_committee_agreement(workspace),
                # This security's own, not the account's. The account's
                # risk level is identical under every symbol, so ten cards
                # read "Low" together — including the ones running 58%
                # volatility.
                safety_score=(evidence.safety_score if evidence is not None else None),
                summary=thesis.summary,
                why_now=list(thesis.catalysts),
                risks=list(thesis.risks),
                expected_holding_period=thesis.expected_holding_period,
                trend=_trend(thesis.trend),
                action=_action(workspace.action),
                conviction_change=_conviction_change(thesis.conviction_change),
            )
        )

    # Built after the briefing, so a decision that changed during this
    # review is already recorded and reported. The market observation this
    # cycle took is recorded by then too, which is what lets the feed say
    # what the market did as well as what the CIO decided.
    changes = ChangeFeedService(
        journal=journal,
        market=MarketSnapshotArchive(),
        # What each holding is measured to move with, so a benchmark move
        # in the feed can say which holdings it touches — and for how much
        # of the account nothing is measured.
        exposures=holding_exposures(brain),
    ).build(
        symbols=[workspace.symbol for workspace in briefing.workspaces],
    )

    # Composed from the same cycle: the decisions it changed and the
    # earnings schedules it already read per security. Nothing is fetched
    # twice, so the dashboard and the dossiers cannot disagree.
    today = TodayBriefingBuilder().build(
        brain,
        changes.events,
        datetime.now(UTC).date(),
    )

    return PortfolioBriefingResponse(
        today=TodayBriefingResponse(
            lines=[
                BriefingLineResponse(
                    statement=line.statement,
                    notable=line.notable,
                )
                for line in today.lines
            ],
            headline=today.headline,
            is_quiet=today.is_quiet,
        ),
        headline=brief.headline,
        summary=brief.summary,
        confidence=brief.confidence,
        portfolio_health=brief.portfolio_health,
        portfolio_health_label=health_label(brief.portfolio_health),
        priorities=[
            ExecutivePriorityResponse(
                title=priority.title,
                description=priority.description,
                urgency=priority.urgency,
                urgency_band=urgency_band(priority.urgency),
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
    builder: BrainBuilderService = Depends(get_brain_builder_service),
) -> ExecutiveBriefResponse:
    """
    Explain the Artificial CIO decision for one symbol.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    normalized_symbol = symbol.upper().strip()

    brain = await builder.build(
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
        portfolio_health_label=health_label(view.portfolio_health),
        priorities=[
            ExecutivePriorityResponse(
                title=priority.title,
                description=priority.description,
                urgency=priority.urgency,
                urgency_band=urgency_band(priority.urgency),
            )
            for priority in view.priorities
        ],
        investment_cases=[
            InvestmentCaseResponse(
                symbol=case.symbol,
                recommendation=case.recommendation,
                confidence=case.confidence,
                conviction=case.conviction,
                conviction_label=conviction_label(case.conviction),
                summary=case.summary,
                trend=case.trend,
            )
            for case in view.investment_cases
        ],
    )


def _trend(trend: DecisionTrend | None) -> TrendResponse | None:
    """Null stays null: a first review has no trend to report."""

    if trend is None:
        return None

    return TrendResponse(
        direction=trend.direction.value,
        stated=trend.stated,
    )


def _conviction_change(
    change: ConvictionChange | None,
) -> ConvictionChangeResponse | None:
    """Null stays null: a conviction that did not move is not a change."""

    if change is None:
        return None

    return ConvictionChangeResponse(
        previous=change.previous,
        delta=change.delta,
        stated=change.stated,
        because=list(change.because),
        unexplained=change.unexplained,
    )


def _action(action: ExecutiveAction | None) -> ActionResponse | None:
    """The consideration the pipeline built, carried without rewording."""

    if action is None:
        return None

    return ActionResponse(
        kind=action.kind.value,
        statement=action.statement,
        because=action.because,
        checkpoint=action.checkpoint,
    )


def _provenance(
    provenance: Provenance | None,
) -> ProvenanceResponse | None:
    """Null stays null: undated evidence is reported as undated."""

    if provenance is None:
        return None

    return ProvenanceResponse(
        source=provenance.source,
        observed_at=provenance.observed_at,
        age=provenance.stated(),
        last_known=provenance.last_known,
    )


def _score(
    value: int | None,
    basis: ScoreBasis,
) -> ScoreResponse:
    """
    Pair a score with the reasoning the pipeline already worded for it.

    Nothing is derived here and no sentence is written here: both come
    from where the score was computed.
    """

    return ScoreResponse(
        value=value,
        basis=basis.basis,
        evidence=list(basis.evidence),
        kind=basis.kind.value,
        kind_stated=basis.kind.stated,
    )


@router.get(
    "/{symbol}/dossier",
    response_model=DossierResponse,
)
async def dossier(
    symbol: str,
    builder: BrainBuilderService = Depends(get_brain_builder_service),
) -> DossierResponse:
    """
    The complete investment case for one security.

    Composed from the canonical pipeline outputs — ExecutiveDecision,
    InvestmentThesis, DecisionEvidence, CommitteeOpinion, Provenance —
    and from nothing else. Nothing here is derived at the API layer.
    """

    normalized_symbol = symbol.upper().strip()

    brain = await builder.build(
        focus_symbols=(normalized_symbol,),
    )

    workspace = ExecutivePipeline.with_memory().execute(
        symbol=normalized_symbol,
        brain=brain,
    )

    decision = workspace.decision
    thesis = workspace.thesis
    evidence = workspace.evidence

    if decision is None or thesis is None or evidence is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"The Artificial CIO could not produce a decision for "
                f"{normalized_symbol}."
            ),
        )

    # Why each score is the number it is, as the pipeline worded it. A
    # path that stated none says so rather than leaving the scores bare.
    bases = evidence.score_bases or ScoreBases.unrecorded()

    # Communication only, and strictly after the judgment: the writer
    # receives the finished canonical objects and cannot change them.
    outcome = await ExecutiveWriterService().narrate(
        symbol=normalized_symbol,
        decision=decision,
        thesis=thesis,
        evidence=evidence,
        opinions=workspace.committee_opinions,
    )

    return DossierResponse(
        symbol=normalized_symbol,
        decision_state=decision.state.value,
        conviction=decision.conviction,
        conviction_label=conviction_label(decision.conviction),
        committee_agreement=thesis.confidence,
        rationale=decision.rationale,
        trend=_trend(thesis.trend),
        action=_action(workspace.action),
        conviction_change=_conviction_change(thesis.conviction_change),
        decided_at=decision.decided_at,
        summary=thesis.summary,
        expected_holding_period=thesis.expected_holding_period,
        catalysts=list(thesis.catalysts),
        invalidation_conditions=list(thesis.invalidation_conditions),
        next_trigger=decision.next_trigger,
        security_evidenced=evidence.security_evidenced,
        evidence_weighed=list(decision.evidence_weighed),
        strengths=list(decision.key_strengths),
        risks=list(decision.key_risks),
        missing_evidence=list(decision.missing_evidence),
        scores=EvidenceScoresResponse(
            quality=_score(evidence.quality_score, bases.quality),
            evidence=_score(evidence.evidence_score, bases.evidence),
            valuation=_score(evidence.valuation_score, bases.valuation),
            # Safety, not risk: the same reading, turned once, so every
            # score on the page runs the same way.
            safety=_score(evidence.safety_score, bases.safety),
            portfolio_fit=_score(
                evidence.portfolio_fit_score,
                bases.portfolio_fit,
            ),
        ),
        context_strengths=list(thesis.context_strengths),
        context_risks=list(decision.context_risks),
        committees=[
            CommitteeOpinionResponse(
                committee=opinion.committee,
                recommendation=opinion.recommendation.value,
                confidence=opinion.confidence,
                # An abstention is not opposition, and is marked so no
                # surface has to infer the difference from a null.
                abstained=opinion.confidence is None,
                summary=opinion.summary,
                evidence=[
                    CommitteeEvidenceResponse(
                        statement=item.description,
                        source=item.source,
                    )
                    for item in opinion.evidence
                ],
            )
            for opinion in workspace.committee_opinions
        ],
        evidence_as_of=_provenance(decision.evidence_as_of),
        narrative=_narrative(outcome.narrative),
        narrative_absent=outcome.absent_reason,
    )


def _narrative(
    narrative: ExecutiveNarrative | None,
) -> NarrativeResponse | None:
    """The narrative over the wire, citations and provenance intact."""

    if narrative is None:
        return None

    return NarrativeResponse(
        headline=narrative.headline,
        recommendation=narrative.recommendation,
        sections=[
            NarrativeSectionResponse(
                section=section.section,
                text=section.text,
                finding_ids=list(section.finding_ids),
            )
            for section in narrative.sections
        ],
        findings=[
            NarrativeFindingResponse(
                id=finding.id,
                statement=finding.statement,
                source=finding.source,
            )
            for finding in narrative.findings
        ],
        model=narrative.model,
        written=narrative.reading.stated(),
    )
