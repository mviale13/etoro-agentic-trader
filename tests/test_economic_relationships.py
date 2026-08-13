"""Business Economic Relationships (ED1).

Revenue diversity is not driver diversity: a filer can state that one
of its businesses exists essentially to support another, and until this
slice the platform had nowhere to put that sentence. The relationship
is established only from explicit filer statements — never inferred
from names, intersegment revenue, or business logic — the filer's
degree of claim travels intact, absence stays an evidence state, and
nothing about it can reach a decision.
"""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime

from app.domain.company_knowledge import (
    CompanyKnowledgeObservation,
    EconomicRelationship,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.provenance import Provenance
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.company_knowledge_extractor import (
    RELATIONSHIP_SYSTEM_PROMPT,
    CompanyKnowledgeExtractor,
    faithful_quantifier,
)
from app.services.understanding_engine import understand
from tests.test_supplemental_description_reading import (
    ScriptedProvider,
    source_document,
)

RELATIONSHIP = EconomicRelationship(
    dependent="Financial Arm",
    driver="deliveries of the group's vehicles",
    statement=(
        "predominantly supports the sale of the group's vehicles; "
        "deliveries are stated as a decisive driver of new contracts"
    ),
    quoted="liegt im Wesentlichen in der Vertriebsunterstützung",
)


# ── the quantifier guard (requirement 7) ──────────────────────────────


def test_a_qualified_claim_may_not_harden_into_an_absolute() -> None:
    assert not faithful_quantifier(
        "depends entirely on vehicle sales",
        "liegt im Wesentlichen in der Vertriebsunterstützung",
    )


def test_an_absolute_the_filer_stated_is_allowed() -> None:
    assert faithful_quantifier(
        "depends entirely on vehicle sales",
        "hängt ausschließlich vom Absatz ab",
    )


def test_a_qualified_statement_passes_untouched() -> None:
    assert faithful_quantifier(
        "predominantly supports the sale of the group's vehicles",
        "liegt im Wesentlichen in der Vertriebsunterstützung",
    )


# ── extraction: explicit evidence only ────────────────────────────────

PRIMARY = {
    "description": "An industrial group.",
    "segments": [
        {
            "name": "Alpha Division",
            "revenue_models": ["manufacturing"],
            "quoted": "conçoit et vend des turbines industrielles",
        },
        {
            "name": "Financial Arm",
            "revenue_models": ["financial_spread"],
            "quoted": "fournit des services de maintenance sous contrat",
        },
    ],
}

#: The relationship evidence, printed in the untagged prose beside the
#: descriptions the E1 fixtures already use.
PROSE = (
    "Rapport de gestion. La division Alpha Division conçoit et vend des "
    "turbines industrielles aux compagnies d'électricité. La division "
    "Financial Arm fournit des services de maintenance sous contrat. "
    "Le modèle économique de Financial Arm consiste essentiellement à "
    "soutenir les ventes de la division Alpha Division."
)


def extract_with(relationship_payload: object):
    provider = ScriptedProvider(
        [
            PRIMARY,
            relationship_payload,
        ]
    )

    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract(
            "EXAM.PA",
            # The description spans ground in the tagged text itself, so
            # the primary pass needs no repair and the request sequence
            # is exactly: the extraction, then the relationship ask.
            replace(source_document(""), business_description=PROSE),
        )
    )

    return knowledge, provider


def test_a_stated_relationship_is_read_grounded_and_kept() -> None:
    knowledge, provider = extract_with(
        {
            "relationships": [
                {
                    "dependent": "Financial Arm",
                    "driver": "sales of the Alpha Division",
                    "statement": (
                        "consists essentially in supporting sales of the Alpha Division"
                    ),
                    "quoted": ("consiste essentiellement à soutenir les ventes"),
                }
            ]
        }
    )

    assert len(knowledge.relationships) == 1
    assert knowledge.relationships[0].dependent == "Financial Arm"
    assert "essentially" in knowledge.relationships[0].statement
    assert provider.requests[-1].system_prompt == RELATIONSHIP_SYSTEM_PROMPT


def test_an_unknown_dependent_is_dropped() -> None:
    knowledge, _ = extract_with(
        {
            "relationships": [
                {
                    "dependent": "Leasing",  # not an established segment
                    "driver": "sales of the Alpha Division",
                    "statement": "supports sales",
                    "quoted": "consiste essentiellement à soutenir les ventes",
                }
            ]
        }
    )

    assert knowledge.relationships == ()


def test_a_hardened_quantifier_is_refused_by_the_validator() -> None:
    knowledge, _ = extract_with(
        {
            "relationships": [
                {
                    "dependent": "Financial Arm",
                    "driver": "sales of the Alpha Division",
                    "statement": ("depends entirely on sales of the Alpha Division"),
                    "quoted": ("consiste essentiellement à soutenir les ventes"),
                }
            ]
        }
    )

    assert knowledge.relationships == ()


def test_a_span_the_text_does_not_print_is_refused() -> None:
    knowledge, _ = extract_with(
        {
            "relationships": [
                {
                    "dependent": "Financial Arm",
                    "driver": "sales of the Alpha Division",
                    "statement": "essentially supports sales",
                    "quoted": "exists to support the industrial business",
                }
            ]
        }
    )

    assert knowledge.relationships == ()


def test_an_empty_answer_is_the_ordinary_state() -> None:
    knowledge, _ = extract_with({"relationships": []})

    assert knowledge.relationships == ()


# ── consensus: settles by majority, atomically ───────────────────────


def _observation(n: int, relationships=()) -> CompanyKnowledgeObservation:
    from tests.test_supplemental_description_reading import source_document

    document = source_document("")

    from app.domain.company_knowledge import BusinessSegment

    return CompanyKnowledgeObservation(
        symbol="EXAM.PA",
        description="An industrial group.",
        segments=(
            BusinessSegment(name="Alpha Division", revenue=None, description=None),
            BusinessSegment(name="Financial Arm", revenue=None, description=None),
        ),
        source=document.source,
        reading=Provenance(
            source="test-reader",
            observed_at=datetime(2026, 8, 13, 10, n, tzinfo=UTC),
        ),
        relationships=tuple(relationships),
    )


def test_a_majority_settles_the_relationship() -> None:
    observations = (
        _observation(0, [RELATIONSHIP]),
        _observation(1, [RELATIONSHIP]),
        _observation(2, [RELATIONSHIP]),
        _observation(3),
        _observation(4),
    )

    consensus = consensus_of(observations)

    financial = next(s for s in consensus.segments if s.name == "Financial Arm")

    assert financial.dependency is not None
    assert financial.dependency.statement == RELATIONSHIP.statement
    assert financial.dependency_agreement is not None
    assert financial.dependency_agreement.counted() == "3/5"

    alpha = next(s for s in consensus.segments if s.name == "Alpha Division")

    assert alpha.dependency is None


def test_a_minority_claim_settles_to_nothing() -> None:
    observations = (
        _observation(0, [RELATIONSHIP]),
        _observation(1),
        _observation(2),
        _observation(3),
        _observation(4),
    )

    consensus = consensus_of(observations)

    financial = next(s for s in consensus.segments if s.name == "Financial Arm")

    assert financial.dependency is None


# ── the understanding surface, and the filer's degree ────────────────


def test_the_understanding_words_the_filers_claim_with_its_degree() -> None:
    observations = tuple(_observation(n, [RELATIONSHIP]) for n in range(5))

    understanding = understand(consensus_of(observations))

    financial = next(s for s in understanding.sells if s.name == "Financial Arm")

    assert financial.depends_stated is not None
    assert "states that this business" in financial.depends_stated
    assert "predominantly" in financial.depends_stated
    assert "entirely" not in financial.depends_stated
    assert financial.depends_quoted == RELATIONSHIP.quoted
    assert financial.depends_support == "stated by the filer; 5/5 readings agree"


def test_absence_is_an_evidence_state_never_independence() -> None:
    """The DIS control, structurally: no stated dependence renders as
    nothing at all — no field anywhere says 'independent'."""

    observations = tuple(_observation(n) for n in range(5))

    understanding = understand(consensus_of(observations))

    for segment in understanding.sells:
        assert segment.depends_stated is None
        assert segment.depends_quoted is None
        assert segment.depends_support is None


# ── decision neutrality (requirements 10 + 14) ───────────────────────


def test_the_relationship_cannot_move_the_understanding_verdict() -> None:
    """Identical engine, archetype and contingencies with and without
    the relationship — it is presentation the domain owns, not input."""

    without = understand(consensus_of(tuple(_observation(n) for n in range(5))))
    with_it = understand(
        consensus_of(tuple(_observation(n, [RELATIONSHIP]) for n in range(5)))
    )

    assert without.engine == with_it.engine
    assert without.characteristics == with_it.characteristics
    assert without.contingencies == with_it.contingencies


def test_no_selector_or_rule_reads_the_dependency() -> None:
    """The door held shut in source: the archetype rules and playbook
    mappings never mention the dependency fields."""

    import pathlib

    for owner in (
        "app/services/archetype_engine.py",
        "app/services/playbook_mapping.py",
        "app/services/playbook_selector.py",
        "app/domain/financial_question.py",
    ):
        source = pathlib.Path(owner).read_text(encoding="utf-8")

        assert "dependency" not in source, owner
        assert "EconomicRelationship" not in source, owner
        assert "depends_stated" not in source, owner


# ── the store: schema 13 round-trips, 12 restores absent ─────────────


def test_relationships_round_trip_through_the_store(tmp_path) -> None:
    store = JsonCompanyKnowledgeStore(directory=tmp_path)

    store.append(_observation(0, [RELATIONSHIP]))

    restored = store.latest("EXAM.PA")

    assert len(restored) == 1
    assert restored[0].relationships == (RELATIONSHIP,)


def test_a_schema_12_entry_restores_with_the_question_never_asked(
    tmp_path,
) -> None:
    """The cross-schema read: schema 13 changed what a reading is asked,
    not what it is shown, so a 12-entry's claims stay valid — and its
    empty relationships are marked never-asked, not "none found"."""

    store = JsonCompanyKnowledgeStore(directory=tmp_path)

    store.append(_observation(0, [RELATIONSHIP]))

    entry = next(tmp_path.glob("*.json"))
    stored = json.loads(entry.read_text(encoding="utf-8"))
    stored["schema_version"] = 12
    for observed in stored["observations"]:
        del observed["relationships"]
        del observed["relationships_asked"]
    entry.write_text(json.dumps(stored), encoding="utf-8")

    restored = store.latest("EXAM.PA")

    assert len(restored) == 1
    assert restored[0].relationships == ()
    assert restored[0].relationships_asked is False


def test_unasked_readings_cannot_outvote_the_filers_stated_dependence() -> None:
    """Three old readings never asked, two asked readings that found the
    filer's sentence: the dependence settles 2/2 over the asked, rather
    than being outvoted 3-2 by readings the question predates."""

    from dataclasses import replace as dc_replace

    observations = (
        dc_replace(_observation(0), relationships_asked=False),
        dc_replace(_observation(1), relationships_asked=False),
        dc_replace(_observation(2), relationships_asked=False),
        _observation(3, [RELATIONSHIP]),
        _observation(4, [RELATIONSHIP]),
    )

    consensus = consensus_of(observations)

    financial = next(s for s in consensus.segments if s.name == "Financial Arm")

    assert financial.dependency is not None
    assert financial.dependency_agreement is not None
    assert financial.dependency_agreement.counted() == "2/2"


def test_an_append_preserves_the_never_asked_flag(tmp_path) -> None:
    """An append rewrites the whole entry under schema 13; a restored
    unasked reading must not be re-stamped as asked."""

    from dataclasses import replace as dc_replace

    store = JsonCompanyKnowledgeStore(directory=tmp_path)

    store.append(dc_replace(_observation(0), relationships_asked=False))
    store.append(_observation(1, [RELATIONSHIP]))

    restored = store.latest("EXAM.PA")

    assert [o.relationships_asked for o in restored] == [False, True]
