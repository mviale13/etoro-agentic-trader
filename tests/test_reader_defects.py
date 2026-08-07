"""The taxonomy classifies the knowledge layer's own reasons — nothing else."""

from datetime import UTC, datetime

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
)
from app.domain.provenance import Provenance
from app.domain.reader_defects import Claim, DefectCause, cause_of
from app.services.reader_defect_service import ReaderDefectService
from tests.test_playbook_mapping import SOURCE

# ── classification, against the real templates ──────────────────────


def test_every_template_lands_on_its_cause() -> None:
    cases = {
        "The description of 'X' arrived with no words at all. "
        "(5 of 5 observations.)": DefectCause.NEVER_ARRIVED,
        "The description of 'X' quotes words that are not in the "
        "document.": DefectCause.UNGROUNDED,
        "The description of 'X' quotes words the document prints outside "
        "the section it heads 'Y', so they are not what it says there "
        "about 'X'.": DefectCause.MISAPPLIED,
        "The description of 'X' quotes words the document prints under "
        "'Y', so they are not what it says about 'X'. A repair was "
        "attempted, and the reader found no words in this filing that "
        "describe this segment.": DefectCause.MISAPPLIED,
        "The filing's description of this segment names no way of "
        "earning.": DefectCause.NAMES_NO_EARNING,
        # The asked-by-name absence follows the empty arrival it
        # answered, and the stronger fact is the operative one.
        "The description of 'X' arrived with no words at all. Asked "
        "once more by name, the reader found no words describing it in "
        "the text this platform reads.": DefectCause.NONE_TO_QUOTE,
        "Which ways this segment earns is unsettled across 5 "
        "observations: 2× financial_spread, services; 2× "
        "financial_spread; 1× financial_spread, premiums.": DefectCause.UNSETTLED,
        "This filing's management discussion is 395 characters long and "
        "prints no table, which makes it a pointer to a document filed "
        "separately rather than the discussion itself.": (DefectCause.POINTER_DOCUMENT),
        "The reading located no cell reporting this segment's revenue in "
        "the tables this filing's performance discussion "
        "prints.": DefectCause.CELL_NOT_LOCATED,
    }

    for reason, expected in cases.items():
        assert cause_of(reason) is expected, reason


def test_an_unknown_wording_is_other_never_guessed() -> None:
    assert cause_of("A wording no template produced.") is DefectCause.OTHER


def test_a_disagreement_outranks_the_wordings_beneath_it() -> None:
    """A consensus disagreement may embed observation wordings; the
    disagreement is the operative fact."""

    reason = (
        "Whether the filing describes this segment is unsettled across 5 "
        "observations: 3× it arrived with no words at all; 2× described."
    )

    assert cause_of(reason) is DefectCause.UNSETTLED


# ── the scan ────────────────────────────────────────────────────────


def observation(*segments: BusinessSegment) -> CompanyKnowledgeObservation:
    return CompanyKnowledgeObservation(
        symbol="TEST",
        description="What the company says it does.",
        segments=segments,
        source=SOURCE,
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime(2026, 8, 7, tzinfo=UTC),
        ),
    )


def undescribed(name: str, because: str) -> BusinessSegment:
    return BusinessSegment(
        name=name,
        revenue=None,
        description=None,
        undescribed_because=because,
        unmeasured_because="The reading located no cell reporting this "
        "segment's revenue in the tables this filing's performance "
        "discussion prints.",
    )


class FakeStore:
    def __init__(self, entries: dict[str, tuple]) -> None:
        self._entries = entries

    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def latest(self, symbol: str) -> tuple:
        return self._entries.get(symbol, ())


def test_the_taxonomy_counts_companies_and_claims_by_cause() -> None:
    nothing_arrived = undescribed(
        "A", "The description of 'A' arrived with no words at all."
    )
    misapplied = undescribed(
        "B",
        "The description of 'B' quotes words the document prints under "
        "'C', so they are not what it says about 'B'.",
    )

    taxonomy = ReaderDefectService(
        store=FakeStore(
            {
                "ONE": (observation(nothing_arrived),),
                "TWO": (observation(nothing_arrived, misapplied),),
            }
        )
    ).taxonomy()

    assert taxonomy.scanned == ("ONE", "TWO")
    assert taxonomy.affected == ("ONE", "TWO")

    by_cause = {count.cause: count for count in taxonomy.by_cause}

    never = by_cause[DefectCause.NEVER_ARRIVED]

    assert never.companies == 2
    assert never.claims == 2
    assert never.symbols == ("ONE", "TWO")

    assert by_cause[DefectCause.MISAPPLIED].companies == 1

    # Both companies also carry the size defect.
    assert by_cause[DefectCause.CELL_NOT_LOCATED].companies == 2


def test_the_pattern_rule_earns_only_causes_reaching_the_threshold() -> None:
    nothing_arrived = undescribed(
        "A", "The description of 'A' arrived with no words at all."
    )

    taxonomy = ReaderDefectService(
        store=FakeStore(
            {
                "ONE": (observation(nothing_arrived),),
                "TWO": (observation(nothing_arrived),),
            }
        )
    ).taxonomy()

    earned = {count.cause for count in taxonomy.earned()}

    assert DefectCause.NEVER_ARRIVED in earned
    assert DefectCause.CELL_NOT_LOCATED in earned
    assert DefectCause.MISAPPLIED not in earned


def test_disagreement_is_noise_and_never_earns_a_slice() -> None:
    unsettled = undescribed(
        "A",
        "Which ways this segment earns is unsettled across 5 "
        "observations: 3× services; 2× manufacturing.",
    )

    taxonomy = ReaderDefectService(
        store=FakeStore(
            {
                "ONE": (observation(unsettled),),
                "TWO": (observation(unsettled),),
            }
        )
    ).taxonomy()

    assert all(count.cause is not DefectCause.UNSETTLED for count in taxonomy.earned())


def test_a_settled_company_contributes_no_defects() -> None:
    from tests.test_playbook_mapping import MFG
    from tests.test_playbook_mapping import segment as full_segment

    settled = (full_segment("Only", share=0.95, earns=MFG),)

    taxonomy = ReaderDefectService(
        store=FakeStore({"ONE": (observation(*settled),) * 5})
    ).taxonomy()

    assert taxonomy.scanned == ("ONE",)
    assert taxonomy.affected == ()
    assert taxonomy.defects == ()

    claims = {defect.claim for defect in taxonomy.defects}

    assert Claim.SEGMENTS not in claims
