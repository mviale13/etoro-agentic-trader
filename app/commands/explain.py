import httpx

from app.renderers.explain_renderer import ExplainRenderer
from app.services.committee_service import CommitteeService


async def run(symbol: str = "SPY") -> int:
    try:
        recommendation = await CommitteeService().evaluate(symbol)

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest explain failed (HTTP {status}).")
        print(body)
        return 1

    except Exception as exc:
        print(f"MOVRvest explain failed: {exc}")
        return 1

    ExplainRenderer.render(recommendation)

    return 0
