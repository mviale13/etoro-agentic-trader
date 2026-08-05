"""Run the identical dossier through every writing provider and compare."""

from __future__ import annotations

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.renderers.writer_comparison_renderer import WriterComparisonRenderer
from app.services.writer_comparison_service import WriterComparisonService


class WriterCompareCommand:
    """
    One canonical decision, worded by every provider.

    The pipeline runs once, so both providers receive the identical
    findings — the comparison is about language, latency and spend,
    never about evidence. The command is its own opt-in: invoking it is
    the request to generate language, so it does not sit behind the
    dossier's writer flag.
    """

    async def run(self, symbol: str) -> int:
        normalized_symbol = symbol.upper().strip()

        brain = await BrainBuilderService().build(
            focus_symbols=(normalized_symbol,),
        )

        workspace = ExecutivePipeline.with_memory().execute(
            symbol=normalized_symbol,
            brain=brain,
        )

        decision = workspace.decision
        thesis = workspace.thesis
        evidence = workspace.evidence

        if decision is None or thesis is None or evidence is None:
            print(
                f"The Artificial CIO could not produce a decision for "
                f"{normalized_symbol}, so there is nothing to word."
            )
            return 1

        comparison = await WriterComparisonService().compare(
            symbol=normalized_symbol,
            decision=decision,
            thesis=thesis,
            evidence=evidence,
            opinions=workspace.committee_opinions,
        )

        WriterComparisonRenderer.render(comparison)
        return 0


async def run(symbol: str) -> int:
    return await WriterCompareCommand().run(symbol)
