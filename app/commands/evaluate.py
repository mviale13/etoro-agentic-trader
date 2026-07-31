from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.executive import ExecutiveService
from app.renderers.executive_brief_console_renderer import (
    ExecutiveBriefConsoleRenderer,
)


class EvaluateCommand:
    """
    Run the canonical Artificial CIO pipeline for one symbol.

    Brain → Reasoning → Executive Committee → Artificial CIO → Executive Brief
    """

    async def run(
        self,
        symbol: str,
    ) -> int:
        normalized_symbol = symbol.upper().strip()

        brain = await BrainBuilderService().build()

        brief = ExecutiveService().brief(
            symbol=normalized_symbol,
            brain=brain,
        )

        ExecutiveBriefConsoleRenderer.render(
            brief,
        )

        return 0


async def run(
    symbol: str,
) -> int:
    return await EvaluateCommand().run(
        symbol,
    )
