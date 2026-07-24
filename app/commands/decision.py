from datetime import UTC, datetime

import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.providers.yahoo_market_provider import YahooMarketProvider
from app.renderers.decision_renderer import DecisionRenderer
from app.services.account_service import AccountService
from app.services.decision_engine import DecisionEngine
from app.services.market_service import MarketService
from app.services.policy_analyzer import PolicyAnalyzer
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
        policy_analysis = PolicyAnalyzer().analyze(
            portfolio,
            policy,
        )

        market_data = await YahooMarketProvider().snapshot()
        market = MarketService().build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            timestamp=datetime.now(UTC),
        )

        decision = DecisionEngine().evaluate(
            policy_analysis,
            market,
        )

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest could not retrieve the required data (HTTP {status}).")
        print(body)
        return 1
    except Exception as exc:
        print(f"MOVRvest decision failed: {exc}")
        return 1

    DecisionRenderer.render(decision)
    return 0
