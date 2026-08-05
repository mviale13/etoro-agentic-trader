"""Print a writer comparison: two narratives, measured differences, no verdict."""

from __future__ import annotations

from app.domain.writer_comparison import ProviderRun, WriterComparison

RULE = "────────────────────────────────"


class WriterComparisonRenderer:
    @staticmethod
    def render(comparison: WriterComparison) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print(f"Executive Writer comparison — {comparison.symbol}")
        print(f"Decision (identical for every provider): {comparison.decision_state}")
        print(RULE)

        for run in comparison.runs:
            WriterComparisonRenderer._render_run(run)

        print()
        print(
            f"Costs price each provider's own token report at prices "
            f"read {comparison.prices_stated_on.isoformat()}; they are "
            f"not live quotes."
        )
        print(
            "Both narratives rest on the same findings and passed the "
            "same validation. Which reads better is your judgment — "
            "the platform does not score language."
        )
        print()

    @staticmethod
    def _render_run(run: ProviderRun) -> None:
        print()
        print(f"{run.provider} — {run.model}")

        if run.latency_seconds is not None:
            print(f"  Latency : {run.latency_seconds:.2f}s measured")

        if run.usage is not None:
            print(
                f"  Tokens  : {run.usage.input_tokens:,} in / "
                f"{run.usage.output_tokens:,} out, as reported"
            )
        else:
            print("  Tokens  : not reported")

        if run.cost_usd is not None:
            print(f"  Cost    : ${run.cost_usd:.4f} at stated prices")
        else:
            print("  Cost    : not stated")

        print()

        if run.narrative is None:
            print(f"  {run.absent_reason}")
            return

        print(f"  {run.narrative.headline}")

        for section in run.narrative.sections:
            title = section.section.replace("_", " ").title()
            cited = ", ".join(section.finding_ids)

            print()
            print(f"  {title}  [{cited}]")
            print(f"  {section.text}")
