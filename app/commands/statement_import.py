"""Carry statement observations from an isolated store into another store.

The operator half of promotion, and an explicit maintenance action like
`statement-audit --supersede`: dry-run by default, listing exactly what
would move and what is refused, per observation; `--apply` is the write.
Ordinary reads never import.

It never observes, never asks a model, never touches a provider, and
never rewrites anything — the source is opened read-only, and the target
only ever gains whole observations through the store's append door.
Deserialization is admission to inspection, never to a consensus: an
observation is appended only where its compatibility with today's
semantic contract is proven, by its own located labels and by the
promotion manifest's evidence-backed ruling on its absences. Anything
unproven is refused and says so.
"""

from __future__ import annotations

from pathlib import Path

from app.infrastructure.evidence_root import evidence_path
from app.services.statement_promotion import (
    ArtifactPlan,
    ImportRuling,
    StatementPromotion,
)


class StatementImportCommand:
    def run(self, source: str, into: str | None, apply: bool) -> int:
        source_directory = Path(source)

        if not source_directory.is_dir():
            print(f"{source_directory} is not a directory, so nothing was read.")
            return 1

        target_directory = Path(into) if into else evidence_path("statements")

        promotion = StatementPromotion(source_directory, target_directory)

        print("Statement import — existing observations moved, none created.")
        print(f"  source: {source_directory}")
        print(f"  target: {target_directory}")
        print(
            "Dry run; nothing is written."
            if not apply
            else "Applying: proven-compatible observations will be appended."
        )
        print()

        if apply:
            outcome = promotion.apply()
            plans = outcome.plans
        else:
            plans = promotion.plan()

        compatible = 0

        for plan in plans:
            _render(plan)
            compatible += plan.counted(ImportRuling.COMPATIBLE)

        print()

        if apply:
            print(f"observations appended: {outcome.appended}")
        elif compatible:
            print(
                f"observations that would be appended: {compatible}. "
                "Nothing was written; re-run with --apply to append them."
            )
        else:
            print(
                "Nothing would be appended: everything is already held, "
                "refused, or unproven."
            )

        return 0


def _render(plan: ArtifactPlan) -> None:
    name = plan.path.name

    if plan.refused_because is not None:
        print(f"  {name}: REFUSED — {plan.refused_because}")
        return

    counts = "  ".join(
        f"{ruling.value}={plan.counted(ruling)}"
        for ruling in ImportRuling
        if plan.counted(ruling)
    )

    print(f"  {name}: {plan.symbol} {plan.key} — {counts or 'nothing decoded'}")

    for ruled in plan.rulings:
        line = (
            f"      [{ruled.ruling.value}] {ruled.statement.value} "
            f"read {ruled.observed_at}"
        )

        if ruled.located:
            line += f" — {ruled.located}"

        print(line)

        if ruled.because:
            print(f"          {ruled.because}")


def run(source: str, into: str | None, apply: bool) -> int:
    return StatementImportCommand().run(source, into, apply)
