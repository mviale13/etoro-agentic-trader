import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.renderers.morning_renderer import MorningRenderer
from app.services.account_service import AccountService
from app.services.morning_brief_service import MorningBriefService
from app.services.portfolio_service import PortfolioService


async def run() -> int:
    settings = get_settings()
    account_service = AccountService(
        EtoroAccountBroker(settings),
    )

    try:
        account = await account_service.snapshot()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest could not connect to eToro (HTTP {status}).")
        print(body)
        return 1
    except Exception as exc:
        print(f"MOVRvest morning brief failed: {exc}")
        return 1

    portfolio = PortfolioService().analyze(account)
    brief = MorningBriefService().build(portfolio)

    MorningRenderer.render(brief)
    return 0
