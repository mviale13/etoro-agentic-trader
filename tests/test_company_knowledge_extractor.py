"""The model reads the filing; it cannot assert anything into it."""

import asyncio
import json
from datetime import date

import pytest

from app.domain.company_knowledge import RevenueModel
from app.domain.primary_source import PrimarySource, SourceDocument, SourceType
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined
from app.services.company_knowledge_extractor import (
    CompanyKnowledgeExtractor,
    ExtractionRejected,
)

FILING_TEXT = (
    "ITEM 1. Business The Company operates in two segments. "
    "The Entertainment segment produces and distributes film and television "
    "content and operates direct-to-consumer streaming services. "
    "The Experiences segment operates theme parks and resorts and licenses "
    "the Company's intellectual property to third parties."
)


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
        ),
        business_description=FILING_TEXT,
    )


class StubProvider:
    """A provider that returns whatever the test wants extracted."""

    name = "Stub"
    model = "stub-1"

    def __init__(self, payload: object, declined: str | None = None) -> None:
        self._payload = payload
        self._declined = declined
        self.request: DraftRequest | None = None

    async def draft(self, request: DraftRequest) -> Draft:
        self.request = request

        if self._declined is not None:
            raise NarrativeDeclined(self._declined)

        return Draft(text=json.dumps(self._payload), model=self.model, usage=None)


def extract(payload: object, declined: str | None = None):
    provider = StubProvider(payload, declined)

    return asyncio.run(CompanyKnowledgeExtractor(provider).extract("DIS", filing()))


def segment(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Entertainment",
        "revenue_share": None,
        "revenue_models": ["subscription", "advertising"],
        "quoted": "The Entertainment segment produces and distributes film",
    }

    return {**base, **overrides}


def test_facts_the_filing_actually_contains_are_read() -> None:
    knowledge = extract(
        {
            "description": "A diversified entertainment company.",
            "segments": [segment()],
        }
    )

    assert knowledge.segments[0].name == "Entertainment"
    assert knowledge.segments[0].revenue_models == (
        RevenueModel.SUBSCRIPTION,
        RevenueModel.ADVERTISING,
    )

    # Traceable to the exact document, not merely to "a filing".
    assert knowledge.source.key == "0001744489-25-000155"
    assert knowledge.stated_source() == (
        "10-K 0001744489-25-000155 published 2025-11-13, via SEC EDGAR"
    )


def test_a_segment_the_filing_never_described_is_refused() -> None:
    """
    The grounding contract, enforced against the document itself.

    This is what makes the model an extractor rather than a classifier.
    It cannot assert a segment into existence, however confidently,
    because what is stored is not its assertion — it is the span of the
    filing the segment was read from, and that span must be there.
    """

    with pytest.raises(ExtractionRejected) as rejected:
        extract(
            {
                "description": "A diversified entertainment company.",
                "segments": [
                    segment(
                        name="Cloud Infrastructure",
                        quoted="The Cloud Infrastructure segment sells compute",
                    )
                ],
            }
        )

    assert "not in the filing" in str(rejected.value)


def test_one_ungrounded_segment_discards_the_whole_reading() -> None:
    """Partly trusting an extraction is trusting the part that lied."""

    with pytest.raises(ExtractionRejected):
        extract(
            {
                "description": "A diversified entertainment company.",
                "segments": [
                    segment(),
                    segment(name="Invented", quoted="a segment nobody wrote down"),
                ],
            }
        )


def test_typography_the_filing_arrived_with_does_not_reject_a_real_quote() -> None:
    """
    Markup leaves stray spacing inside words, and the words are still there.

    The check is strict about which words appear and in what order, and
    forgiving about the spacing between them — otherwise a document's own
    formatting would look like a fabrication.
    """

    knowledge = extract(
        {
            "description": "A diversified entertainment company.",
            "segments": [
                segment(quoted="The  Entertainment segment\nproduces and distributes")
            ],
        }
    )

    assert knowledge.segments[0].name == "Entertainment"


def test_shares_that_cannot_be_shares_of_one_company_are_refused() -> None:
    """Rescaling them silently would turn a misreading into a fact."""

    with pytest.raises(ExtractionRejected) as rejected:
        extract(
            {
                "description": "A diversified entertainment company.",
                "segments": [
                    segment(revenue_share=0.8),
                    segment(
                        name="Experiences",
                        revenue_share=0.7,
                        quoted="The Experiences segment operates theme parks",
                    ),
                ],
            }
        )

    assert "discarded rather than rescaled" in str(rejected.value)


def test_a_share_the_filing_did_not_state_stays_absent() -> None:
    """An unstated share is never apportioned from what is left over."""

    knowledge = extract(
        {
            "description": "A diversified entertainment company.",
            "segments": [segment(revenue_share=None)],
        }
    )

    assert knowledge.segments[0].revenue_share is None
    assert knowledge.measured_share == 0.0


def test_a_provider_that_declines_produces_a_worded_refusal() -> None:
    with pytest.raises(ExtractionRejected) as rejected:
        extract({}, declined="The model declined to read this filing.")

    assert "declined" in str(rejected.value)


def test_the_extractor_is_told_not_to_judge_the_company() -> None:
    """
    It reads. Whether this is a good business is a rule's decision, later.
    """

    provider = StubProvider(
        {
            "description": "A diversified entertainment company.",
            "segments": [segment()],
        }
    )

    asyncio.run(CompanyKnowledgeExtractor(provider).extract("DIS", filing()))

    assert provider.request is not None
    assert "You are reading, not deciding." in provider.request.system_prompt
