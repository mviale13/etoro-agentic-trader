"""The model reads the filing; it cannot assert anything into it."""

import asyncio
import json
from datetime import date

import pytest

from app.domain.company_knowledge import RevenueModel
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.tabular_evidence import SourceTable, TableRow
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined
from app.services.company_knowledge_extractor import (
    MIX_SYSTEM_PROMPT,
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
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
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

    # Traceable to the exact document, not merely to "a filing" — and
    # every citation says what kind of source it was, because "filed
    # with a regulator" and "published by the company" are different
    # claims that a reader must not have to infer.
    assert knowledge.source.key == "0001744489-25-000155"
    assert knowledge.stated_source() == (
        "10-K 0001744489-25-000155 published 2025-11-13, via SEC EDGAR "
        "(filed with a regulator)"
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


def test_the_business_reading_reports_no_sizes_at_all() -> None:
    """
    Prose grounds a description. It cannot ground a quantity.

    The section that describes the business is asked what the parts are,
    and deliberately not how large they are: a span proves the filing
    said something, and a size is a claim about a row and a column that
    no span carries. So a filing read without its tables keeps its
    segments and leaves their sizes absent, rather than taking a number
    from a sentence that happened to sit near one.
    """

    knowledge = extract(
        {
            "description": "A diversified entertainment company.",
            "segments": [segment()],
        }
    )

    assert knowledge.segments[0].revenue is None
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


# ── how large each segment is ───────────────────────────────────────
#
# A different kind of fact, evidenced a different way. The reading points
# at cells; this platform reads those cells back out of the document,
# checks that they say what it was told they say, and does the dividing.


SEGMENT_TABLE = SourceTable(
    index=0,
    caption="The following table presents revenues from our operating segments:",
    rows=(
        TableRow(cells=("($ in millions)", "2025", "2024")),
        TableRow(cells=("Entertainment", "42,466", "41,186")),
        TableRow(cells=("Experiences", "36,156", "34,151")),
        TableRow(cells=("Revenues", "94,425", "91,361")),
    ),
)


def filing_with_tables() -> SourceDocument:
    return SourceDocument(
        source=filing().source,
        business_description=FILING_TEXT,
        performance_discussion="Business segment results.",
        performance_tables=(SEGMENT_TABLE,),
    )


class ReadingsStub:
    """
    A provider that answers each of the two readings with its own payload.

    Answering by which question was asked rather than by call order, so
    that a rejection — which puts the whole reading again — is answered
    the same way the first attempt was.
    """

    name = "Stub"
    model = "stub-1"

    def __init__(self, described: object, mix: object) -> None:
        self._described = described
        self._mix = mix
        self.requests: list[DraftRequest] = []

    async def draft(self, request: DraftRequest) -> Draft:
        self.requests.append(request)

        sizes = request.system_prompt is MIX_SYSTEM_PROMPT

        asked = self._mix if sizes else self._described

        return Draft(text=json.dumps(asked), model=self.model, usage=None)


def cell(row: int, value: float, column: int = 1, table: int = 0) -> dict[str, object]:
    return {"table": table, "row": row, "column": column, "value": value}


def measure(mix: object, description: object = None):
    provider = ReadingsStub(
        description
        or {
            "description": "A diversified entertainment company.",
            "segments": [
                segment(),
                segment(
                    name="Experiences",
                    quoted="The Experiences segment operates theme parks",
                ),
            ],
        },
        mix,
    )

    return asyncio.run(
        CompanyKnowledgeExtractor(provider).extract("DIS", filing_with_tables())
    )


def test_a_size_is_measured_from_two_cells_the_filing_printed() -> None:
    """
    The share is arithmetic this platform performs, not a claim it accepts.

    Both figures are read back out of the table and kept, so what a
    reader is shown is the relationship — this row, under this column,
    over that row — rather than a percentage they are asked to believe.
    """

    knowledge = measure(
        {
            "total": cell(row=3, value=94425),
            "segments": [
                {"segment": "Entertainment", **cell(row=1, value=42466)},
                {"segment": "Experiences", **cell(row=2, value=36156)},
            ],
        }
    )

    entertainment = knowledge.segments[0]

    assert entertainment.revenue is not None
    assert round(entertainment.revenue.share, 4) == 0.4497
    assert entertainment.revenue.numerator.label == "Entertainment"
    assert entertainment.revenue.numerator.column_header == "2025"
    assert entertainment.revenue.denominator.label == "Revenues"
    assert entertainment.revenue.stated().startswith("45% — ")


def test_a_citation_of_a_column_header_supports_nothing() -> None:
    """
    The live failure, and the reason this evidence model exists.

    Reading Volkswagen's segment table, the extraction cited a column
    header for two of three segments. The shares were right, the quoted
    words were genuinely in the document, and the citations demonstrated
    nothing whatsoever — because a span can prove that content exists and
    cannot prove that the content supports the number attached to it.

    An address can. The header row labels the columns and measures
    nothing, so a figure claimed to be there is refused before anyone
    has to notice that the number happened to be right.
    """

    with pytest.raises(ExtractionRejected) as rejected:
        measure(
            {
                "total": cell(row=3, value=94425),
                "segments": [{"segment": "Entertainment", **cell(row=0, value=42466)}],
            }
        )

    assert "header row" in str(rejected.value)


def test_a_figure_the_document_does_not_print_there_is_refused() -> None:
    """
    An address alone cannot be wrong in a way anyone notices.

    Whatever cell it lands on becomes the answer, so the reading must
    also say what is printed there — and the disagreement between what it
    says and what the document prints is the check.
    """

    with pytest.raises(ExtractionRejected) as rejected:
        measure(
            {
                "total": cell(row=3, value=94425),
                "segments": [{"segment": "Entertainment", **cell(row=2, value=42466)}],
            }
        )

    assert "disagree about what is there" in str(rejected.value)


def test_a_figure_measured_against_another_period_is_refused() -> None:
    """
    A ratio across two rows *and* two columns compares two different years.

    The rule costs nothing to enforce and closes a failure that is
    invisible downstream: the arithmetic is sound, both figures are real,
    and the answer is about no period at all.
    """

    with pytest.raises(ExtractionRejected) as rejected:
        measure(
            {
                "total": cell(row=3, value=94425, column=1),
                "segments": [
                    {"segment": "Entertainment", **cell(row=1, value=41186, column=2)}
                ],
            }
        )

    assert "neither a row nor a column" in str(rejected.value)


def test_a_figure_read_off_another_row_is_refused() -> None:
    """A real number, in the right table and column, about another part."""

    with pytest.raises(ExtractionRejected) as rejected:
        measure(
            {
                "total": cell(row=3, value=94425),
                "segments": [{"segment": "Entertainment", **cell(row=2, value=36156)}],
            }
        )

    assert "a different thing" in str(rejected.value)


def test_a_filing_with_no_total_leaves_the_sizes_absent() -> None:
    """
    Nothing to measure against is not a failure, and not an excuse either.

    The segments keep their descriptions, their sizes stay unstated, and
    nothing is apportioned from what is left over.
    """

    knowledge = measure({"total": None, "segments": []})

    assert knowledge.segments[0].name == "Entertainment"
    assert knowledge.segments[0].revenue is None
    assert knowledge.measured_share == 0.0


def test_a_part_larger_than_the_whole_it_was_measured_against_is_refused() -> None:
    """A total that is not a total makes every share of it meaningless."""

    with pytest.raises(ExtractionRejected) as rejected:
        measure(
            {
                "total": cell(row=2, value=36156),
                "segments": [
                    {"segment": "Entertainment", **cell(row=1, value=42466)},
                ],
            }
        )

    assert "not a share" in str(rejected.value)


def test_sizes_that_cannot_be_parts_of_one_company_are_refused() -> None:
    """
    Rescaling them silently would turn a misreading into a fact.

    Segments sum past a consolidated total by whatever they sold each
    other — Volkswagen's reach 108.5% of group revenue. They do not
    reach half as much again, and a mix that does is discarded rather
    than normalised back into something plausible.
    """

    doubled = SourceTable(
        index=0,
        caption="Revenues by segment",
        rows=(
            TableRow(cells=("Mio.", "2025")),
            TableRow(cells=("Entertainment", "80")),
            TableRow(cells=("Experiences", "80")),
            TableRow(cells=("Total revenues", "100")),
        ),
    )

    provider = ReadingsStub(
        {
            "description": "A diversified entertainment company.",
            "segments": [
                segment(),
                segment(
                    name="Experiences",
                    quoted="The Experiences segment operates theme parks",
                ),
            ],
        },
        {
            "total": cell(row=3, value=100),
            "segments": [
                {"segment": "Entertainment", **cell(row=1, value=80)},
                {"segment": "Experiences", **cell(row=2, value=80)},
            ],
        },
    )

    document = SourceDocument(
        source=filing().source,
        business_description=FILING_TEXT,
        performance_tables=(doubled,),
    )

    with pytest.raises(ExtractionRejected) as rejected:
        asyncio.run(CompanyKnowledgeExtractor(provider).extract("DIS", document))

    assert "discarded rather than rescaled" in str(rejected.value)


def test_the_sizes_reading_is_shown_the_tables_rather_than_the_prose() -> None:
    """
    The prose is where the old citation came from, and where it misled.

    Handing this reading the flattened discussion would offer it spans to
    quote — the very evidence that cannot carry a quantity — so it is
    given the tables, addressed, and nothing else.
    """

    provider = ReadingsStub(
        {
            "description": "A diversified entertainment company.",
            "segments": [segment()],
        },
        {"total": None, "segments": []},
    )

    asyncio.run(
        CompanyKnowledgeExtractor(provider).extract("DIS", filing_with_tables())
    )

    mix = provider.requests[1]

    assert "[table 0]" in mix.user_prompt
    assert 'r1: c0="Entertainment" | c1="42,466" | c2="41,186"' in mix.user_prompt
    assert "Business segment results." not in mix.user_prompt
