"""Structural knowledge is acquired once per filing, and then kept."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledge,
    DescriptionRepair,
    RevenueModel,
    SegmentDescription,
)
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.prose_evidence import DescribedSegment
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
)
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeState,
)

ACCESSION = "0001744489-25-000155"


def source(key: str = ACCESSION, published: str = "2025-11-13") -> PrimarySource:
    return PrimarySource(
        symbol="DIS",
        company="Walt Disney Co",
        source_type=SourceType.ANNUAL_REPORT,
        identifier=f"10-K {key}",
        key=key,
        published_on=datetime.fromisoformat(published).date(),
        reporting_period=None,
        document_format="html",
        language="en",
        location=f"https://www.sec.gov/Archives/{key}",
        provider="SEC EDGAR",
        authority=SourceAuthority.REGULATOR_FILED,
        verification=(IdentityCheck.REGISTER_INDEXED,),
    )


def measured_share() -> MeasuredShare:
    """A segment's size as the two cells it was measured out of."""

    def figure(label: str, printed: str, value: float, row: int) -> ReportedFigure:
        return ReportedFigure(
            label=label,
            column_header="2025",
            printed=printed,
            value=value,
            cell=CellReference(table=6, row=row, column=1),
            caption="($ in millions)",
        )

    return MeasuredShare(
        numerator=figure("Experiences", "36,156", 36156.0, 3),
        denominator=figure("Revenues", "94,425", 94425.0, 5),
    )


def knowledge(accession: str = ACCESSION, filed: str = "2025-11-13"):
    return CompanyKnowledge(
        symbol="DIS",
        description="A diversified worldwide entertainment company.",
        segments=(
            BusinessSegment(
                name="Experiences",
                revenue=measured_share(),
                description=SegmentDescription(
                    evidence=DescribedSegment(
                        quoted="The Experiences segment operates theme parks",
                        under="Experiences",
                        distance=0,
                    ),
                    revenue_models=(RevenueModel.TRANSACTION, RevenueModel.RETAIL),
                ),
            ),
        ),
        source=source(accession, filed),
        reading=Provenance(source="10-K via SEC EDGAR", observed_at=datetime.now(UTC)),
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
            business_description="The Experiences segment operates theme parks.",
            performance_discussion="",
        )


class ResolverStub:
    """Stands in for the resolver, so the service stays provider-blind."""

    def __init__(self, provider: ProviderStub) -> None:
        self.provider = provider

    def resolve(self, symbol: str):
        return self.provider.resolve(symbol), self.provider


class ExtractorStub:
    def __init__(self) -> None:
        self.extractions = 0

    async def extract(self, symbol: str, document: SourceDocument) -> CompanyKnowledge:
        self.extractions += 1

        return knowledge()


def service(tmp_path: Path, provider: ProviderStub, extractor: ExtractorStub):
    return CompanyKnowledgeService(
        store=JsonCompanyKnowledgeStore(tmp_path),
        sources=ResolverStub(provider),  # type: ignore[arg-type]
        extractor=extractor,  # type: ignore[arg-type]
    )


def test_a_filing_is_read_and_extracted_once_ever(tmp_path: Path) -> None:
    """
    The saving the accession key exists for.

    A filing is immutable, so knowledge read from it never needs reading
    again. The second cycle costs one small lookup — not the megabytes of
    the document, and not the model calls over it.
    """

    filings = ProviderStub()
    extractor = ExtractorStub()

    first = asyncio.run(service(tmp_path, filings, extractor).knowledge("DIS"))
    second = asyncio.run(service(tmp_path, filings, extractor).knowledge("DIS"))

    assert first.knowledge is not None
    assert second.knowledge is not None
    assert second.knowledge.source.key == ACCESSION

    assert filings.lookups == 2
    assert filings.documents_read == 1
    assert extractor.extractions == 1

    # And the states say which cycle paid for it.
    assert first.state is KnowledgeState.AVAILABLE_ACQUIRED
    assert second.state is KnowledgeState.AVAILABLE_CACHED


def test_a_newer_filing_is_read_because_it_is_a_different_document(
    tmp_path: Path,
) -> None:
    filings = ProviderStub()
    extractor = ExtractorStub()

    asyncio.run(service(tmp_path, filings, extractor).knowledge("DIS"))

    JsonCompanyKnowledgeStore(tmp_path).write(knowledge())

    filings.current = source("0001744489-26-000001", "2026-11-12")

    asyncio.run(service(tmp_path, filings, extractor).knowledge("DIS"))

    assert filings.documents_read == 2
    assert extractor.extractions == 2


def test_a_company_with_no_readable_filing_says_so(tmp_path: Path) -> None:
    """
    Reach, stated as reach.

    EDGAR holds SEC registrants. A company listed only in Europe files
    with its own regulator, and the platform reports that rather than
    describing the business from a lesser source.
    """

    filings = ProviderStub(unavailable="BNP.PA is not listed with the SEC.")

    outcome = asyncio.run(
        service(tmp_path, filings, ExtractorStub()).knowledge("BNP.PA")
    )

    assert outcome.knowledge is None
    assert outcome.state is KnowledgeState.UNAVAILABLE

    # A gap in coverage, not an outage: asking the same provider again
    # will produce the same answer, and a different one might not.
    assert outcome.state.may_succeed_later is False
    assert outcome.absent_because == "BNP.PA is not listed with the SEC."


def test_what_was_already_known_survives_a_provider_that_stops_answering(
    tmp_path: Path,
) -> None:
    """
    Knowledge is structural: last year's filing still describes the
    business. A lookup that fails today does not unlearn it.
    """

    JsonCompanyKnowledgeStore(tmp_path).write(knowledge())

    filings = ProviderStub(
        unavailable="The SEC index could not be read.",
        outage=True,
    )

    outcome = asyncio.run(service(tmp_path, filings, ExtractorStub()).knowledge("DIS"))

    assert outcome.knowledge is not None
    assert outcome.knowledge.source.key == ACCESSION

    # The reading stands and the state says it is the older one, so a
    # surface can report coverage without pretending the lookup worked.
    assert outcome.state is KnowledgeState.PROVIDER_ERROR
    assert outcome.state.may_succeed_later is True
    assert outcome.absent_because == "The SEC index could not be read."


def test_the_store_returns_the_latest_filing_by_when_it_was_filed(
    tmp_path: Path,
) -> None:
    """Reading an older filing later must not make it the current word."""

    store = JsonCompanyKnowledgeStore(tmp_path)

    store.write(knowledge("0001744489-26-000001", "2026-11-12"))
    store.write(knowledge(ACCESSION, "2025-11-13"))

    latest = store.latest("DIS")

    assert latest is not None
    assert latest.source.published_on.isoformat() == "2026-11-12"


def test_knowledge_survives_the_round_trip_to_disk(tmp_path: Path) -> None:
    store = JsonCompanyKnowledgeStore(tmp_path)

    store.write(knowledge())

    restored = store.read("DIS", ACCESSION)

    assert restored is not None
    assert restored.segments[0].name == "Experiences"
    assert restored.segments[0].revenue_models == (
        RevenueModel.TRANSACTION,
        RevenueModel.RETAIL,
    )

    # The size survives as the two figures it was measured from, not as
    # the answer. A stored share would be a number nothing had checked;
    # what is kept is the evidence, and the share is worked out again.
    revenue = restored.segments[0].revenue

    assert revenue is not None
    assert revenue.numerator.printed == "36,156"
    assert revenue.numerator.label == "Experiences"
    assert revenue.denominator.printed == "94,425"
    assert revenue.numerator.cell == CellReference(table=6, row=3, column=1)
    assert round(restored.measured_share, 4) == 0.3829

    # The audit trail is part of the knowledge, not part of the run that
    # produced it. A reader months later must still be able to see what
    # kind of source this was and which identity checks actually held.
    assert restored.source.authority is SourceAuthority.REGULATOR_FILED
    assert restored.source.verification == (IdentityCheck.REGISTER_INDEXED,)


def test_an_entry_holding_a_bare_share_is_read_again(tmp_path: Path) -> None:
    """
    A share stored without the figures it was measured from is not upgraded.

    Entries written when a segment's size was a single number carry no
    cell addresses, no row labels and no total — there is nothing to
    check them against, which is precisely what the reading version
    changed. Back-filling would mean inventing the evidence that was
    never captured, so the entry is absent and the document, which is
    immutable and still there, is read again.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.write(knowledge())

    stored = next(tmp_path.glob("*.json"))
    older = json.loads(stored.read_text())

    older["schema_version"] = 3
    older["segments"][0].pop("revenue")
    older["segments"][0]["revenue_share"] = 0.383

    stored.write_text(json.dumps(older))

    assert store.read("DIS", ACCESSION) is None


def test_an_entry_written_before_the_audit_trail_is_read_again(
    tmp_path: Path,
) -> None:
    """
    The source is immutable; the reading of it is not.

    Entries written before authority and verification were captured are
    missing them, and they will never refresh on their own because the
    document behind them has not changed. So such an entry is treated as
    absent and the document is read again — never back-filled with an
    authority nobody established.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.write(knowledge())

    stored = next(tmp_path.glob("*.json"))
    older = json.loads(stored.read_text())
    older["schema_version"] = 2
    older["source"].pop("authority")
    older["source"].pop("verification")
    stored.write_text(json.dumps(older))

    assert store.read("DIS", ACCESSION) is None


def test_an_unreadable_entry_is_absent_rather_than_repaired(tmp_path: Path) -> None:
    """A guessed record would be indistinguishable from a read one."""

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.write(knowledge())

    corrupt = next(tmp_path.glob("DIS.*.json"))
    corrupt.write_text("{ not json", encoding="utf-8")

    assert store.read("DIS", ACCESSION) is None
    assert store.latest("DIS") is None


def test_a_repaired_span_never_comes_back_off_disk_as_a_first_reading(
    tmp_path: Path,
) -> None:
    """
    Provenance that does not survive the round trip is not provenance.

    A repaired citation is as good as any other evidence — it passed the
    identical contract — but how the platform arrived at it is part of
    what a reader is owed, and an entry that forgot would present the
    second answer as the first.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)

    original = knowledge()
    described = original.segments[0].description
    assert described is not None

    store.write(
        replace(
            original,
            segments=(
                replace(
                    original.segments[0],
                    description=replace(
                        described,
                        repair=DescriptionRepair(
                            first_refused_because=(
                                "It quotes words printed under 'Entertainment'."
                            ),
                            reader="reader-9",
                        ),
                    ),
                ),
            ),
        )
    )

    restored = store.read("DIS", ACCESSION)

    assert restored is not None

    repair = restored.segments[0].description.repair  # type: ignore[union-attr]

    assert repair is not None
    assert repair.reader == "reader-9"
    assert "Entertainment" in repair.first_refused_because


def test_an_unrepaired_description_stores_nothing_about_repairs(
    tmp_path: Path,
) -> None:
    """The ordinary case stays the ordinary case, on disk as in memory."""

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.write(knowledge())

    restored = store.read("DIS", ACCESSION)

    assert restored is not None
    assert restored.segments[0].description is not None
    assert not restored.segments[0].description.was_repaired
