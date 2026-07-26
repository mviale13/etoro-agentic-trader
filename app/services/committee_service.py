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
from app.domain.recommendation import Recommendation
from app.providers.crypto_fear_greed_provider import (
    CryptoFearGreedProvider,
)
from app.providers.value_provider import ValueProvider
from app.providers.yahoo_market_provider import YahooMarketProvider
from app.services.account_service import AccountService
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
)
from app.services.market_service import MarketService
from app.services.policy_service import PolicyService
from app.services.portfolio_service import PortfolioService


class CommitteeService:
    async def evaluate(
        self,
        symbol: str = "SPY",
    ) -> Recommendation:
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

        valuation = ValueProvider().snapshot(symbol.upper())

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

        decision = CommitteeChairman().decide(opinions)

        return Recommendation(
            symbol=symbol.upper(),
            portfolio=portfolio,
            intelligence=intelligence,
            decision=decision,
        )
