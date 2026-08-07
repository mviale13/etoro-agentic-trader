"""Repairing the evidence for a claim is not rereading the document.

The distinction this whole mechanism rests on. A retry asks the same
open question again and takes whichever answer passes, which turns the
objective from *read this document* into *find something acceptable*. A
repair asks a closed question about a claim already made: these words
were refused as evidence for it — is there better evidence here, or
none?

Every test below exists to prove the second thing cannot quietly become
the first.
"""

import asyncio
import json
from datetime import date

from app.domain.company_knowledge import RevenueModel
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.reader_defects import DefectCause, cause_of
from app.providers.narrative_provider import Draft, DraftRequest
from app.services.company_knowledge_extractor import (
    ASKED_BY_NAME_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    CompanyKnowledgeExtractor,
)

FILING_TEXT = (
    "ITEM 1. Business The Company operates in two segments. "
    "The Entertainment segment produces and distributes film and television "
    "content and operates direct-to-consumer streaming services. "
    "The Experiences segment operates theme parks and resorts and licenses "
    "the Company's intellectual property to third parties."
)

#: Words the filing prints under Entertainment. Cited for Experiences,
#: they are Meta's failure exactly: genuinely in the document, genuinely
#: about a segment, and about the wrong one.
ANOTHER_SEGMENTS_WORDS = "produces and distributes film and television"

#: Words the filing prints under Experiences, which is where the repair
#: should have looked in the first place.
ITS_OWN_WORDS = "operates theme parks and resorts"


def filing() -> SourceDocument:
    return SourceDocument(
        source=PrimarySource(
            symbol="DIS",
            company="Example Co",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 0001744489-25-000155",
            key="0001744489-25-000155",
            published_on=date(2025, 11, 13),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://www.sec.gov/Archives/example",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        business_description=FILING_TEXT,
    )


class ScriptedProvider:
    """Answers each request in turn, and records every one of them.

    Counting requests is the point. "Exactly one bounded attempt" is a
    claim about how many times this platform asks, and only the provider
    can testify to it.
    """

    name = "Scripted"
    model = "reader-9"

    def __init__(self, *answers: object) -> None:
        self._answers = list(answers)
        self.requests: list[DraftRequest] = []

    async def draft(self, request: DraftRequest) -> Draft:
        self.requests.append(request)

        answer = self._answers.pop(0) if self._answers else {}

        return Draft(text=json.dumps(answer), model=self.model, usage=None)

    @property
    def repairs(self) -> list[DraftRequest]:
        return [
            request
            for request in self.requests
            if request.system_prompt == REPAIR_SYSTEM_PROMPT
        ]

    @property
    def asked_by_name(self) -> list[DraftRequest]:
        return [
            request
            for request in self.requests
            if request.system_prompt == ASKED_BY_NAME_SYSTEM_PROMPT
        ]


def reading(experiences_quotes: str) -> dict[str, object]:
    """A first reading that describes Entertainment soundly, Experiences not."""

    return {
        "description": "A diversified entertainment company.",
        "segments": [
            {
                "name": "Entertainment",
                "revenue_models": ["subscription"],
                "quoted": "produces and distributes film and television content",
            },
            {
                "name": "Experiences",
                "revenue_models": ["transaction", "licensing"],
                "quoted": experiences_quotes,
            },
        ],
    }


def extract(*answers: object):
    provider = ScriptedProvider(*answers)
    knowledge = asyncio.run(
        CompanyKnowledgeExtractor(provider).extract("DIS", filing())
    )

    return knowledge, provider


def named(knowledge, name: str):
    return next(segment for segment in knowledge.segments if segment.name == name)


# ── the acceptance case, both ways ──────────────────────────────────


def test_a_refused_citation_is_repaired_once_and_says_so() -> None:
    """
    The case the mechanism exists for. A claim's first citation quotes
    another segment's words and is refused; one targeted request returns
    a span the filing prints under this segment's own name; the claim is
    evidenced and the repair is recorded.
    """

    knowledge, provider = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {"quoted": ITS_OWN_WORDS},
    )

    experiences = named(knowledge, "Experiences")

    assert experiences.description is not None
    assert experiences.quoted == ITS_OWN_WORDS
    assert experiences.undescribed_because is None

    # Recorded, never presented as a first reading.
    repair = experiences.description.repair
    assert repair is not None
    assert experiences.description.was_repaired
    assert repair.reader == "reader-9"
    assert "Entertainment" in repair.first_refused_because

    # Exactly one, and it was the repair contract rather than a reread.
    assert len(provider.repairs) == 1


def test_a_repair_that_finds_nothing_leaves_that_one_claim_absent() -> None:
    """
    The other half, and the one that proves the boundary held. The
    filing is asked once more and answers honestly that it says nothing;
    the description stays absent, with both reasons, and nothing else
    about the reading is touched.
    """

    knowledge, provider = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {"quoted": ""},
    )

    experiences = named(knowledge, "Experiences")

    assert experiences.description is None
    assert experiences.revenue_models == ()

    # Both reasons: why the citation was refused, and what was then done
    # about it. A reader deciding whether the gap is worth chasing needs
    # to know the platform already tried.
    assert "Entertainment" in (experiences.undescribed_because or "")
    assert "repair was attempted" in (experiences.undescribed_because or "")

    # The rest of the knowledge object is unaffected — the segment keeps
    # its identity, and the segment that was described stays described.
    assert experiences.name == "Experiences"
    assert named(knowledge, "Entertainment").description is not None
    assert knowledge.description == "A diversified entertainment company."

    assert len(provider.repairs) == 1


def test_a_repaired_span_is_held_to_the_identical_contract() -> None:
    """
    A repair that cites another segment's words again is refused again.
    The mechanism improves coverage by asking better, never by accepting
    more — if applicability could be relaxed for a second attempt, every
    refusal would be one retry away from passing.
    """

    knowledge, _ = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {"quoted": ANOTHER_SEGMENTS_WORDS},
    )

    experiences = named(knowledge, "Experiences")

    assert experiences.description is None
    assert "refused too" in (experiences.undescribed_because or "")


# ── what a repair is not allowed to do ──────────────────────────────


def test_a_repair_cannot_change_what_is_being_claimed() -> None:
    """
    The ways of earning come from the first reading. A repair that tries
    to add one has nowhere to put it — `repair_schema` has a single
    field — and anything it sends anyway is not read.

    This is what keeps "repair the evidence for this claim" from
    becoming "find a claim that can be evidenced".
    """

    knowledge, provider = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {
            "quoted": ITS_OWN_WORDS,
            # None of this exists in the contract. Sent anyway.
            "revenue_models": ["subscription", "advertising", "premiums"],
            "name": "Something Else",
        },
    )

    experiences = named(knowledge, "Experiences")

    assert experiences.name == "Experiences"
    assert experiences.revenue_models == (
        RevenueModel.TRANSACTION,
        RevenueModel.LICENSING,
    )

    # And the contract offered no way to say otherwise.
    assert set(provider.repairs[0].schema["properties"]) == {"quoted"}


def test_an_empty_arrival_is_asked_by_name_not_repaired() -> None:
    """
    A reading that returned no words made no claim, so there is nothing
    to *repair* — the repair contract is never used for it. What it now
    earns instead is the asked-by-name follow-up: a closed question
    about that one segment, exactly once. The taxonomy overturned the
    old leave-it-as-it-arrived rule with a measurement: on JPMorgan's
    10-K, two readings in five found describing words the other three
    returned empty, so an empty arrival is one pass's attention, not
    yet a fact about the filing.
    """

    knowledge, provider = extract(reading(""), {"quoted": ITS_OWN_WORDS})

    assert provider.repairs == []
    assert len(provider.asked_by_name) == 1
    assert named(knowledge, "Experiences").description is not None


def test_asked_by_name_describes_the_segment_and_says_how_it_was_asked() -> None:
    knowledge, provider = extract(reading(""), {"quoted": ITS_OWN_WORDS})

    experiences = named(knowledge, "Experiences")

    assert experiences.description is not None
    assert experiences.quoted == ITS_OWN_WORDS
    assert experiences.undescribed_because is None

    # The claim is the first reading's: the models arrived beside the
    # empty span, and the follow-up evidenced them rather than made them.
    assert experiences.revenue_models == (
        RevenueModel.TRANSACTION,
        RevenueModel.LICENSING,
    )

    # Recorded, never presented as a first reading.
    repair = experiences.description.repair
    assert repair is not None
    assert "no words at all" in repair.first_refused_because
    assert repair.reader == "reader-9"


def test_asked_by_name_finding_nothing_is_the_stronger_worded_absence() -> None:
    """
    Volkswagen's shape, measured: its tagged note prints tables and
    boilerplate and describes nothing, so the honest answer to the
    closed question is empty — and that absence is a different fact
    from an empty first arrival, because the attention explanation has
    been ruled out. The taxonomy reads it as its own cause.
    """

    knowledge, provider = extract(reading(""), {"quoted": ""})

    experiences = named(knowledge, "Experiences")

    assert experiences.description is None
    assert experiences.revenue_models == ()

    because = experiences.undescribed_because or ""

    assert "no words at all" in because
    assert "Asked once more by name" in because
    assert cause_of(because) is DefectCause.NONE_TO_QUOTE

    assert len(provider.asked_by_name) == 1


def test_an_asked_by_name_span_is_held_to_the_identical_contract() -> None:
    knowledge, _ = extract(reading(""), {"quoted": ANOTHER_SEGMENTS_WORDS})

    experiences = named(knowledge, "Experiences")

    assert experiences.description is None
    assert "refused too" in (experiences.undescribed_because or "")


def test_asked_by_name_is_one_attempt_and_cannot_supply_a_claim() -> None:
    """
    The same boundary the repair holds, held here: one bounded request,
    and a one-field contract with nowhere to put a revenue model or a
    different segment. A segment that arrived with neither words nor
    models is described and names no way of earning — the narrower
    honest claim — however many models the follow-up tries to send.
    """

    wordless = {
        "description": "A diversified entertainment company.",
        "segments": [
            {
                "name": "Entertainment",
                "revenue_models": ["subscription"],
                "quoted": "produces and distributes film and television content",
            },
            {"name": "Experiences", "revenue_models": [], "quoted": ""},
        ],
    }

    knowledge, provider = extract(
        wordless,
        {"quoted": ITS_OWN_WORDS, "revenue_models": ["premiums"]},
        {"quoted": ITS_OWN_WORDS},  # never asked for
    )

    experiences = named(knowledge, "Experiences")

    assert experiences.description is not None
    assert experiences.revenue_models == ()

    assert len(provider.asked_by_name) == 1
    assert set(provider.asked_by_name[0].schema["properties"]) == {"quoted"}


def test_a_sound_citation_is_never_second_guessed() -> None:
    """
    A description that applied is left alone. Asking again about a claim
    that is already evidenced would be looking for a better answer, not
    a repair — and it would cost a model call per segment per filing.
    """

    knowledge, provider = extract(reading(ITS_OWN_WORDS))

    assert named(knowledge, "Experiences").description is not None
    assert named(knowledge, "Entertainment").description is not None
    assert provider.repairs == []


def test_a_repair_is_asked_once_and_the_failure_then_stands() -> None:
    """
    No loop. A repair that fails is not repaired, and the second
    attempt's refusal is where it ends — the boundary between one
    bounded request and "until something passes" is a count.
    """

    knowledge, provider = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {"quoted": ANOTHER_SEGMENTS_WORDS},
        {"quoted": ITS_OWN_WORDS},  # would have worked, and is never asked for
    )

    assert named(knowledge, "Experiences").description is None
    assert len(provider.repairs) == 1


def test_each_repair_is_scoped_to_one_claim_in_one_document() -> None:
    """
    Same segment, same document, and the refused citation stated back —
    so the request cannot be about anything other than the claim already
    made.
    """

    _, provider = extract(
        reading(ANOTHER_SEGMENTS_WORDS),
        {"quoted": ITS_OWN_WORDS},
    )

    asked = provider.repairs[0].user_prompt

    assert "Experiences" in asked
    assert ANOTHER_SEGMENTS_WORDS in asked
    assert FILING_TEXT in asked

    # The claim is stated as unchanged, and the refusal as the thing
    # being fixed.
    assert "The claim, unchanged" in asked
