from collections.abc import Mapping
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_brain_builder_service
from app.api.models.asset_profile_adapter import asset_profile_response
from app.api.models.crypto_market_adapter import crypto_market_response
from app.api.models.crypto_playbook_adapter import crypto_playbook_response
from app.api.models.dossier import (
    ClassificationResponse,
    CommitteeOpinionResponse,
    CommitteeUncertaintyResponse,
    ContributionResponse,
    DecisionCourseResponse,
    DerivationResponse,
    DossierDefinitionResponse,
    DossierResponse,
    EarnedPlaybookResponse,
    EvidenceScoresResponse,
    FundCostResponse,
    IndustryContextResponse,
    NarrativeFindingResponse,
    NarrativeOutcomeResponse,
    NarrativeResponse,
    NarrativeSectionResponse,
    PlaybookCoverageResponse,
    PlaybookResponse,
    ProvenanceResponse,
    RatingDimensionResponse,
    RecordedTransitionResponse,
    ScoreResponse,
    TokenRatingResponse,
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
from app.api.models.protocol_adapter import protocol_fundamentals_response
from app.api.models.supply_adapter import supply_response
from app.api.models.synthesis import synthesis_response
from app.api.models.understanding_adapter import understanding_response
from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.brief.today_briefing_builder import TodayBriefingBuilder
from app.application.change_feed.change_feed_service import ChangeFeedService
from app.application.change_feed.holding_exposures import holding_exposures
from app.application.executive.decision_synthesis_builder import synthesise
from app.application.executive.executive_service import ExecutiveService
from app.application.learning.decision_journal import DecisionJournal
from app.application.market import MarketSnapshotArchive
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.brain import Brain
from app.domain.asset_class import AssetClass
from app.domain.committee.panel import Panel
from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.decision_history import (
    ConvictionChange,
    DecisionHistory,
    DecisionTrend,
)
from app.domain.dossier_definition import DossierDefinition, definition_for
from app.domain.executive.executive_action import ExecutiveAction
from app.domain.executive_narrative import ExecutiveNarrative
from app.domain.playbook import InvestmentPlaybook
from app.domain.playbook_selection import PlaybookSelection
from app.domain.provenance import Provenance
from app.domain.research_plan import AnalystKey
from app.domain.score_basis import ScoreBases, ScoreBasis
from app.domain.token_rating import TokenRating
from app.domain.valuation_snapshot import ValuationSnapshot
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.token_insight_provider import CachedTokenInsightProvider
from app.renderers import ExecutiveBriefRenderer
from app.renderers.brief_language import (
    conviction_label,
    health_label,
    urgency_band,
)
from app.repositories.json_event_repository import JsonEventRepository
from app.services.company_understanding_service import (
    CompanyUnderstanding,
    CompanyUnderstandingService,
)
from app.services.crypto_market_service import CryptoMarketService
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.executive_writer_service import ExecutiveWriterService
from app.services.playbook_mapping import select_grounded
from app.services.protocol_fundamentals_service import (
    ProtocolFundamentalsService,
)
from app.services.supply_semantics_service import SupplySemanticsService
from app.services.token_facts_service import TokenFactsService

router = APIRouter(
    prefix="/executive",
    tags=["executive"],
)


def _committee_agreement(
    workspace: ExecutiveWorkspace,
) -> int:
    """How far the committees that spoke pointed the same way, as a percentage.

    This used to average their confidence floats while being called
    agreement, so two committees flatly contradicting each other on
    well-read evidence outscored two agreeing on thin evidence.

    A committee that could not form a view is silent, not opposed, and
    is not counted either way.
    """

    agreement = Panel(opinions=workspace.committee_opinions).agreement_pct

    # Nobody spoke. Zero would say they disagreed completely, which is
    # the opposite of what an empty panel means.
    return 0 if agreement is None else agreement


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
                playbook_name=_playbook_name(brain, workspace.symbol),
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


def _playbook_name(brain: Brain, symbol: str) -> str | None:
    """What kind of investment this is read as, or nothing gathered."""

    company = brain.security_evidence(symbol)

    if company is None or company.signals.research is None:
        return None

    return company.signals.research.playbook.name


def _playbook(playbook: InvestmentPlaybook | None) -> PlaybookResponse | None:
    """
    The framework, with every analysis marked asked-for or declined.

    Coverage is built from the whole set of analysts this platform has,
    not from the ones that ran — a reader comparing two dossiers must be
    able to see that a question was declined rather than merely absent.
    """

    if playbook is None:
        return None

    declined = {item.analyst: item.reason for item in playbook.excluded}

    return PlaybookResponse(
        kind=playbook.kind.value,
        name=playbook.name,
        explanation=playbook.explanation,
        priorities=list(playbook.priorities),
        coverage=[
            PlaybookCoverageResponse(
                analyst=analyst.value,
                label=analyst.label,
                covered=analyst in playbook.analysts,
                reason=declined.get(analyst),
            )
            for analyst in AnalystKey
            if analyst in playbook.analysts or analyst in declined
        ],
        classified=playbook.is_classified,
    )


def _decision_course(
    history: DecisionHistory,
    labels: Mapping[str, str],
) -> DecisionCourseResponse:
    """Every recorded change of mind about this security, worded by the domain.

    Composed from the history the Brain already perceived for this cycle
    — the same records the pipeline decided against — so this adds no
    store read, no fetch and no model call to a page view. It reaches no
    score and no decision: the case above was decided before this
    exists.

    `labels` are the dossier definition's own score names, so a token's
    quality moving reads as an asset-quality move rather than a
    business-quality one.
    """

    course = history.course(labels)

    return DecisionCourseResponse(
        reviews=course.reviews,
        changes=course.changes,
        first_recorded_at=course.first_recorded_at,
        last_recorded_at=course.last_recorded_at,
        transitions=[
            RecordedTransitionResponse(
                at=transition.at,
                from_state=transition.from_state,
                to_state=transition.to_state,
                from_conviction=transition.from_conviction,
                to_conviction=transition.to_conviction,
                stated=transition.stated,
                rationale=transition.rationale,
                moved=list(transition.moved),
                unexplained=transition.unexplained,
            )
            for transition in course.transitions
        ],
        stated=course.stated,
        absent_because=course.absent_because,
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


def _fund_cost(
    symbol: str,
    asset_class: AssetClass | None,
) -> FundCostResponse | None:
    """What owning the fund costs, read from the store and judged by nobody.

    Composed here at the surface, the token-rating pattern: not on
    `CompanyFacts`' signals path, not near a selector, so "it reaches no
    score" is a fact about the code. Read-only — the stored door serves
    what the last acquisition read, and a fund never acquired has no
    cost figure rather than a fetched one.
    """

    if asset_class is not AssetClass.ETF:
        return None

    snapshot = CachedValueProvider.stored().snapshot(symbol)

    if snapshot.expense_ratio is None or snapshot.reading is None:
        return None

    return FundCostResponse(
        stated=(
            f"Owning this fund costs {snapshot.expense_ratio:.2%} of assets "
            "per year — the total expense ratio, as the provider reports it."
        ),
        expense_ratio=snapshot.expense_ratio,
        read=ProvenanceResponse(
            source=snapshot.reading.source,
            observed_at=snapshot.reading.observed_at,
            age=snapshot.reading.stated(),
            last_known=snapshot.reading.last_known,
        ),
    )


def _token_rating(rating: TokenRating | None) -> TokenRatingResponse | None:
    """Somebody else's rating, carried with their name on it or not at all."""

    if rating is None:
        return None

    return TokenRatingResponse(
        source=rating.reading.source,
        name=rating.name,
        level=rating.level,
        score=rating.score,
        dimensions=[
            RatingDimensionResponse(label=dimension.label, score=dimension.score)
            for dimension in rating.dimensions
        ],
        reviewed_at=rating.reviewed_at,
        page_url=rating.page_url,
        report_url=rating.report_url,
        read=ProvenanceResponse(
            source=rating.reading.source,
            observed_at=rating.reading.observed_at,
            age=rating.reading.stated(),
            last_known=rating.reading.last_known,
        ),
    )


def _definition(definition: DossierDefinition) -> DossierDefinitionResponse:
    """The dossier's own semantics, carried without rewording."""

    return DossierDefinitionResponse(
        kind=definition.kind.value,
        title=definition.title,
        classification_heading=definition.classification_heading,
        analysis_heading=definition.analysis_heading,
        filings_apply=definition.filings_apply,
        filings_inapplicable_because=definition.filings_inapplicable_because,
    )


def _classification(
    symbol: str,
    definition: DossierDefinition,
    understanding: CompanyUnderstanding | None,
) -> ClassificationResponse | None:
    """Industry and the earned playbook, side by side and never blended.

    Composed here at the surface, the fund-cost pattern: the stored
    fundamentals door and the understanding the route already composed,
    consumed by no analyst, no score and no decision — the decision
    fields in the response are computed before this exists. Null where
    the subject is not a company: a token's and a fund's sections
    declare their own semantics, and a company classification printed
    over them would be a claim about a business they do not run.
    """

    if not definition.filings_apply:
        return None

    return ClassificationResponse(
        industry=_industry_context(CachedValueProvider.stored().snapshot(symbol)),
        playbook=_earned_playbook(understanding),
        distinction=(
            "Industry is where the market files this company, as the "
            "data provider reports it. The investment playbook is what "
            "kind of economic business this platform established from "
            "the company's own filing. They answer different questions, "
            "and neither substitutes for the other."
        ),
    )


def _industry_context(snapshot: ValuationSnapshot) -> IndustryContextResponse:
    """The provider's category strings, dated — or their honest absence.

    Two absences, kept apart: a profile that was read and names no
    industry (the provider's own answer) and a profile never acquired
    (this platform's, because acquisition is explicit and no page view
    performs it).
    """

    if snapshot.reading is None:
        return IndustryContextResponse(
            label="Not acquired",
            industry=None,
            sector=None,
            stated=(
                "No provider profile has been acquired for this "
                "security, so no industry is held. Acquisition is "
                "explicit — a page view performs none."
            ),
            read=None,
        )

    read = ProvenanceResponse(
        source=snapshot.reading.source,
        observed_at=snapshot.reading.observed_at,
        age=snapshot.reading.stated(),
        last_known=snapshot.reading.last_known,
    )

    if snapshot.industry is None:
        return IndustryContextResponse(
            label="None reported",
            industry=None,
            sector=snapshot.sector,
            stated="The data provider reports no industry for this security.",
            read=read,
        )

    return IndustryContextResponse(
        label=snapshot.industry,
        industry=snapshot.industry,
        sector=snapshot.sector,
        stated=(
            f"The data provider files this company under "
            f"{snapshot.industry!r} — context about where it operates, "
            "not a conclusion from its filing."
        ),
        read=read,
    )


def _earned_playbook(
    understanding: CompanyUnderstanding | None,
) -> EarnedPlaybookResponse:
    """The grounded route's answer for this company, in its honest state.

    The same canonical mapping the CLI's two-route selector runs —
    `select_grounded` over Business Understanding — applied to the
    understanding this page already composed from the store's read-only
    door. Three states, never collapsed and never defaulted: what was
    established, what the route itself refused with its reason, and what
    is not held under the current reading contract. No industry string
    can reach this: a fallback here would recreate the substitution this
    section exists to end.
    """

    if understanding is None or understanding.business is None:
        absent = (
            understanding.business_absent_because if understanding is not None else None
        )

        return EarnedPlaybookResponse(
            state="unavailable",
            playbook=None,
            label="Not established",
            stated=absent
            or (
                "No current reading of this company's filing is held, "
                "so no playbook could be established from one."
            ),
            narrowest_agreement=None,
        )

    selection = select_grounded(understanding.business)

    if not isinstance(selection, PlaybookSelection):
        return EarnedPlaybookResponse(
            state="refused",
            playbook=None,
            label="Not established",
            stated=selection.because,
            narrowest_agreement=None,
        )

    return EarnedPlaybookResponse(
        state="established",
        playbook=selection.playbook.name,
        label=selection.playbook.name,
        stated=selection.selected_because,
        narrowest_agreement=selection.narrowest_agreement,
    )


def _score(
    value: int | None,
    basis: ScoreBasis,
    label: str,
) -> ScoreResponse:
    """
    Pair a score with the reasoning the pipeline already worded for it.

    Nothing is derived here and no sentence is written here: both come
    from where the score was computed, and the label from the dossier's
    definition.
    """

    derivation = basis.derivation

    return ScoreResponse(
        value=value,
        label=label,
        basis=basis.basis,
        evidence=list(basis.evidence),
        kind=basis.kind.value,
        kind_stated=basis.kind.stated,
        derivation=(
            None
            if derivation is None
            else DerivationResponse(
                contributions=[
                    ContributionResponse(
                        statement=item.statement,
                        points=item.points,
                        sense=item.sense.value,
                        verdict=item.verdict,
                    )
                    for item in derivation.contributions
                ],
                earned=derivation.earned,
                available=derivation.available,
                band=derivation.band,
                score=derivation.score,
                scale=list(derivation.scale),
                required=derivation.required,
                capped_by_unreadable_factors=(
                    derivation.is_capped_by_unreadable_factors
                ),
                stated=derivation.stated(),
                established_factors=derivation.established_factors,
                candidate_factors=derivation.candidate_factors,
                coverage=derivation.coverage,
            )
        ),
    )


@router.get(
    "/{symbol}/narrative",
    response_model=NarrativeOutcomeResponse,
)
async def narrative(
    symbol: str,
    builder: BrainBuilderService = Depends(get_brain_builder_service),
) -> NarrativeOutcomeResponse:
    """
    The Artificial CIO's case, put into words.

    Its own request because it is its own wait. The dossier's evidence
    is ready in under two seconds and this takes fifteen to twenty, all
    of it one model call — so asking for them together made the investor
    wait on communication for a case that was already decided.

    The case is rebuilt here rather than carried over. That costs the
    reasoning twice, and it is the honest trade: the alternative is
    holding a decided case in memory between two requests, where it
    could be worded from something the second request would no longer
    decide.
    """

    normalized_symbol = symbol.upper().strip()

    brain = await builder.build(focus_symbols=(normalized_symbol,))

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

    # Communication only, and strictly after the judgment: the writer
    # receives the finished canonical objects and cannot change them.
    outcome = await ExecutiveWriterService().narrate(
        symbol=normalized_symbol,
        decision=decision,
        thesis=thesis,
        evidence=evidence,
        opinions=workspace.committee_opinions,
        # What kind of security this is, so a case with no company behind
        # it is left as measured rather than written up.
        asset_class=brain.asset_class_for(normalized_symbol),
    )

    return NarrativeOutcomeResponse(
        symbol=normalized_symbol,
        narrative=_narrative(outcome.narrative),
        narrative_absent=outcome.absent_reason,
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

    # A digital asset this platform reads has one decision surface, and
    # it is not this one. This route answered BTC with a conviction of
    # 46 from provider-fed signals the crypto rulings retired, beside a
    # crypto dossier that held the platform's best-grounded evidence and
    # refused to score — one asset, two live product answers. Gone, not
    # redirected: the two payloads share no shape, so a redirect would
    # hand a parser a page it cannot read. The gate is `ASSIGNMENTS` —
    # the same declaration the crypto corpus and its switcher serve, so
    # the two surfaces cannot disagree about which assets it covers —
    # and it runs before the pipeline, so retirement costs no build.
    if normalized_symbol in ASSIGNMENTS:
        raise HTTPException(
            status_code=410,
            detail=(
                f"The executive dossier no longer answers for {normalized_symbol}: "
                "a digital asset has one decision surface, "
                f"GET /crypto/{normalized_symbol}/dossier."
            ),
        )

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

    # What kind of investment case this is — equity, crypto, or the
    # general default — and therefore what the sections below are called
    # and which of them belong. Decided here, from the asset class the
    # Brain already holds, so the page renders semantics it was told.
    asset_class = brain.asset_class_for(normalized_symbol)
    definition = definition_for(asset_class)

    # A token's market facts, judged through the validation gate on
    # read: standings, dates, sources and the claims that failed. Read
    # from the stores only — null for anything that is not a
    # cryptocurrency, and the service itself refuses to promote an
    # unclassified security to a token.
    token_facts = TokenFactsService().established(
        normalized_symbol,
        normalized_symbol,
        asset_class,
    )

    # The economics of the system behind the token — its own evidence
    # family, read from the store only, independent of whether the
    # market facts above reached agreement, and consumed by nothing.
    protocol_facts = ProtocolFundamentalsService().established(
        normalized_symbol,
        asset_class,
    )

    # Which investment questions this kind of digital asset is asked at
    # all, and what evidence would answer each. Read from the same two
    # stores and nothing else; applicability is settled from the
    # archetype before a figure is consulted, so no absence of data can
    # turn a legitimate question into an inapplicable one.
    crypto_playbook = CryptoPlaybookService().established(
        normalized_symbol,
        asset_class,
    )

    # What kind of market this asset is trading inside — its own
    # evidence family, read from the cycle the last acquisition stored.
    # Market context is never Asset Quality: nothing below consumes it,
    # and it is rendered in a section of its own.
    crypto_market = CryptoMarketService().context(
        normalized_symbol,
        asset_class,
    )

    # What each supply number counts. Read from the same stores; the
    # semantics explain a disagreement rather than resolving one, and
    # no standing here reaches a score.
    supply = SupplySemanticsService().established(
        normalized_symbol,
        asset_class,
    )

    # Read from the stores only — no fetch, no model — and composed
    # before the narrative so the conclusion below is available whether
    # or not the optional writer runs.
    #
    # Not composed at all where the subject publishes no filings: a
    # token's dossier saying "no filing has been read yet" promised work
    # nobody can do, and an inapplicable section is not sent rather than
    # sent empty. The definition carries the reason.
    understanding = (
        CompanyUnderstandingService().understanding(normalized_symbol)
        if definition.filings_apply
        else None
    )

    # A third party's published rating, read from the store and composed
    # here at the surface — deliberately not on `CompanyFacts`, not on
    # the signals and not in the research package. Reaching it only at
    # the edge is what makes "it never touches a selector" a fact about
    # the code rather than a promise in a docstring.
    token_rating = _token_rating(
        CachedTokenInsightProvider.stored().rating(normalized_symbol)
    )

    # The narrative is not written here. It is communication, it is
    # optional, and it took fifteen to twenty seconds of a request whose
    # evidence took under two — so the case is served as soon as it is
    # decided, and `/{symbol}/narrative` words it separately.
    #
    # Nothing is lost by that: the conclusion below is deterministic and
    # already stands without a writer.

    return DossierResponse(
        symbol=normalized_symbol,
        definition=_definition(definition),
        decision_state=decision.state.value,
        conviction=decision.conviction,
        conviction_label=conviction_label(decision.conviction),
        committee_agreement=thesis.confidence,
        rationale=decision.rationale,
        trend=_trend(thesis.trend),
        action=_action(workspace.action),
        conviction_change=_conviction_change(thesis.conviction_change),
        # What the CIO decided before, and what moved each time it
        # changed its mind. Read from the history the Brain already
        # perceived for this cycle, so this opens no store and adds no
        # fetch to a page view; composed after the decision it describes
        # and consumed by none of it.
        decision_course=_decision_course(
            brain.decision_history_for(normalized_symbol),
            definition.score_labels,
        ),
        playbook=_playbook(
            company.signals.research.playbook
            if (company := brain.security_evidence(normalized_symbol)) is not None
            and company.signals.research is not None
            else None
        ),
        # Industry beside the earned playbook, each in its honest state.
        # Read from the stored doors only, and consumed by nothing: the
        # decision fields in this response are computed before this
        # exists.
        classification=_classification(
            normalized_symbol,
            definition,
            understanding,
        ),
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
            quality=_score(
                evidence.quality_score,
                bases.quality,
                definition.score_labels["quality"],
            ),
            evidence=_score(
                evidence.evidence_score,
                bases.evidence,
                definition.score_labels["evidence"],
            ),
            valuation=_score(
                evidence.valuation_score,
                bases.valuation,
                definition.score_labels["valuation"],
            ),
            # Safety, not risk: the same reading, turned once, so every
            # score on the page runs the same way.
            safety=_score(
                evidence.safety_score,
                bases.safety,
                definition.score_labels["safety"],
            ),
            portfolio_fit=_score(
                evidence.portfolio_fit_score,
                bases.portfolio_fit,
                definition.score_labels["portfolio_fit"],
            ),
        ),
        context_strengths=list(thesis.context_strengths),
        context_risks=list(decision.context_risks),
        committees=[
            CommitteeOpinionResponse(
                committee=opinion.committee,
                stance=None if opinion.stance is None else opinion.stance.stated,
                # An abstention is not opposition, and is marked so no
                # surface has to infer the difference from a null.
                abstained=not opinion.has_opinion,
                abstained_because=opinion.abstained_because,
                confidence=(
                    None if opinion.confidence is None else opinion.confidence.stated()
                ),
                decided_by=opinion.decided_by,
                summary=opinion.summary,
                # Resolved through the decision's own ledger, so what the
                # investor reads is the finding the committee pointed at
                # and can never be prose the committee composed itself.
                supporting=list(decision.findings.statements_for(opinion.supporting)),
                opposing=list(decision.findings.statements_for(opinion.opposing)),
                uncertainty=[
                    CommitteeUncertaintyResponse(
                        kind=item.kind.value,
                        about=item.about,
                        resolvable=item.is_resolvable,
                    )
                    for item in opinion.uncertainty
                ],
            )
            for opinion in workspace.committee_opinions
        ],
        evidence_as_of=_provenance(decision.evidence_as_of),
        token_rating=token_rating,
        fund_cost=_fund_cost(normalized_symbol, asset_class),
        asset_profile=asset_profile_response(token_facts),
        protocol_fundamentals=protocol_fundamentals_response(protocol_facts),
        crypto_playbook=crypto_playbook_response(crypto_playbook),
        crypto_market=crypto_market_response(crypto_market),
        supply=supply_response(supply),
        # Both null on purpose: this route no longer words the case.
        narrative=None,
        narrative_absent=None,
        # Composed after the decision and consumed by none of it. Read
        # from the stores only, so this adds no fetch and no model call
        # to a page view — a company nothing has been observed for
        # arrives with both halves absent and their reasons worded.
        #
        # Null where filings do not apply to the subject: an absent
        # section, not an empty one, with the reason on the definition.
        understanding=(
            understanding_response(understanding) if understanding is not None else None
        ),
        # Composed from the decision, the thesis and the understanding
        # already in hand. Deterministic, and complete without the
        # writer: the dossier's conclusion never depends on a model.
        synthesis=synthesis_response(synthesise(decision, understanding)),
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
