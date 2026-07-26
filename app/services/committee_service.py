from datetime import UTC, datetime

from app.brokers.etoro_account import EtoroAccountBroker
from app.committee.base import CommitteeMember
from app.committee.cash import CashCommittee
from app.committee.chairman import CommitteeChairman
from app.committee.diversification import DiversificationCommittee
from app.committee.momentum import MomentumCommittee
from app.committee.risk import RiskCommittee
from app.committee.value import ValueCommittee
from app.config import get_settings
from app.domain.committee_context import CommitteeContext
from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.recommendation import Recommendation
from app.providers.crypto_fear_greed_provider import (
    CryptoFearGreedProvider,
)
from app.providers.value_provider import ValueProvider
from app.providers.yahoo_market_provider import YahooMarketProvider
from app.repositories.event_repository import EventRepository
from app.repositories.json_event_repository import JsonEventRepository
from app.services.account_service import AccountService
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
)
from app.services.market_service import MarketService
from app.services.policy_service import PolicyService
from app.services.portfolio_service import PortfolioService


class CommitteeService:
    def __init__(
        self,
        event_repository: EventRepository | None = None,
    ) -> None:
        self._event_repository = (
            event_repository if event_repository is not None else JsonEventRepository()
        )

    async def evaluate(
        self,
        symbol: str = "SPY",
    ) -> Recommendation:
        normalized_symbol = symbol.upper()
        settings = get_settings()

        account = await AccountService(
            EtoroAccountBroker(settings),
        ).snapshot()

        portfolio = PortfolioService().analyze(account)
        policy = PolicyService().load()

        market_data = await YahooMarketProvider().snapshot()

        market = MarketService().build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            timestamp=datetime.now(UTC),
        )

        sentiment = await CryptoFearGreedProvider().snapshot()

        intelligence = MarketIntelligenceService().build(
            market=market,
            sentiment=sentiment,
        )

        valuation = ValueProvider().snapshot(
            normalized_symbol,
        )

        context = CommitteeContext(
            intelligence=intelligence,
            portfolio=portfolio,
            policy=policy,
            valuation=valuation,
        )

        committee: list[CommitteeMember] = [
            MomentumCommittee(),
            RiskCommittee(),
            CashCommittee(),
            DiversificationCommittee(),
            ValueCommittee(),
        ]

        opinions = [member.evaluate(context) for member in committee]

        decision = CommitteeChairman().decide(
            opinions,
        )

        recommendation = Recommendation(
            symbol=normalized_symbol,
            portfolio=portfolio,
            intelligence=intelligence,
            decision=decision,
        )

        self._log_recommendation(
            recommendation,
        )

        return recommendation

    def _log_recommendation(
        self,
        recommendation: Recommendation,
    ) -> None:
        decision = recommendation.decision

        self._event_repository.save(
            Event(
                timestamp=datetime.now(UTC),
                event_type=EventType.RECOMMENDATION_GENERATED,
                symbol=recommendation.symbol,
                payload={
                    "recommendation": decision.recommendation,
                    "confidence": decision.confidence,
                    "votes": [
                        {
                            "member": opinion.member,
                            "vote": opinion.vote,
                            "confidence": opinion.confidence,
                            "rationale": opinion.rationale,
                        }
                        for opinion in decision.opinions
                    ],
                },
            )
        )
