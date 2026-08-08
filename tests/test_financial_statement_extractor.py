"""The model locates cells in a statement; it cannot assert figures into it."""

import asyncio
import json
from datetime import date

import pytest

from app.domain.financial_statements import StatementConcept, matches_concept
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.tabular_evidence import SourceTable, TableRow, row_figures
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined
from app.services.company_knowledge_extractor import MAX_ATTEMPTS, ExtractionRejected
from app.services.financial_statement_extractor import FinancialStatementExtractor

STATEMENT_TABLE = SourceTable(
    index=0,
    caption="(in millions, except per share data)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total net revenue", "177,419", "162,878")),
        TableRow(cells=("Total noninterest expense", "91,000", "87,000")),
        TableRow(cells=("Net income", "58,471", "49,552")),
    ),
)


def statement_document(
    tables: tuple[SourceTable, ...] = (STATEMENT_TABLE,),
    text: str = "Consolidated statements of income",
) -> SourceDocument:
    return SourceDocument(
        source=PrimarySource(
            symbol="JPM",
            company="Example Bank",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 0000019617-26-000100",
            key="0000019617-26-000100",
            published_on=date(2026, 2, 13),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://www.sec.gov/Archives/example",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        business_description="",
        income_statement_text=text,
        income_statement_tables=tables,
    )


class StubProvider:
    """A provider that returns whatever the test wants located."""

    name = "Stub"
    model = "stub-1"

    def __init__(self, payload: object, declined: str | None = None) -> None:
        self._payload = payload
        self._declined = declined
        self.requests: list[DraftRequest] = []

    async def draft(self, request: DraftRequest) -> Draft:
        self.requests.append(request)

        if self._declined is not None:
            raise NarrativeDeclined(self._declined)

        return Draft(text=json.dumps(self._payload), model=self.model, usage=None)


def located(concept: str, row: int, value: float) -> dict[str, object]:
    return {"concept": concept, "table": 0, "row": row, "column": 1, "value": value}


BOTH = {
    "located": [
        located("total_revenue", 1, 177419),
        located("net_income", 3, 58471),
    ]
}


def extract(payload: object, document: SourceDocument | None = None):
    provider = StubProvider(payload)

    return asyncio.run(
        FinancialStatementExtractor(provider).extract(
            "JPM", document or statement_document()
        )
    )


def test_a_located_figure_is_read_back_out_of_the_document() -> None:
    """The anchor carries the filer's label, header, printed cell and caption."""

    observation = extract(BOTH)

    revenue = observation.fact(StatementConcept.TOTAL_REVENUE)

    assert revenue is not None and revenue.anchor is not None
    assert revenue.anchor.label == "Total net revenue"
    assert revenue.anchor.column_header == "2025"
    assert revenue.anchor.printed == "177,419"
    assert revenue.anchor.value == 177419.0
    assert revenue.anchor.caption == "(in millions, except per share data)"


def test_the_rest_of_the_row_is_read_by_the_platform() -> None:
    """
    Prior periods arrive as evidence without a single model claim: the
    anchored row's other figures are read off the parsed table, each
    under the filer's own header.
    """

    observation = extract(BOTH)

    income = observation.fact(StatementConcept.NET_INCOME)

    assert income is not None
    assert [figure.printed for figure in income.row] == ["58,471", "49,552"]
    assert [figure.column_header for figure in income.row] == ["2025", "2024"]


def test_a_reading_that_disagrees_with_the_document_is_discarded() -> None:
    """A misaddressed citation becomes a disagreement, and is caught."""

    provider = StubProvider({"located": [located("total_revenue", 1, 999999)]})

    with pytest.raises(ExtractionRejected, match="disagree"):
        asyncio.run(
            FinancialStatementExtractor(provider).extract("JPM", statement_document())
        )

    # Held to the same bounded retries as every reading.
    assert len(provider.requests) == MAX_ATTEMPTS


def test_a_row_the_concept_does_not_declare_is_refused() -> None:
    """
    The applicability gate: a real figure, in the right table, on a row
    the filer labels as something else entirely.
    """

    payload = {"located": [located("total_revenue", 2, 91000)]}

    with pytest.raises(ExtractionRejected, match="Total noninterest expense"):
        extract(payload)


def test_one_cell_cannot_answer_two_concepts() -> None:
    """
    Refused by whichever check reaches it first: today the label
    correspondence, since no row label answers two concepts — and the
    distinctness backstop stands behind it for the day the vocabulary
    grows overlapping forms.
    """

    payload = {
        "located": [
            located("total_revenue", 1, 177419),
            {
                "concept": "net_income",
                "table": 0,
                "row": 1,
                "column": 1,
                "value": 177419,
            },
        ]
    }

    with pytest.raises(ExtractionRejected, match="Total net revenue"):
        extract(payload)


def test_a_concept_never_asked_for_is_refused() -> None:
    payload = {"located": [located("operating_margin", 1, 42)]}

    with pytest.raises(ExtractionRejected, match="never asked"):
        extract(payload)


def test_a_concept_located_twice_is_refused() -> None:
    payload = {
        "located": [
            located("total_revenue", 1, 177419),
            located("total_revenue", 1, 177419),
        ]
    }

    with pytest.raises(ExtractionRejected, match="twice"):
        extract(payload)


def test_a_header_row_citation_is_refused() -> None:
    payload = {"located": [located("total_revenue", 0, 2025)]}

    with pytest.raises(ExtractionRejected, match="header row"):
        extract(payload)


def test_an_omitted_concept_is_a_worded_absence_not_a_failure() -> None:
    """The claim that no cell holds it is stored for the consensus to weigh."""

    observation = extract({"located": [located("total_revenue", 1, 177419)]})

    income = observation.fact(StatementConcept.NET_INCOME)

    assert income is not None
    assert income.anchor is None
    assert income.unlocated_because is not None
    assert "located no cell" in income.unlocated_because


def test_a_document_with_no_statement_is_read_without_a_model() -> None:
    """
    A deterministic observation, every concept absent with the reason
    saying which fact it states — and no spend anywhere.
    """

    provider = StubProvider(BOTH)

    observation = asyncio.run(
        FinancialStatementExtractor(provider).extract(
            "JPM", statement_document(tables=(), text="")
        )
    )

    assert provider.requests == []
    assert all(fact.anchor is None for fact in observation.facts)
    assert all(
        fact.unlocated_because is not None
        and "located no income statement" in fact.unlocated_because
        for fact in observation.facts
    )


def test_a_located_statement_with_no_readable_table_says_that_instead() -> None:
    """Two different absences, and only one might be about the company."""

    provider = StubProvider(BOTH)

    observation = asyncio.run(
        FinancialStatementExtractor(provider).extract(
            "JPM",
            statement_document(tables=(), text="Consolidated statements of income"),
        )
    )

    assert provider.requests == []
    assert all(
        fact.unlocated_because is not None
        and "no table this platform could read" in fact.unlocated_because
        for fact in observation.facts
    )


def test_a_declined_reading_is_a_worded_rejection() -> None:
    provider = StubProvider(BOTH, declined="No credentials are configured.")

    with pytest.raises(ExtractionRejected, match="credentials"):
        asyncio.run(
            FinancialStatementExtractor(provider).extract("JPM", statement_document())
        )


def test_concept_labels_match_by_equality_never_containment() -> None:
    """
    "Total net revenue" contains "revenue", and so does "Revenue from
    contracts with related parties" — a containment rule would read the
    second as the company's revenue.
    """

    assert matches_concept(StatementConcept.TOTAL_REVENUE, "Total net revenue")
    assert matches_concept(StatementConcept.TOTAL_REVENUE, "REVENUES")
    assert not matches_concept(
        StatementConcept.TOTAL_REVENUE, "Revenue from contracts with related parties"
    )
    assert matches_concept(StatementConcept.NET_INCOME, "Net income (loss)")
    assert not matches_concept(StatementConcept.NET_INCOME, "Net income per share")


def test_the_row_expansion_skips_what_it_cannot_name() -> None:
    """A number under an unheaded column is a number whose period is unproven."""

    table = SourceTable(
        index=0,
        caption="",
        rows=(
            TableRow(cells=("", "2025", "")),
            TableRow(cells=("Net income", "58,471", "49,552")),
        ),
    )

    figures = row_figures(table, 1)

    assert [figure.printed for figure in figures] == ["58,471"]


def test_the_row_expansion_reads_no_header_or_label_rows() -> None:
    assert row_figures(STATEMENT_TABLE, 0) == ()
    assert row_figures(STATEMENT_TABLE, 9) == ()
