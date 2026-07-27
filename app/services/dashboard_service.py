from app.api.models.dashboard import DashboardResponse
from app.api.models.investor_dna import InvestorDNAResponse
from app.api.models.observation import ObservationResponse
from app.api.models.opportunity import OpportunityResponse
from app.api.models.portfolio import AllocationResponse, PortfolioResponse
from app.api.models.reflection import ReflectionResponse
from app.api.models.today import (
    HealthCheckResponse,
    HealthResponse,
    OpinionResponse,
    RecommendationResponse,
    TodayResponse,
)
from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.services.account_service import AccountService
from app.services.brief_service import BriefService
from app.services.daily_reflection_service import DailyReflectionService
from app.services.investor_dna_service import InvestorDNAService
from app.services.investor_observation_service import InvestorObservationService
from app.services.opportunity_service import OpportunityService
from app.services.portfolio_service import PortfolioService
from app.services.signal_service import SignalService


class DashboardService:
    async def build(self) -> DashboardResponse:
        today = await self._build_today()
        portfolio, observation = await self._build_portfolio_sections()

        reflection = DailyReflectionService().today()
        dna = InvestorDNAService().analyze([])
        opportunities = OpportunityService().top_opportunities()

        understanding = dna.confidence

        if understanding < 25:
            dna_message = "I'm just getting to know your investment style."
        elif understanding < 50:
            dna_message = "I'm starting to recognize patterns in your decisions."
        elif understanding < 75:
            dna_message = "I can personalize many recommendations."
        else:
            dna_message = "I understand your long-term investment philosophy well."

        return DashboardResponse(
            today=today,
            portfolio=portfolio,
            observation=observation,
            reflection=ReflectionResponse(
                title=reflection.title,
                message=reflection.message,
                source=reflection.source,
            ),
            investor_dna=InvestorDNAResponse(
                understanding=understanding,
                message=dna_message,
            ),
            opportunities=[
                OpportunityResponse(
                    company=item.company,
                    action=item.action,
                    confidence=item.confidence,
                    summary=item.summary,
                )
                for item in opportunities
            ],
        )

    async def _build_today(self) -> TodayResponse:
        snapshot = await BriefService().build()

        return TodayResponse(
            greeting=snapshot.greeting,
            health=HealthResponse(
                score=snapshot.health.overall_score,
                checks=[
                    HealthCheckResponse(
                        name=check.name,
                        score=check.score,
                        status=check.status,
                        message=check.message,
                    )
                    for check in snapshot.health.checks
                ],
            ),
            summary=snapshot.summary,
            changes=list(snapshot.changes),
            recommendation=RecommendationResponse(
                symbol=snapshot.recommendation.symbol,
                action=snapshot.recommendation.decision.recommendation,
                confidence=snapshot.recommendation.decision.confidence,
                opinions=[
                    OpinionResponse(
                        member=opinion.member,
                        vote=opinion.vote,
                        confidence=opinion.confidence,
                        rationale=opinion.rationale,
                    )
                    for opinion in snapshot.recommendation.decision.opinions
                ],
            ),
            next_action=snapshot.next_action,
        )

    async def _build_portfolio_sections(
        self,
    ) -> tuple[PortfolioResponse | None, ObservationResponse | None]:
        try:
            settings = Settings()
            broker = EtoroAccountBroker(settings)
            account = await AccountService(broker).snapshot()
            snapshot = PortfolioService().analyze(account)
        except Exception:
            return None, None

        portfolio = PortfolioResponse(
            total_value=snapshot.total_value,
            total_value_eur=snapshot.total_value_eur,
            positions=snapshot.positions,
            allocation=AllocationResponse(
                cash=snapshot.allocation.cash,
                stocks=snapshot.allocation.stocks,
                etfs=snapshot.allocation.etfs,
                crypto=snapshot.allocation.crypto,
                unclassified=snapshot.allocation.unclassified,
            ),
            risk_flags=list(snapshot.risk_flags),
        )

        signals = SignalService().analyze(
            current=snapshot,
            previous=None,
        )
        result = InvestorObservationService().observe(signals)

        observation = ObservationResponse(
            title=result.title,
            message=result.message,
            category=result.category,
        )

        return portfolio, observation
