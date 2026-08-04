from datetime import UTC, datetime

import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.committee.base import CommitteeMember
from app.committee.cash import CashCommittee
from app.committee.chairman import CommitteeChairman
from app.committee.diversification import DiversificationCommittee
from app.committee.momentum import MomentumCommittee
from app.committee.risk import RiskCommittee
from app.config import get_settings
from app.domain.committee_context import CommitteeContext
from app.providers.crypto_fear_greed_provider import (
    CryptoFearGreedProvider,
)
from app.providers.yahoo_market_provider import YahooMarketProvider
from app.renderers.committee_renderer import CommitteeRenderer
from app.services.account_service import AccountService
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
)
from app.services.market_service import MarketService
from app.services.policy_service import PolicyService
from app.services.portfolio_service import PortfolioService


async def run() -> int:
    settings = get_settings()
    account_service = AccountService(
        EtoroAccountBroker(settings),
    )

    try:
        account = await account_service.snapshot()
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

        context = CommitteeContext(
            intelligence=intelligence,
            portfolio=portfolio,
            policy=policy,
        )

        committee: list[CommitteeMember] = [
            MomentumCommittee(),
            RiskCommittee(),
            CashCommittee(),
            DiversificationCommittee(),
        ]

        opinions = [member.evaluate(context) for member in committee]

        decision = CommitteeChairman().decide(opinions)

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest committee failed (HTTP {status}).")
        print(body)
        return 1

    except Exception as exc:
        print(f"MOVRvest committee failed: {exc}")
        return 1

    CommitteeRenderer.render(decision)
    return 0
