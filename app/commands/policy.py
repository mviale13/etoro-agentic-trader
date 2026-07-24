from app.renderers.policy_renderer import PolicyRenderer
from app.services.policy_service import PolicyService


async def run() -> int:
    try:
        policy = PolicyService().load()
    except Exception as exc:
        print(f"MOVRvest policy failed: {exc}")
        return 1

    PolicyRenderer.render(policy)
    return 0