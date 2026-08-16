"""Move statement observations between stores, without manufacturing any.

The gap this closes was measured before it was built. BQ11–BQ13 paid for
twenty readings and wrote every one to an isolated evidence root, as the
hermetic-evidence rule requires of an experiment; BQ15 then found that
nothing can carry them the last mile. `observe-statements` re-runs the
model and spends again, and copying files by hand is the manual JSON
surgery the briefs forbid. So validated evidence sat reachable by
nobody, one `/tmp` sweep from being a re-spend.

Promotion is the missing verb, and it is deliberately narrow: **moving
existing evidence between stores, never creating it.** What may travel
is a `FinancialStatementObservation` the ordinary acquisition pipeline
already produced — decoded by the store's own codec, schema-gated by the
store's own version rule, appended through the store's own door. This
module contains no extractor, no provider, no model seam, and no notion
of what any observation is worth: `tests/test_statement_promotion.py`
pins that no analytical name appears in its syntax tree, because the one
corruption promotion must be incapable of is choosing evidence for the
answer it would produce.

What travels, travels whole. Facts, anchors, rows, periods, the reading
provenance with its timestamp, the source identity — the decoded
dataclass is appended as decoded, and the fidelity test asserts the
round trip is equality. An observation equal in every field to one the
target already holds is skipped, deterministically and reported; a file
another schema wrote, or that decodes to nothing, is refused whole with
the reason worded. The source artifact is opened read-only and never
rewritten, whatever happens on the target side.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementKind,
)
from app.repositories.financial_statement_store import (
    STATEMENT_SCHEMA_VERSION,
    JsonFinancialStatementStore,
)


@dataclass(frozen=True, slots=True)
class ArtifactPlan:
    """What one source artifact would contribute, or why it cannot."""

    path: Path

    symbol: str | None
    key: str | None

    #: Observations the target does not hold, in the source's own order.
    new: tuple[FinancialStatementObservation, ...] = ()

    #: Observations equal in every field to one already in the target.
    duplicates: int = 0

    refused_because: str | None = None

    @property
    def importable(self) -> bool:
        return self.refused_because is None and bool(self.new)


@dataclass(frozen=True, slots=True)
class PromotionOutcome:
    """What an apply run actually appended, artifact by artifact."""

    plans: tuple[ArtifactPlan, ...]
    appended: int


class StatementPromotion:
    """Plan and apply the movement of observations into a target store."""

    def __init__(self, source_directory: Path, target_directory: Path) -> None:
        self._source_directory = Path(source_directory)
        self._target = JsonFinancialStatementStore(Path(target_directory))

    def plan(self) -> tuple[ArtifactPlan, ...]:
        """Every artifact in the source, and what promoting it would do.

        Read-only on both sides: the source is decoded, the target is
        read for duplicates, and nothing is written by planning.
        """

        return tuple(
            self._plan_artifact(path)
            for path in sorted(self._source_directory.glob("*.json"))
        )

    def apply(self) -> PromotionOutcome:
        """Append every importable observation through the ordinary door.

        The plan is recomputed at apply time and duplicates are
        re-checked against the growing target, so promoting a source
        that holds the same observation twice appends it once — the
        deterministic answer, not an error.
        """

        plans = []
        appended = 0

        for path in sorted(self._source_directory.glob("*.json")):
            plan = self._plan_artifact(path)
            plans.append(plan)

            for observation in plan.new:
                if self._held(observation, plan.key or ""):
                    continue

                self._target.append(observation)
                appended += 1

        return PromotionOutcome(plans=tuple(plans), appended=appended)

    # ── one artifact ────────────────────────────────────────────────

    def _plan_artifact(self, path: Path) -> ArtifactPlan:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ArtifactPlan(
                path=path,
                symbol=None,
                key=None,
                refused_because=(
                    "the artifact could not be read as JSON, so nothing in "
                    "it can be established as an observation"
                ),
            )

        symbol = payload.get("symbol")
        key = (payload.get("source") or {}).get("key")
        version = payload.get("schema_version")

        if not symbol or not key:
            return ArtifactPlan(
                path=path,
                symbol=symbol,
                key=key,
                refused_because=(
                    "the artifact names no symbol or no source document, so "
                    "whose evidence it is cannot be established"
                ),
            )

        if version != STATEMENT_SCHEMA_VERSION:
            return ArtifactPlan(
                path=path,
                symbol=symbol,
                key=key,
                refused_because=(
                    f"the artifact was written by schema {version} and this "
                    f"platform appends schema {STATEMENT_SCHEMA_VERSION}; a "
                    "reading taken under another contract is re-observed, "
                    "never imported"
                ),
            )

        source_store = JsonFinancialStatementStore(path.parent)

        decoded = tuple(
            observation
            for kind in StatementKind
            for observation in source_store.read(symbol, key, kind)
        )

        if not decoded:
            return ArtifactPlan(
                path=path,
                symbol=symbol,
                key=key,
                refused_because=(
                    "the artifact decodes to no observation under the "
                    "store's own codec, so there is nothing to promote"
                ),
            )

        new = tuple(
            observation
            for observation in decoded
            if not self._held(observation, key)
        )

        return ArtifactPlan(
            path=path,
            symbol=symbol,
            key=key,
            new=new,
            duplicates=len(decoded) - len(new),
        )

    def _held(self, observation: FinancialStatementObservation, key: str) -> bool:
        """Whether the target already holds this exact observation.

        Equality over the whole frozen dataclass — every fact, every
        cell, the reading's own timestamp, the supersession state. Two
        readings of one filing that found the same figures at different
        moments are two observations and both belong; only a record
        identical in all of it is the same record twice.
        """

        existing = self._target.read(observation.symbol, key, observation.statement)

        return any(held == observation for held in existing)
