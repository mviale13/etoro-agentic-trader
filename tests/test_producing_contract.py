"""An observation records the contract that produced it, not the one reading it.

BQ16 could only rule on the historical corpus through an operator's
authored testimony, because the records carried no trace of which labels
their reader was permitted to accept. BQ17 stamps that at acquisition.
The whole value of the stamp is that it describes the producer — so the
tests that matter most are the ones proving it does not drift: an old
record opened under a new vocabulary must keep saying what it said, and
compatibility must see A against B rather than merely seeing one schema.

And the fingerprint is per *concept*, which only earns its keep if a
change to one concept's vocabulary leaves the others alone. That is the
last case below, and it is the reason the design is not one hash.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from app.domain.financial_statements import (
    CONCEPT_LABELS,
    ConceptContract,
    StatementConcept,
    StatementKind,
    concept_vocabulary_fingerprint,
    producing_contract,
    vocabulary_fingerprints,
)
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.statement_promotion import ImportRuling, StatementPromotion
from tests.test_financial_statement_store import ACCESSION, observation

INCOME = StatementKind.INCOME_STATEMENT

#: The fixture observation locates total_revenue and records net_income
#: absent, so these two concepts exercise both halves of the rule.
LOCATED = StatementConcept.TOTAL_REVENUE
ABSENT = StatementConcept.NET_INCOME

#: A concept the mutation below never touches, for the per-concept case.
UNTOUCHED = StatementConcept.GROSS_PROFIT


def widen(monkeypatch, concept: StatementConcept) -> str:
    """Change one concept's accepted vocabulary; return the new fingerprint.

    A real widening, in the shape `6c96ea0` had: one more accepted form
    for one concept, everything else untouched.
    """

    monkeypatch.setitem(
        CONCEPT_LABELS,
        concept,
        (*CONCEPT_LABELS[concept], "a form no filer has ever printed"),
    )

    return concept_vocabulary_fingerprint(concept)


def stamped(**changes) -> object:
    """The store fixture's observation, stamped as acquisition would."""

    return dataclasses.replace(
        observation(),
        produced_under=producing_contract(INCOME),
        **changes,
    )


# ── the identity ────────────────────────────────────────────────────


def test_the_stamp_covers_every_concept_the_statement_asks() -> None:
    """Every concept, derived from the contract rather than listed here.

    Listed, this test asserted a snapshot of the vocabulary and failed the
    next time a concept was added — which is the opposite of what it is
    for. What it must guarantee is that the stamp covers *whatever* the
    statement asks, so it reads the same function the extractor does.
    """

    from app.domain.financial_statements import concepts_of

    stamp = producing_contract(INCOME)

    assert {contract.concept for contract in stamp} == set(concepts_of(INCOME))

    # And the three the rest of this file exercises are among them.
    assert {LOCATED, ABSENT, UNTOUCHED} <= {contract.concept for contract in stamp}

    # Fingerprints, never the forms: the vocabulary itself is not copied
    # into every observation of every company.
    for contract in stamp:
        assert contract.fingerprint == concept_vocabulary_fingerprint(contract.concept)
        assert len(contract.fingerprint) == 16


def test_a_statement_is_stamped_only_with_the_concepts_it_is_asked() -> None:
    balance = {c.concept for c in producing_contract(StatementKind.BALANCE_SHEET)}

    assert LOCATED not in balance
    assert StatementConcept.TOTAL_EQUITY in balance


# ── the mutation: A, then B ─────────────────────────────────────────


def test_a_stored_stamp_is_never_rewritten_by_a_later_vocabulary(
    tmp_path: Path, monkeypatch
) -> None:
    """The four properties the brief names, proved together."""

    store = JsonFinancialStatementStore(tmp_path)

    before = concept_vocabulary_fingerprint(ABSENT)
    store.append(stamped())

    untouched_before = concept_vocabulary_fingerprint(UNTOUCHED)

    # The contract moves under the record's feet.
    after = widen(monkeypatch, ABSENT)

    assert after != before, "the mutation must actually change the fingerprint"

    restored = store.read("JPM", ACCESSION, INCOME)[0]

    # 1. the stored observation still says A
    assert restored.produced_contract_for(ABSENT) == before
    assert restored.produced_contract_for(ABSENT) != after

    # 2. rereading it does not mutate it
    on_disk = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    written = on_disk["observations"][0]["produced_under"]

    assert written[ABSENT.value] == before

    again = store.read("JPM", ACCESSION, INCOME)[0]

    assert again == restored

    # 4. a concept whose vocabulary did not change is untouched
    assert restored.produced_contract_for(UNTOUCHED) == untouched_before
    assert concept_vocabulary_fingerprint(UNTOUCHED) == untouched_before


def test_compatibility_sees_a_against_b_rather_than_one_schema(
    tmp_path: Path, monkeypatch
) -> None:
    """3. compatibility reads the contracts, not the schema version."""

    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    JsonFinancialStatementStore(source).append(stamped())

    # Same schema on both sides, throughout.
    compatible = StatementPromotion(source, target).plan()[0]

    assert compatible.counted(ImportRuling.COMPATIBLE) == 1

    widen(monkeypatch, ABSENT)

    ruled = StatementPromotion(source, target).plan()[0]

    assert ruled.counted(ImportRuling.INCOMPATIBLE) == 1
    assert ruled.rulings[0].because is not None
    assert "the reading records no figure" in ruled.rulings[0].because
    assert StatementPromotion(source, target).apply().appended == 0


def test_a_change_to_another_concept_does_not_make_a_reading_incompatible(
    tmp_path: Path, monkeypatch
) -> None:
    """The per-concept case, and the reason this is not one global hash."""

    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    JsonFinancialStatementStore(source).append(stamped())

    # A concept this reading located, and one it never mentions: neither
    # is the absence its compatibility turns on.
    widen(monkeypatch, UNTOUCHED)
    widen(monkeypatch, StatementConcept.TOTAL_CURRENT_ASSETS)

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.COMPATIBLE) == 1
    assert StatementPromotion(source, target).apply().appended == 1


# ── native versus historical ────────────────────────────────────────


def test_a_native_stamp_needs_no_manifest(tmp_path: Path) -> None:
    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    JsonFinancialStatementStore(source).append(stamped())

    assert not (source / "promotion-manifest.json").exists()
    assert StatementPromotion(source, target).apply().appended == 1


def test_an_unstamped_reading_still_needs_the_manifest(tmp_path: Path) -> None:
    """The BQ16 bridge is intact for records that predate the stamp."""

    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    JsonFinancialStatementStore(source).append(observation())

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.UNPROVEN) == 1
    assert plan.rulings[0].because is not None
    assert "no producing contract" in plan.rulings[0].because


def test_the_record_answers_for_itself_before_any_testimony(
    tmp_path: Path, monkeypatch
) -> None:
    """A manifest may not overrule an observation that carries its own stamp.

    The manifest here says today's vocabulary produced the reading; the
    reading itself says otherwise. The record wins, and is refused.
    """

    source = tmp_path / "isolated" / "statements"
    target = tmp_path / "production" / "statements"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    JsonFinancialStatementStore(source).append(stamped())

    widen(monkeypatch, ABSENT)

    artifact = next(source.glob("*.json"))
    (source / "promotion-manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "artifacts": {
                    artifact.name: {
                        "sha256": __import__("hashlib")
                        .sha256(artifact.read_bytes())
                        .hexdigest(),
                        "produced_under": vocabulary_fingerprints(),
                        "evidence": "testimony that contradicts the record",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    plan = StatementPromotion(source, target).plan()[0]

    assert plan.counted(ImportRuling.INCOMPATIBLE) == 1
    assert plan.rulings[0].because is not None
    assert plan.rulings[0].because.startswith("the reading")


# ── the store round trip ────────────────────────────────────────────


def test_an_unstamped_entry_encodes_without_the_field(tmp_path: Path) -> None:
    """No migration: a store of unstamped readings is byte-identical."""

    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())

    written = next(tmp_path.glob("*.json")).read_text(encoding="utf-8")

    assert "produced_under" not in written


def test_a_stamp_round_trips_to_equality(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)

    original = stamped()
    store.append(original)

    assert store.read("JPM", ACCESSION, INCOME)[0] == original


def test_appending_beside_an_unstamped_reading_leaves_it_unstamped(
    tmp_path: Path,
) -> None:
    """A new reading does not backfill the ones already in the file."""

    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())
    store.append(stamped())

    held = store.read("JPM", ACCESSION, INCOME)

    assert held[0].produced_under == ()
    assert held[1].produced_under == producing_contract(INCOME)


def test_a_stamp_decodes_to_the_recorded_concepts(tmp_path: Path) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(
        dataclasses.replace(
            observation(),
            produced_under=(ConceptContract(concept=ABSENT, fingerprint="abc123"),),
        )
    )

    restored = store.read("JPM", ACCESSION, INCOME)[0]

    assert restored.produced_contract_for(ABSENT) == "abc123"
    assert restored.produced_contract_for(LOCATED) is None


# ── why it cannot drift ─────────────────────────────────────────────


def test_only_acquisition_generates_a_producing_contract() -> None:
    """The generator is reachable from the extractor and nowhere else.

    This is the structural half of "provenance describes the producer".
    `producing_contract` reads the live `CONCEPT_LABELS`, which is
    correct exactly once — at the instant of reading — and wrong
    everywhere else. A store or consensus that called it would stamp
    every old record with whatever is running now.
    """

    callers = {
        path
        for path in Path("app").rglob("*.py")
        if "__pycache__" not in str(path)
        and "producing_contract(" in path.read_text(encoding="utf-8")
    }

    assert callers == {
        Path("app/domain/financial_statements.py"),  # where it is defined
        Path("app/services/financial_statement_extractor.py"),  # acquisition
    }


def test_the_store_never_computes_a_fingerprint() -> None:
    """Decoding reads what was written; it never asks today's vocabulary."""

    source = Path("app/repositories/financial_statement_store.py").read_text(
        encoding="utf-8"
    )

    assert "concept_vocabulary_fingerprint" not in source
    assert "producing_contract" not in source
    assert "vocabulary_fingerprints" not in source
