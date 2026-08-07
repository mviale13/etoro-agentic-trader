"""Structural knowledge is acquired once per filing, and then kept."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    DescriptionRepair,
    RevenueModel,
    SegmentDescription,
)
from app.domain.knowledge_consensus import (
    QUORUM,
    ConsensusState,
    consensus_of,
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
from app.domain.prose_evidence import DescribedSegment, Ownership
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
)
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.company_knowledge_extractor import ExtractionRejected
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
    return CompanyKnowledgeObservation(
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

    async def extract(
        self, symbol: str, document: SourceDocument
    ) -> CompanyKnowledgeObservation:
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

    JsonCompanyKnowledgeStore(tmp_path).append(knowledge())

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

    JsonCompanyKnowledgeStore(tmp_path).append(knowledge())

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

    store.append(knowledge("0001744489-26-000001", "2026-11-12"))
    store.append(knowledge(ACCESSION, "2025-11-13"))

    latest = store.latest("DIS")

    assert len(latest) == 1
    assert latest[0].source.published_on.isoformat() == "2026-11-12"


def test_knowledge_survives_the_round_trip_to_disk(tmp_path: Path) -> None:
    store = JsonCompanyKnowledgeStore(tmp_path)

    store.append(knowledge())

    observations = store.read("DIS", ACCESSION)

    assert len(observations) == 1

    restored = observations[0]
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


def test_which_mechanism_owned_a_description_survives_the_round_trip(
    tmp_path: Path,
) -> None:
    """
    "Inside the section headed Reality Labs Products" and "51 characters
    after a mention of Reality Labs" are different strengths of proof.
    An entry that lost the difference would read as the stronger one.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)

    structural = replace(
        knowledge(),
        segments=(
            replace(
                knowledge().segments[0],
                description=SegmentDescription(
                    evidence=DescribedSegment(
                        quoted="operates theme parks",
                        under="Experiences Products",
                        distance=20,
                        ownership=Ownership.STRUCTURE,
                    ),
                    revenue_models=(RevenueModel.TRANSACTION,),
                ),
            ),
        ),
    )

    store.append(structural)

    observations = store.read("DIS", ACCESSION)

    assert len(observations) == 1

    restored = observations[0]

    description = restored.segments[0].description

    assert description is not None
    assert description.evidence.ownership is Ownership.STRUCTURE
    assert "into the section the document heads" in description.evidence.stated()


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
    store.append(knowledge())

    stored = next(tmp_path.glob("*.json"))
    older = json.loads(stored.read_text())

    older["schema_version"] = 3
    segments = older["observations"][0]["segments"]
    segments[0].pop("revenue")
    segments[0]["revenue_share"] = 0.383

    stored.write_text(json.dumps(older))

    assert store.read("DIS", ACCESSION) == ()


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
    store.append(knowledge())

    stored = next(tmp_path.glob("*.json"))
    older = json.loads(stored.read_text())
    older["schema_version"] = 2
    older["source"].pop("authority")
    older["source"].pop("verification")
    stored.write_text(json.dumps(older))

    assert store.read("DIS", ACCESSION) == ()


def test_an_unreadable_entry_is_absent_rather_than_repaired(tmp_path: Path) -> None:
    """A guessed record would be indistinguishable from a read one."""

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.append(knowledge())

    corrupt = next(tmp_path.glob("DIS.*.json"))
    corrupt.write_text("{ not json", encoding="utf-8")

    assert store.read("DIS", ACCESSION) == ()
    assert store.latest("DIS") == ()


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

    store.append(
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

    observations = store.read("DIS", ACCESSION)

    assert len(observations) == 1

    restored = observations[0]

    repair = restored.segments[0].description.repair  # type: ignore[union-attr]

    assert repair is not None
    assert repair.reader == "reader-9"
    assert "Entertainment" in repair.first_refused_because


def test_an_unrepaired_description_stores_nothing_about_repairs(
    tmp_path: Path,
) -> None:
    """The ordinary case stays the ordinary case, on disk as in memory."""

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.append(knowledge())

    observations = store.read("DIS", ACCESSION)

    assert len(observations) == 1

    restored = observations[0]
    assert restored.segments[0].description is not None
    assert not restored.segments[0].description.was_repaired


def test_why_a_size_is_absent_survives_the_round_trip_to_disk(
    tmp_path: Path,
) -> None:
    """
    An absence stored without its reason is an absence a later session
    has to re-derive from outside the platform. This one was: the sizes
    Caterpillar's 10-K prints looked like a gap in the filing for as
    long as nothing recorded that the reading had never seen its tables.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)

    stored = knowledge()

    store.append(
        replace(
            stored,
            segments=(
                replace(
                    stored.segments[0],
                    revenue=None,
                    unmeasured_because="This filing's discussion prints no table.",
                ),
            ),
        )
    )

    observations = store.read("DIS", ACCESSION)

    assert len(observations) == 1

    restored = observations[0]
    assert restored.segments[0].revenue is None
    assert (
        restored.segments[0].unmeasured_because
        == "This filing's discussion prints no table."
    )


# ── observations and consensus ──────────────────────────────────────


def test_what_the_service_serves_is_a_consensus_with_its_width_stated(
    tmp_path: Path,
) -> None:
    """One acquisition is one observation, labeled as exactly that."""

    outcome = asyncio.run(
        service(tmp_path, ProviderStub(), ExtractorStub()).knowledge("DIS")
    )

    assert outcome.knowledge is not None
    assert outcome.knowledge.observation_count == 1
    assert outcome.knowledge.state is ConsensusState.INSUFFICIENT_QUORUM
    assert "a single reading, not a consensus" in outcome.knowledge.reading.source


def test_observe_fills_the_quorum_and_stops_on_the_count(tmp_path: Path) -> None:
    """
    The stopping rule references the count and never the content — an
    entry stops at quorum whether its claims settled or not.
    """

    provider = ProviderStub()
    extractor = ExtractorStub()
    knowing = service(tmp_path, provider, extractor)

    asyncio.run(knowing.knowledge("DIS"))

    assert extractor.extractions == 1

    outcome = asyncio.run(knowing.observe("DIS"))

    assert extractor.extractions == QUORUM
    assert outcome.knowledge is not None
    assert outcome.knowledge.observation_count == QUORUM
    assert outcome.knowledge.state is ConsensusState.QUORATE

    # Asking again observes nothing further: the quorum is filled.
    asyncio.run(knowing.observe("DIS"))

    assert extractor.extractions == QUORUM


def test_observe_reaches_a_deeper_target_and_still_stops_on_the_count(
    tmp_path: Path,
) -> None:
    """
    The deeper explicit spend: a target past the quorum, fixed before
    anything is read. The rule is unchanged — the count stops the run,
    never the content — and a target the entry already meets observes
    nothing further.
    """

    provider = ProviderStub()
    extractor = ExtractorStub()
    knowing = service(tmp_path, provider, extractor)

    asyncio.run(knowing.observe("DIS"))

    assert extractor.extractions == QUORUM

    outcome = asyncio.run(knowing.observe("DIS", target=QUORUM + 2))

    assert extractor.extractions == QUORUM + 2
    assert outcome.knowledge is not None
    assert outcome.knowledge.observation_count == QUORUM + 2
    assert outcome.knowledge.state is ConsensusState.QUORATE

    # A shallower target than the entry's width spends nothing.
    asyncio.run(knowing.observe("DIS", target=3))

    assert extractor.extractions == QUORUM + 2


def test_a_refused_reading_ends_the_observe_run_and_keeps_what_stands(
    tmp_path: Path,
) -> None:
    class RefusingAfterOne(ExtractorStub):
        async def extract(self, symbol: str, document: SourceDocument):
            if self.extractions >= 1:
                raise ExtractionRejected("The span was not in the text.")

            return await super().extract(symbol, document)

    outcome = asyncio.run(
        service(tmp_path, ProviderStub(), RefusingAfterOne()).observe("DIS")
    )

    assert outcome.knowledge is not None
    assert outcome.knowledge.observation_count == 1
    assert outcome.knowledge.state is ConsensusState.INSUFFICIENT_QUORUM
    assert "was not in the text" in (outcome.absent_because or "")


def test_a_schema_8_entry_serves_as_one_observation_below_quorum(
    tmp_path: Path,
) -> None:
    """
    The carried-forward corpus: a single-reading entry keeps operating,
    labeled, and is never called settled.
    """

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.append(knowledge())

    # Rewrite the entry as its schema-8 form: the observation body at
    # the top level, exactly as the previous store wrote it.
    path = next(tmp_path.glob("*.json"))
    entry = json.loads(path.read_text())
    observation = entry["observations"][0]
    entry.pop("observations")
    entry.update(observation)
    entry["schema_version"] = 8
    path.write_text(json.dumps(entry))

    restored = store.read("DIS", ACCESSION)

    assert len(restored) == 1

    consensus = consensus_of(restored)

    assert consensus.observation_count == 1
    assert consensus.state is ConsensusState.INSUFFICIENT_QUORUM


def test_appending_to_a_schema_8_entry_carries_the_observation_forward(
    tmp_path: Path,
) -> None:
    """The relabeling is real: the old reading survives beside the new one."""

    store = JsonCompanyKnowledgeStore(tmp_path)
    store.append(knowledge())

    path = next(tmp_path.glob("*.json"))
    entry = json.loads(path.read_text())
    observation = entry["observations"][0]
    entry.pop("observations")
    entry.update(observation)
    entry["schema_version"] = 8
    path.write_text(json.dumps(entry))

    store.append(knowledge())

    assert len(store.read("DIS", ACCESSION)) == 2
