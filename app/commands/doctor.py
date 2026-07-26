import httpx

from app.renderers.doctor_renderer import DoctorRenderer
from app.services.committee_service import CommitteeService
from app.services.doctor_service import DoctorService


async def run() -> int:
    try:
        recommendation = await CommitteeService().evaluate("SPY")

        health = DoctorService().evaluate(
            recommendation,
        )

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text[:400]

        print(f"MOVRvest doctor failed (HTTP {status}).")
        print(body)
        return 1

    except Exception as exc:
        print(f"MOVRvest doctor failed: {exc}")
        return 1

    DoctorRenderer.render(health)

    return 0
