"""Move statement observations between stores, without manufacturing any.

The gap this closes was measured before it was built. BQ11–BQ13 paid for
twenty readings and wrote every one to an isolated evidence root, as the
hermetic-evidence rule requires of an experiment; BQ15 then found that
nothing can carry them the last mile. `observe-statements` re-runs the
model and spends again, and copying files by hand is the manual JSON
surgery the briefs forbid. So validated evidence sat reachable by
nobody, one `/tmp` sweep from being a re-spend.

Promotion is the missing verb, and it is deliberately narrow: **moving
existing evidence between stores, never creating it.** This module
contains no extractor, no provider, no model seam, and no notion of what
any observation is worth: `tests/test_statement_promotion.py` pins that
no analytical name appears in its syntax tree, because the one
corruption promotion must be incapable of is choosing evidence for the
answer it would produce.

## Same schema is not same contract

The first cut of this module gated on `STATEMENT_SCHEMA_VERSION` alone,
and BQ16's own measurement refuted it: schema 3 contains observations
produced under materially different semantic contracts. A BQ8 reading of
Coca-Cola recorded *"no figure located for total_revenue"* under a
vocabulary that refused `Net Operating Revenues`; BQ11 widened the
vocabulary by exactly that form, under no schema bump; five later
readings of the same filing locate the figure. Both decode identically.
Pooling them makes a contract difference vote as a disagreement —
measured: the one stale absence turns an honest 5-vs-5 tie into a
6-of-11 settled absence.

So deserialization is admission to *inspection*, never to a consensus.
An observation is appendable only when its compatibility with today's
contract is **proven**, and the proof has two parts:

- **What the record itself can prove.** A located anchor's label is
  checkable against today's `matches_concept` — a label today's
  vocabulary refuses is a claim today's contract would not accept.
- **What only testimony can prove.** An *absence* — "no figure located
  for X" — is a claim about the producing vocabulary, and the record
  does not carry which vocabulary that was. A promotion manifest beside
  the artifacts records an operator's evidence-backed ruling: the
  artifact's hash, and per concept the fingerprint of the vocabulary it
  was produced under. An absence is compatible only where that
  fingerprint equals today's for that concept; the historical record is
  never retro-stamped — the manifest is a ruling *about* it, tied to
  its bytes.

Anything unproven is refused. That is the default the whole platform
runs on: not knowing is never treated as knowing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementKind,
    concept_vocabulary_fingerprint,
    matches_concept,
)
from app.repositories.financial_statement_store import (
    STATEMENT_SCHEMA_VERSION,
    JsonFinancialStatementStore,
)

#: The operator's compatibility rulings, beside the artifacts they rule.
MANIFEST_NAME = "promotion-manifest.json"


class ImportRuling(StrEnum):
    """What the importer may do with one observation, and why."""

    #: Proven compatible with today's contract, and not already held.
    COMPATIBLE = "compatible"

    #: Equal in every field to an observation the target already holds.
    DUPLICATE = "duplicate"

    #: Proven incompatible: a located label today's vocabulary refuses,
    #: or an absence produced under a vocabulary that differs from
    #: today's for that concept.
    INCOMPATIBLE = "incompatible"

    #: Nothing proves compatibility either way. Refused, by default:
    #: not knowing is not knowing.
    UNPROVEN = "compatibility unproven"


@dataclass(frozen=True, slots=True)
class ObservationRuling:
    """One observation's import ruling, carried with its identity."""

    statement: StatementKind
    position: int
    observed_at: str

    ruling: ImportRuling
    because: str | None = None

    #: The located figures, for the dry-run listing.
    located: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactPlan:
    """What one source artifact would contribute, or why it cannot."""

    path: Path

    symbol: str | None
    key: str | None

    rulings: tuple[ObservationRuling, ...] = ()

    refused_because: str | None = None

    def counted(self, ruling: ImportRuling) -> int:
        return sum(1 for ruled in self.rulings if ruled.ruling is ruling)


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
        self._manifest = self._read_manifest()

    def plan(self) -> tuple[ArtifactPlan, ...]:
        """Every artifact in the source, and what promoting it would do.

        Read-only on both sides: the source is decoded, the target is
        read for duplicates, and nothing is written by planning.
        """

        return tuple(
            self._plan_artifact(path)
            for path in sorted(self._source_directory.glob("*.json"))
            if path.name != MANIFEST_NAME
        )

    def apply(self) -> PromotionOutcome:
        """Append every proven-compatible observation through the ordinary door.

        The plan is recomputed at apply time and duplicates re-checked
        against the growing target, so promoting a source that holds
        the same observation twice appends it once — the deterministic
        answer, not an error.
        """

        plans = []
        appended = 0

        for path in sorted(self._source_directory.glob("*.json")):
            if path.name == MANIFEST_NAME:
                continue

            plan = self._plan_artifact(path)
            plans.append(plan)

            if plan.refused_because is not None:
                continue

            observations = self._decode(path, plan.symbol or "", plan.key or "")

            for ruled, observation in zip(plan.rulings, observations, strict=True):
                if ruled.ruling is not ImportRuling.COMPATIBLE:
                    continue

                if self._held(observation, plan.key or ""):
                    continue

                self._target.append(observation)
                appended += 1

        return PromotionOutcome(plans=tuple(plans), appended=appended)

    # ── one artifact ────────────────────────────────────────────────

    def _plan_artifact(self, path: Path) -> ArtifactPlan:
        try:
            raw = path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
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

        ruled_under = self._manifest.get(path.name)

        if ruled_under is not None:
            recorded = str(ruled_under.get("sha256", ""))

            if recorded != sha256(raw).hexdigest():
                return ArtifactPlan(
                    path=path,
                    symbol=symbol,
                    key=key,
                    refused_because=(
                        "the artifact does not match the manifest's hash — "
                        "it changed after the compatibility ruling, so the "
                        "ruling no longer speaks for it"
                    ),
                )

        observations = self._decode(path, symbol, key)

        if not observations:
            return ArtifactPlan(
                path=path,
                symbol=symbol,
                key=key,
                refused_because=(
                    "the artifact decodes to no observation under the "
                    "store's own codec, so there is nothing to promote"
                ),
            )

        rulings = tuple(
            self._rule(observation, position, key, ruled_under)
            for position, observation in enumerate(observations)
        )

        return ArtifactPlan(path=path, symbol=symbol, key=key, rulings=rulings)

    def _rule(
        self,
        observation: FinancialStatementObservation,
        position: int,
        key: str,
        ruled_under: dict[str, object] | None,
    ) -> ObservationRuling:
        """One observation against today's contract, worst answer first."""

        located = ", ".join(
            f"{fact.concept.value}={fact.anchor.printed}"
            for fact in observation.facts
            if fact.anchor is not None
        )

        def ruled(
            ruling: ImportRuling, because: str | None = None
        ) -> ObservationRuling:
            return ObservationRuling(
                statement=observation.statement,
                position=position,
                observed_at=observation.reading.observed_at.isoformat(),
                ruling=ruling,
                because=because,
                located=located,
            )

        if self._held(observation, key):
            return ruled(ImportRuling.DUPLICATE)

        # What the record itself proves: a located label today's
        # vocabulary refuses is a claim today's contract would not make.
        for fact in observation.facts:
            if fact.anchor is None:
                continue

            if not matches_concept(fact.concept, fact.anchor.label):
                return ruled(
                    ImportRuling.INCOMPATIBLE,
                    because=(
                        f"the reading locates {fact.concept.value} on the "
                        f"label {fact.anchor.label!r}, which today's "
                        "vocabulary does not accept"
                    ),
                )

        # What only testimony proves: which vocabulary an absence was
        # produced under. No ruling, no entry, no fingerprint — refused.
        absent = tuple(
            fact.concept for fact in observation.facts if fact.anchor is None
        )

        if ruled_under is None:
            return ruled(
                ImportRuling.UNPROVEN,
                because=(
                    "no manifest entry rules this artifact's producing "
                    "contract, and an observation's own record cannot prove "
                    "which vocabulary its absences were read under"
                ),
            )

        produced = ruled_under.get("produced_under")
        fingerprints = produced if isinstance(produced, dict) else {}

        for concept in absent:
            recorded = fingerprints.get(concept.value)

            if recorded is None:
                return ruled(
                    ImportRuling.UNPROVEN,
                    because=(
                        f"the manifest records no producing vocabulary for "
                        f"{concept.value}, whose absence this reading claims"
                    ),
                )

            if recorded != concept_vocabulary_fingerprint(concept):
                return ruled(
                    ImportRuling.INCOMPATIBLE,
                    because=(
                        f"the reading records no figure for {concept.value} "
                        "under a vocabulary that differs from today's for "
                        "that concept, so the absence is a claim about a "
                        "contract this platform no longer reads under"
                    ),
                )

        return ruled(ImportRuling.COMPATIBLE)

    # ── plumbing ────────────────────────────────────────────────────

    def _read_manifest(self) -> dict[str, dict[str, object]]:
        path = self._source_directory / MANIFEST_NAME

        if not path.exists():
            return {}

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        artifacts = payload.get("artifacts")

        return artifacts if isinstance(artifacts, dict) else {}

    def _decode(
        self, path: Path, symbol: str, key: str
    ) -> tuple[FinancialStatementObservation, ...]:
        source_store = JsonFinancialStatementStore(path.parent)

        return tuple(
            observation
            for kind in StatementKind
            for observation in source_store.read(symbol, key, kind)
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
