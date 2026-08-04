from app.renderers.brief_renderer import BriefRenderer
from app.services.brief_service import BriefService


async def run() -> int:
    snapshot = await BriefService().build()

    BriefRenderer.render(snapshot)

    return 0
