"""Statement facts are acquired once per filing, and the spend is explicit."""

import asyncio
from datetime import UTC, date, datetime
from pathlib import Path

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.knowledge_consensus import QUORUM
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from app.services.company_knowledge_extractor import ExtractionRejected
from app.services.company_knowledge_service import KnowledgeState
from app.services.financial_statement_service import FinancialStatementService

ACCESSION = "0000019617-26-000100"


def source(key: str = ACCESSION) -> PrimarySource:
    return PrimarySource(
        symbol="JPM",
        company="Example Bank",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
        published_on=date(2026, 2, 13),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{key}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


def observation() -> FinancialStatementObservation:
    anchor = ReportedFigure(
        label="Total net revenue",
        column_header="2025",
        printed="177,419",
        value=177419.0,
        cell=CellReference(table=0, row=1, column=1),
        caption="(in millions)",
    )

    return FinancialStatementObservation(
        symbol="JPM",
        statement=StatementKind.INCOME_STATEMENT,
        facts=(
            StatementFact(
                concept=StatementConcept.TOTAL_REVENUE,
                anchor=anchor,
                row=(anchor,),
            ),
        ),
        source=source(),
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime.now(UTC),
        ),
    )


class ProviderStub:
    """Counts what a cycle actually costs: lookups, and documents fetched."""

    name = "Stub source"

    def __init__(
        self,
        unavailable: str | None = None,
        outage: bool = False,
    ) -> None:
        self.unavailable = unavailable
        self.outage = outage
        self.lookups = 0
        self.documents_read = 0
        self.current = source()

    def resolve(self, symbol: str) -> PrimarySource:
        self.lookups += 1

        if self.unavailable is not None:
            if self.outage:
                raise PrimarySourceProviderError(self.unavailable)

            raise PrimarySourceUnavailable(self.unavailable)

        return self.current

    def fetch(self, resolved: PrimarySource) -> SourceDocument:
        self.documents_read += 1

        return SourceDocument(
            source=resolved,
            business_description="",
            income_statement_text="Consolidated statements of income",
        )


class ResolverStub:
    def __init__(self, provider: ProviderStub) -> None:
        self.provider = provider

    def resolve(self, symbol: str):
        return self.provider.resolve(symbol), self.provider


class ExtractorStub:
    def __init__(self, rejected: str | None = None) -> None:
        self.extractions = 0
        self.rejected = rejected

    async def extract(
        self,
        symbol: str,
        document: SourceDocument,
        statement: StatementKind = StatementKind.INCOME_STATEMENT,
    ) -> FinancialStatementObservation:
        self.extractions += 1

        if self.rejected is not None:
            raise ExtractionRejected(self.rejected)

        return observation()


def service(tmp_path: Path, provider: ProviderStub, extractor: ExtractorStub):
    return FinancialStatementService(
        store=JsonFinancialStatementStore(tmp_path),
        sources=ResolverStub(provider),  # type: ignore[arg-type]
        extractor=extractor,  # type: ignore[arg-type]
    )


def test_a_statement_is_read_and_extracted_once_ever(tmp_path: Path) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub()

    first = asyncio.run(service(tmp_path, filings, extractor).statements("JPM"))
    second = asyncio.run(service(tmp_path, filings, extractor).statements("JPM"))

    assert first.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert second.state is KnowledgeState.AVAILABLE_CACHED
    assert second.statements is not None
    assert second.statements.observation_count == 1

    assert filings.lookups == 2
    assert filings.documents_read == 1
    assert extractor.extractions == 1


def test_observe_fills_the_quorum_and_stops_on_the_count(tmp_path: Path) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub()

    outcome = asyncio.run(service(tmp_path, filings, extractor).observe("JPM"))

    assert outcome.statements is not None
    assert outcome.statements.observation_count == QUORUM
    assert outcome.statements.is_quorate
    assert extractor.extractions == QUORUM

    # Already at the target: nothing further is observed or spent.
    again = asyncio.run(service(tmp_path, filings, extractor).observe("JPM"))

    assert again.statements is not None
    assert extractor.extractions == QUORUM


def test_a_gap_in_coverage_is_not_an_outage(tmp_path: Path) -> None:
    gap = ProviderStub(unavailable="JPM is not listed with this register.")
    outage = ProviderStub(unavailable="The register could not be reached.", outage=True)

    missing = asyncio.run(service(tmp_path, gap, ExtractorStub()).statements("JPM"))
    failed = asyncio.run(service(tmp_path, outage, ExtractorStub()).statements("JPM"))

    assert missing.state is KnowledgeState.UNAVAILABLE
    assert failed.state is KnowledgeState.PROVIDER_ERROR
    assert missing.absent_because is not None
    assert failed.absent_because is not None


def test_a_rejected_reading_stores_nothing(tmp_path: Path) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub(rejected="The reading and the document disagree.")

    outcome = asyncio.run(service(tmp_path, filings, extractor).statements("JPM"))

    assert outcome.state is KnowledgeState.INVALID_EXTRACTION
    assert outcome.statements is None
    assert outcome.absent_because is not None
    assert (
        JsonFinancialStatementStore(tmp_path).read(
            "JPM", ACCESSION, StatementKind.INCOME_STATEMENT
        )
        == ()
    )


def test_a_refusal_mid_observe_keeps_what_was_observed(tmp_path: Path) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub()

    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())
    store.append(observation())

    refusing = ExtractorStub(rejected="The document resists reading.")

    outcome = asyncio.run(service(tmp_path, filings, refusing).observe("JPM"))

    assert outcome.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert outcome.statements is not None
    assert outcome.statements.observation_count == 2
    assert outcome.absent_because == "The document resists reading."
    assert extractor.extractions == 0


def test_an_unconfigured_reader_is_a_worded_absence(tmp_path: Path) -> None:
    """
    The service composed without an extractor states why nothing can be
    read — the hermetic default in tests, where no credentials exist.
    """

    outcome = asyncio.run(
        FinancialStatementService(
            store=JsonFinancialStatementStore(tmp_path),
            sources=ResolverStub(ProviderStub()),  # type: ignore[arg-type]
        ).statements("JPM")
    )

    assert outcome.state is KnowledgeState.UNAVAILABLE
    assert outcome.absent_because is not None


def test_last_filings_statements_stand_when_todays_lookup_fails(
    tmp_path: Path,
) -> None:
    store = JsonFinancialStatementStore(tmp_path)
    store.append(observation())

    outage = ProviderStub(unavailable="The register could not be reached.", outage=True)

    outcome = asyncio.run(service(tmp_path, outage, ExtractorStub()).statements("JPM"))

    assert outcome.state is KnowledgeState.PROVIDER_ERROR
    assert outcome.statements is not None
    assert outcome.statements.observation_count == 1


def test_a_superseded_reading_does_not_fill_the_observe_target(
    tmp_path: Path,
) -> None:
    """An audited statement can be re-read; withdrawn readings do not count."""

    filings = ProviderStub()
    extractor = ExtractorStub()

    asyncio.run(service(tmp_path, filings, extractor).observe("JPM"))
    assert extractor.extractions == QUORUM

    store = JsonFinancialStatementStore(tmp_path)
    withdrawn = store.supersede(
        "JPM", ACCESSION, dict.fromkeys(range(QUORUM), "the filer heads it 2025")
    )
    assert withdrawn == QUORUM

    # The target is unchanged and every stored reading is still there —
    # but none of them votes, so the spend is taken again.
    again = asyncio.run(service(tmp_path, filings, extractor).observe("JPM"))

    assert extractor.extractions == QUORUM * 2
    assert again.statements is not None
    assert again.statements.observation_count == QUORUM
    assert again.statements.superseded_count == QUORUM
    held = store.read("JPM", ACCESSION, StatementKind.INCOME_STATEMENT)

    assert len(held) == QUORUM * 2, "the withdrawn readings are still stored"


def test_a_wholly_superseded_statement_reads_as_never_cached(tmp_path: Path) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub()

    asyncio.run(service(tmp_path, filings, extractor).statements("JPM"))
    JsonFinancialStatementStore(tmp_path).supersede(
        "JPM", ACCESSION, {0: "the filer heads it 2025"}
    )

    outcome = asyncio.run(service(tmp_path, filings, extractor).statements("JPM"))

    assert outcome.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert extractor.extractions == 2


def test_a_withdrawn_statement_is_not_reported_as_never_read(tmp_path: Path) -> None:
    filings = ProviderStub()

    asyncio.run(service(tmp_path, filings, ExtractorStub()).observe("JPM"))
    store = JsonFinancialStatementStore(tmp_path)
    store.supersede(
        "JPM", ACCESSION, dict.fromkeys(range(QUORUM), "the filer heads it 2025")
    )

    read_only = FinancialStatementService(
        store=store,
        sources=ResolverStub(filings),  # type: ignore[arg-type]
        extractor=ExtractorStub(),  # type: ignore[arg-type]
    )

    assert read_only.established("JPM") == {}
    assert read_only.withdrawn("JPM") == {StatementKind.INCOME_STATEMENT: QUORUM}
