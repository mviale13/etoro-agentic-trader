import httpx

from app.renderers.daily_renderer import DailyRenderer
from app.services.committee_service import CommitteeService


async def run() -> int:
    try:
        recommendation = await CommitteeService().evaluate("SPY")

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest daily brief failed (HTTP {status}).")
        print(body)
        return 1

    except Exception as exc:
        print(f"MOVRvest daily brief failed: {exc}")
        return 1

    DailyRenderer.render(
        portfolio=recommendation.portfolio,
        intelligence=recommendation.intelligence,
        committee=recommendation.decision,
    )

    return 0
