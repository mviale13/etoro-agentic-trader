"""Promotion moves observations whole, refuses what it cannot verify, creates nothing.

The invariant under test: an observation may enter another store only as
the record it already is — every fact, anchor, period and timestamp
surviving equality-checked — and never because of what it would do to a
quality answer, which the module is pinned to be unable to see.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path

from app.domain.financial_statements import StatementKind
from app.repositories.financial_statement_store import (
    STATEMENT_SCHEMA_VERSION,
    JsonFinancialStatementStore,
)
from app.services import statement_promotion
from app.services.statement_promotion import StatementPromotion
from tests.test_financial_statement_service import ACCESSION, observation
from tests.test_financial_statement_store import observation as other_filing

INCOME = StatementKind.INCOME_STATEMENT


def stores(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    return source, target


# ── movement ────────────────────────────────────────────────────────


def test_an_observation_travels_whole_and_round_trips_to_equality(
    tmp_path: Path,
) -> None:
    source, target = stores(tmp_path)

    original = observation()
    JsonFinancialStatementStore(source).append(original)

    outcome = StatementPromotion(source, target).apply()

    assert outcome.appended == 1

    landed = JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)

    assert len(landed) == 1
    assert landed[0] == original, "every field survives, or nothing moved"


def test_the_source_artifact_is_never_rewritten(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())

    artifact = next(source.glob("*.json"))
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

    StatementPromotion(source, target).apply()

    assert target_store.read("JPM", ACCESSION, INCOME) == held_before


# ── duplicates ──────────────────────────────────────────────────────


def test_an_exact_duplicate_is_skipped_and_reported(tmp_path: Path) -> None:
    source, target = stores(tmp_path)

    same = observation()
    JsonFinancialStatementStore(source).append(same)
    JsonFinancialStatementStore(target).append(same)

    promotion = StatementPromotion(source, target)

    plan = promotion.plan()[0]

    assert plan.duplicates == 1
    assert not plan.new

    outcome = promotion.apply()

    assert outcome.appended == 0
    assert len(JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)) == 1


def test_applying_twice_appends_once(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())

    promotion = StatementPromotion(source, target)

    assert promotion.apply().appended == 1
    assert promotion.apply().appended == 0
    assert len(JsonFinancialStatementStore(target).read("JPM", ACCESSION, INCOME)) == 1


# ── refusals ────────────────────────────────────────────────────────


def test_an_artifact_from_another_schema_is_refused_whole(tmp_path: Path) -> None:
    source, target = stores(tmp_path)
    JsonFinancialStatementStore(source).append(observation())

    artifact = next(source.glob("*.json"))
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["schema_version"] = STATEMENT_SCHEMA_VERSION + 1
    artifact.write_text(json.dumps(payload), encoding="utf-8")

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
