from app.renderers.explain_renderer import ExplainRenderer


async def run(symbol: str = "SPY") -> int:
    ExplainRenderer.render(symbol)

    return 0
