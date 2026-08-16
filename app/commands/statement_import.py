"""Carry statement observations from an isolated store into another store.

The operator half of promotion, and an explicit maintenance action like
`statement-audit --supersede`: dry-run by default, listing exactly what
would move; `--apply` is the write. Ordinary reads never import.

It never observes, never asks a model, never touches a provider, and
never rewrites anything — the source is opened read-only, and the target
only ever gains whole observations through the store's append door.
"""

from __future__ import annotations

from pathlib import Path

from app.infrastructure.evidence_root import evidence_path
from app.services.statement_promotion import ArtifactPlan, StatementPromotion


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
            else "Applying: new observations will be appended to the target."
        )
        print()

        if apply:
            outcome = promotion.apply()
            plans = outcome.plans
        else:
            plans = promotion.plan()

        importable = 0

        for plan in plans:
            _render(plan)
            importable += len(plan.new)

        print()

        if apply:
            print(f"observations appended: {outcome.appended}")
        elif importable:
            print(
                f"observations that would be appended: {importable}. "
                "Nothing was written; re-run with --apply to append them."
            )
        else:
            print("Nothing to append: the target already holds all of it.")

        return 0


def _render(plan: ArtifactPlan) -> None:
    name = plan.path.name

    if plan.refused_because is not None:
        print(f"  {name}: REFUSED — {plan.refused_because}")
        return

    print(
        f"  {name}: {plan.symbol} {plan.key} — "
        f"{len(plan.new)} new, {plan.duplicates} already held"
    )

    for observation in plan.new:
        located = ", ".join(
            f"{fact.concept.value}={fact.anchor.printed}"
            for fact in observation.facts
            if fact.anchor is not None
        )
        print(
            f"      {observation.statement.value} "
            f"read {observation.reading.observed_at.isoformat()} — "
            f"{located or 'no located figures'}"
        )


def run(source: str, into: str | None, apply: bool) -> int:
    return StatementImportCommand().run(source, into, apply)
