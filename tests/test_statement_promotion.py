"""Promotion moves observations whole, and only under a proven contract.

Two invariants under test. An observation may enter another store only
as the record it already is — every fact, anchor, period and timestamp
surviving equality-checked. And it may enter only where its
compatibility with today's semantic contract is proven: same schema is
not same contract, deserialization is admission to inspection and never
to a consensus, and two observations produced under the same contract
receive the same ruling whatever conclusion their figures support.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
from hashlib import sha256
from pathlib import Path

from app.domain.financial_statements import (
    StatementConcept,
    StatementFact,
    StatementKind,
    vocabulary_fingerprints,
)
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import (
    STATEMENT_SCHEMA_VERSION,
    JsonFinancialStatementStore,
)
from app.services import statement_promotion
from app.services.statement_promotion import (
    MANIFEST_NAME,
    ImportRuling,
    StatementPromotion,
)
from tests.test_financial_statement_service import ACCESSION, observation
from tests.test_financial_statement_store import observation as other_filing

INCOME = StatementKind.INCOME_STATEMENT

#: A vocabulary identity that is not today's, for any concept.
ANOTHER_CONTRACT = "0000000000000000"


def stores(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    return source, target


def manifested(source: Path, produced_under: dict[str, str] | None = None) -> None:
    """Write the operator ruling for whatever the source now holds.

    Called after any mutation a test performs, because the manifest ties
    its ruling to the artifact's exact bytes.
    """

    fingerprints = produced_under or vocabulary_fingerprints()

    artifacts = {
        artifact.name: {
            "sha256": sha256(artifact.read_bytes()).hexdigest(),
            "produced_under": fingerprints,
            "evidence": "test ruling",
        }
        for artifact in sorted(source.glob("*.json"))
        if artifact.name != MANIFEST_NAME
    }

    (source / MANIFEST_NAME).write_text(
        json.dumps({"manifest_version": 1, "artifacts": artifacts}),
        encoding="utf-8",
    )


# ── movement ────────────────────────────────────────────────────────


def test_an_observation_travels_whole_and_round_trips_to_equality(
    tmp_path: Path,
) -> None:
    source, target = stores(tmp_path)

    original = observation()
    JsonFinancialStatementStore(source).append(original)
    manifested(source)

    outcome = StatementPromotion(source, target).apply()

    assert outcome.appended == 1

    landed = JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)

    assert len(landed) == 1
    assert landed[0] == original, "every field survives, or nothing moved"


def test_the_source_artifact_is_never_rewritten(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())
    manifested(source)

    artifact = next(
        path for path in source.glob("*.json") if path.name != MANIFEST_NAME
    )
    before = artifact.read_bytes()

    StatementPromotion(source, target).apply()

    assert artifact.read_bytes() == before


def test_existing_target_observations_are_never_rewritten(tmp_path: Path) -> None:
    source, target = stores(tmp_path)

    target_store = JsonFinancialStatementStore(target)
    target_store.append(observation())
    held_before = target_store.read("JPM", ACCESSION, INCOME)

    JsonFinancialStatementStore(source).append(
        other_filing(key="0000019617-26-000200")
    )
    manifested(source)

    StatementPromotion(source, target).apply()

    assert target_store.read("JPM", ACCESSION, INCOME) == held_before


# ── duplicates ──────────────────────────────────────────────────────


def test_an_exact_duplicate_is_skipped_and_reported(tmp_path: Path) -> None:
    source, target = stores(tmp_path)

    same = observation()
    JsonFinancialStatementStore(source).append(same)
    JsonFinancialStatementStore(target).append(same)
    manifested(source)

    promotion = StatementPromotion(source, target)

    plan = promotion.plan()[0]

    assert plan.counted(ImportRuling.DUPLICATE) == 1
    assert plan.counted(ImportRuling.COMPATIBLE) == 0

    outcome = promotion.apply()

    assert outcome.appended == 0
    assert len(JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)) == 1


def test_applying_twice_appends_once(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())
    manifested(source)

    promotion = StatementPromotion(source, target)

    assert promotion.apply().appended == 1
    assert promotion.apply().appended == 0
    assert len(JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)) == 1


# ── the contract gate ───────────────────────────────────────────────


def test_a_valid_store_without_a_manifest_is_unproven_and_refused(
    tmp_path: Path,
) -> None:
    """Deserialization succeeding is not authority to enter a consensus."""

    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())

    promotion = StatementPromotion(source, target)

    plan = promotion.plan()[0]

    assert plan.counted(ImportRuling.UNPROVEN) == 1
    assert plan.rulings[0].because is not None
    assert "manifest" in plan.rulings[0].because
    assert promotion.apply().appended == 0


def test_an_artifact_that_changed_after_its_ruling_is_refused_whole(
    tmp_path: Path,
) -> None:
    source, target = stores(tmp_path)

    store = JsonFinancialStatementStore(source)
    store.append(observation())
    manifested(source)
    store.append(observation())  # the artifact's bytes moved

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.refused_because is not None
    assert "does not match the manifest's hash" in plan.refused_because
    assert StatementPromotion(source, target).apply().appended == 0


def test_an_absence_under_a_changed_vocabulary_is_incompatible(
    tmp_path: Path,
) -> None:
    """The BQ8 shape: an absence read under a narrower vocabulary.

    The fixture observation records net_income as absent, so a manifest
    whose producing fingerprint for net_income differs from today's
    proves the absence belongs to another contract.
    """

    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(other_filing())

    fingerprints = dict(vocabulary_fingerprints())
    fingerprints["net_income"] = ANOTHER_CONTRACT
    manifested(source, produced_under=fingerprints)

    promotion = StatementPromotion(source, target)

    plan = promotion.plan()[0]

    assert plan.counted(ImportRuling.INCOMPATIBLE) == 1
    assert plan.rulings[0].because is not None
    assert "no figure for net_income" in plan.rulings[0].because
    assert promotion.apply().appended == 0


def test_an_absence_under_todays_vocabulary_is_compatible(tmp_path: Path) -> None:
    """The same observation, ruled produced under today's contract, moves."""

    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(other_filing())
    manifested(source)

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.COMPATIBLE) == 1


def test_a_manifest_silent_on_an_absent_concept_is_unproven(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(other_filing())

    fingerprints = dict(vocabulary_fingerprints())
    del fingerprints["net_income"]
    manifested(source, produced_under=fingerprints)

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.UNPROVEN) == 1


def test_a_located_label_todays_vocabulary_refuses_is_incompatible(
    tmp_path: Path,
) -> None:
    """A record can refute its own compatibility without any manifest."""

    source, target = stores(tmp_path)

    renamed = ReportedFigure(
        label="A label no vocabulary accepts",
        column_header="2025",
        printed="177,419",
        value=177419.0,
        cell=CellReference(table=0, row=1, column=1),
        caption="(in millions)",
    )
    original = observation()
    rewritten = dataclasses.replace(
        original,
        facts=(
            dataclasses.replace(original.facts[0], anchor=renamed, row=(renamed,)),
        ),
    )
    JsonFinancialStatementStore(source).append(rewritten)
    manifested(source)

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.INCOMPATIBLE) == 1
    assert plan.rulings[0].because is not None
    assert "today's" in plan.rulings[0].because


def test_the_same_contract_earns_the_same_ruling_whatever_the_figures_say(
    tmp_path: Path,
) -> None:
    """Eligibility follows the contract, never the conclusion.

    Two readings under one manifest: one whose revenue rose against the
    prior period, one whose revenue collapsed. If eligibility could see
    what the figures imply, these would part ways; they must not.
    """

    source, target = stores(tmp_path)

    def anchored(current: str, value: float):
        anchor = ReportedFigure(
            label="Total net revenue",
            column_header="2025",
            printed=current,
            value=value,
            cell=CellReference(table=0, row=1, column=1),
            caption="(in millions)",
        )
        earlier = ReportedFigure(
            label="Total net revenue",
            column_header="2024",
            printed="162,878",
            value=162878.0,
            cell=CellReference(table=0, row=1, column=2),
            caption="(in millions)",
        )
        base = observation()
        return dataclasses.replace(
            base,
            facts=(
                StatementFact(
                    concept=StatementConcept.TOTAL_REVENUE,
                    anchor=anchor,
                    row=(anchor, earlier),
                ),
                *base.facts[1:],
            ),
        )

    flattering = anchored("999,999", 999999.0)
    adverse = anchored("1", 1.0)

    store = JsonFinancialStatementStore(source)
    store.append(flattering)
    store.append(adverse)
    manifested(source)

    plan = StatementPromotion(source, target).plan()[0]

    assert [ruled.ruling for ruled in plan.rulings] == [
        ImportRuling.COMPATIBLE,
        ImportRuling.COMPATIBLE,
    ]


# ── refusals ────────────────────────────────────────────────────────


def test_an_artifact_from_another_schema_is_refused_whole(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())

    artifact = next(
        path for path in source.glob("*.json") if path.name != MANIFEST_NAME
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["schema_version"] = STATEMENT_SCHEMA_VERSION + 1
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    manifested(source)

    promotion = StatementPromotion(source, target)

    plan = promotion.plan()[0]

    assert plan.refused_because is not None
    assert "re-observed, never imported" in plan.refused_because
    assert promotion.apply().appended == 0


def test_an_unreadable_artifact_is_refused_whole(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    (source / "JPM.BROKEN.json").write_text("{not json", encoding="utf-8")

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.refused_because is not None
    assert StatementPromotion(source, target).apply().appended == 0


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())
    manifested(source)

    StatementPromotion(source, target).plan()

    assert not list(target.glob("*.json"))


# ── the module cannot see an answer ─────────────────────────────────

FORBIDDEN = frozenset(
    {
        "BusinessQuality",
        "QualityBand",
        "quality_of",
        "band",
        "band_for",
        "score",
        "favourable",
        "adverse",
        "sense_of",
        "FinancialUnderstanding",
        "financial_engine",
        "answer_questions",
        "assess",
        "consensus_of",
        "statement_consensus_of",
        "recommendation",
        "decide",
    }
)


def test_promotion_cannot_read_an_analytical_outcome() -> None:
    tree = ast.parse(inspect.getsource(statement_promotion))
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.update(node.name.split("."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.update(node.module.split("."))

    assert not names & FORBIDDEN, sorted(names & FORBIDDEN)


def test_promotion_never_observes_or_fetches() -> None:
    tree = ast.parse(inspect.getsource(statement_promotion))

    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert not called & {"observe", "extract", "fetch", "resolve", "statements"}
