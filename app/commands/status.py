import httpx

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.renderers.status_renderer import StatusRenderer
from app.services.account_service import AccountService


async def run() -> int:
    settings = get_settings()

    service = AccountService(EtoroAccountBroker(settings))

    try:
        snapshot = await service.snapshot()

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest could not connect to eToro (HTTP {status}).")
        print(body)

        return 1

    except Exception as exc:
        print(f"MOVRvest status failed: {exc}")
        return 1

    StatusRenderer.render(snapshot)

    return 0
