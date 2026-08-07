"""Measuring how reproducibly this platform reads one unchanged document."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledge,
    RevenueModel,
    SegmentDescription,
)
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.prose_evidence import DescribedSegment, Ownership
from app.domain.provenance import Provenance
from app.domain.reader_stability import agreement
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
)
from app.services.company_knowledge_extractor import ExtractionRejected
from app.services.reader_calibration import (
    ReaderCalibrationService,
    ReaderCalibrationUnavailable,
)

SOURCE = PrimarySource(
    symbol="DIS",
    company="The Walt Disney Company",
    source_type=SourceType.ANNUAL_REPORT,
    identifier="10-K 0001744489-25-000155",
    key="0001744489-25-000155",
    published_on=datetime(2025, 11, 13, tzinfo=UTC).date(),
    reporting_period=None,
    document_format="html",
    language="en",
    location="https://example.invalid/10k.htm",
    provider="SEC EDGAR",
    authority=SourceAuthority.REGULATOR_FILED,
    verification=(IdentityCheck.REGISTER_INDEXED,),
)

DOCUMENT = SourceDocument(
    source=SOURCE,
    business_description="The Entertainment segment produces film and television.",
    performance_discussion="Segment results.",
)


def figure(label: str, value: float, row: int) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header="2025",
        printed=f"{value:,.0f}",
        value=value,
        cell=CellReference(table=0, row=row, column=1),
        caption="Revenues by segment",
    )


def segment(
    name: str,
    *,
    share: float | None = None,
    earns: tuple[RevenueModel, ...] = (RevenueModel.SUBSCRIPTION,),
    quoted: str = "produces film and television",
    row: int = 1,
) -> BusinessSegment:
    return BusinessSegment(
        name=name,
        revenue=(
            MeasuredShare(
                numerator=figure(name, 100.0 * share, row),
                denominator=figure("Revenues", 100.0, 9),
            )
            if share is not None
            else None
        ),
        description=(
            SegmentDescription(
                evidence=DescribedSegment(
                    quoted=quoted,
                    under=name,
                    distance=0,
                    ownership=Ownership.STRUCTURE,
                ),
                revenue_models=earns,
            )
            if earns or quoted
            else None
        ),
    )


def knowledge(*segments: BusinessSegment) -> CompanyKnowledge:
    return CompanyKnowledge(
        symbol="DIS",
        description="A diversified entertainment company.",
        segments=segments,
        source=SOURCE,
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=datetime(2026, 8, 7, tzinfo=UTC),
        ),
    )


class Sources:
    """The resolver with the network replaced."""

    def __init__(self, unavailable: str | None = None) -> None:
        self.unavailable = unavailable
        self.fetches = 0

    def resolve(self, symbol: str):
        if self.unavailable:
            raise PrimarySourceUnavailable(self.unavailable)

        return SOURCE, self

    def fetch(self, source: PrimarySource) -> SourceDocument:
        self.fetches += 1
        return DOCUMENT


class Readings:
    """A reader that answers each call with the next scripted outcome."""

    def __init__(self, *outcomes: CompanyKnowledge | str) -> None:
        self._outcomes = list(outcomes)
        self.documents: list[SourceDocument] = []

    async def extract(self, symbol: str, document: SourceDocument):
        self.documents.append(document)

        outcome = self._outcomes.pop(0)

        if isinstance(outcome, str):
            raise ExtractionRejected(outcome)

        return outcome


def calibrate(sources: Sources, reader: Readings, readings: int = 3):
    service = ReaderCalibrationService(sources=sources, extractor=reader)

    return asyncio.run(service.calibrate("DIS", readings))


# ── the measurement ─────────────────────────────────────────────────


def test_readings_that_agree_are_reported_as_settled() -> None:
    """The baseline this instrument exists to establish."""

    stable = knowledge(segment("Entertainment", share=0.45))

    measured = calibrate(Sources(), Readings(stable, stable, stable))

    assert measured.read == 3
    assert measured.identity.settled
    assert measured.archetype.settled
    assert measured.segments[0].size.stability == 1.0


def test_a_way_of_earning_that_moves_between_readings_is_caught() -> None:
    """
    NVIDIA's shape, and the finding that produced this instrument: the
    sizes did not move, the archetype did, because one reading of
    unchanged prose reported one fewer way of earning.
    """

    both = knowledge(
        segment(
            "Graphics",
            share=0.10,
            earns=(RevenueModel.MANUFACTURING, RevenueModel.SERVICES),
        )
    )
    one = knowledge(
        segment("Graphics", share=0.10, earns=(RevenueModel.MANUFACTURING,))
    )

    measured = calibrate(Sources(), Readings(both, one, both))

    graphics = measured.segments[0]

    assert graphics.size.settled
    assert not graphics.earning.settled
    assert graphics.earning.agreeing == 2
    assert {answer.stated for answer in graphics.earning.answers} == {
        "manufacturing, services",
        "manufacturing",
    }


def test_every_answer_is_kept_and_not_only_the_winner() -> None:
    """
    Two readings splitting evenly and nine disagreeing separately both
    read as low agreement, and they are entirely different findings.
    """

    measured = calibrate(
        Sources(),
        Readings(
            knowledge(segment("A", quoted="one")),
            knowledge(segment("A", quoted="two")),
            knowledge(segment("A", quoted="three")),
        ),
    )

    assert len(measured.segments[0].description.answers) == 3
    assert measured.segments[0].description.agreeing == 1


def test_a_segment_only_some_readings_named_is_counted_over_those() -> None:
    """
    A segment seven readings never mentioned has no opinion in them to
    disagree with. Folding those in would report one instability twice
    — once as a missing segment and again as a size nobody measured.
    """

    measured = calibrate(
        Sources(),
        Readings(
            knowledge(segment("Entertainment", share=0.45), segment("Sports", row=2)),
            knowledge(segment("Entertainment", share=0.45)),
            knowledge(segment("Entertainment", share=0.45)),
        ),
    )

    entertainment, sports = measured.segments

    assert entertainment.named_in == 3
    assert sports.named_in == 1

    # Not "1 of 3": the two readings that never named Sports said nothing
    # about its size either.
    assert sports.size.readings == 1
    assert sports.size.stability == 1.0

    assert not measured.identity.settled


def test_a_refused_reading_is_an_outcome_rather_than_an_error() -> None:
    """
    The share of readings that produce nothing is part of the noise
    floor. A calibration that raised on the first refusal would measure
    only the documents that happen to be easy.
    """

    good = knowledge(segment("Entertainment", share=0.45))

    measured = calibrate(
        Sources(), Readings(good, "The span was not in the text.", good)
    )

    assert measured.read == 2
    assert measured.readings == 3
    assert measured.completed == pytest.approx(2 / 3)
    assert measured.refusals.modal is not None
    assert measured.refusals.modal.stated == "The span was not in the text."


def test_a_document_no_reading_could_read_reports_that_and_nothing_else() -> None:
    """Which is the measurement, not a failure to take one."""

    measured = calibrate(Sources(), Readings("refused", "refused", "refused"))

    assert measured.read == 0
    assert measured.completed == 0.0
    assert measured.identity.modal is None
    assert measured.archetype.modal is None


# ── the boundaries ──────────────────────────────────────────────────


def test_the_document_is_fetched_once_and_given_to_every_reading() -> None:
    """
    A primary source is immutable, so one fetch *is* every reading's
    document — and anything that then differs between readings came
    from this platform, which is the whole point of the instrument.
    """

    sources = Sources()
    reader = Readings(*(knowledge(segment("Entertainment", share=0.45)),) * 4)

    calibrate(sources, reader, readings=4)

    assert sources.fetches == 1
    assert reader.documents == [DOCUMENT] * 4


def test_a_calibration_stores_nothing_it_reads(tmp_path) -> None:
    """
    The boundary, not an omission. A calibration that wrote what it read
    would let whichever draw ran last become this platform's account of
    the company — the exact failure it exists to quantify.
    """

    from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore

    store = JsonCompanyKnowledgeStore(tmp_path)

    calibrate(
        Sources(),
        Readings(*(knowledge(segment("Entertainment", share=0.45)),) * 3),
    )

    assert store.read("DIS", SOURCE.key) is None
    assert list(tmp_path.iterdir()) == []


def test_one_reading_is_refused_because_it_compares_nothing() -> None:
    service = ReaderCalibrationService(sources=Sources(), extractor=Readings())

    with pytest.raises(ReaderCalibrationUnavailable) as refused:
        asyncio.run(service.calibrate("DIS", 1))

    assert "at least two" in str(refused.value)


def test_a_document_that_cannot_be_obtained_is_worded_rather_than_raised_raw() -> None:
    service = ReaderCalibrationService(
        sources=Sources(unavailable="EDGAR does not list ZZZZ."),
        extractor=Readings(),
    )

    with pytest.raises(ReaderCalibrationUnavailable) as refused:
        asyncio.run(service.calibrate("ZZZZ", 3))

    assert "EDGAR does not list ZZZZ." in str(refused.value)


# ── the arithmetic ──────────────────────────────────────────────────


def test_a_question_no_reading_answered_has_no_stability_rather_than_zero() -> None:
    """
    Nothing answered and everything disagreed are different findings,
    and averaging them together would report a reading that never
    happened as a disagreement.
    """

    assert agreement("nothing", ()).stability is None
    assert agreement("split", ("a", "b")).stability == 0.5


def test_the_platform_never_calls_an_observed_share_a_probability() -> None:
    """
    An agreement over N readings is exactly that. Stating it as the
    chance a further reading agrees would invent a number nobody
    measured.
    """

    measured = agreement("earning", ("a", "a", "b"))

    assert "of 3 readings agreed" in measured.stated()


def test_a_size_that_moves_to_another_cell_is_a_disagreement() -> None:
    """
    Even at the same share. Two readings agreeing on a number by way of
    different cells have agreed on less than they appear to, and this
    platform's evidence is the cell.
    """

    same_share_other_cell = replace(
        segment("Entertainment", share=0.45),
        revenue=MeasuredShare(
            numerator=figure("Entertainment", 45.0, 4),
            denominator=figure("Revenues", 100.0, 9),
        ),
    )

    measured = calibrate(
        Sources(),
        Readings(
            knowledge(segment("Entertainment", share=0.45)),
            knowledge(same_share_other_cell),
        ),
        readings=2,
    )

    assert not measured.segments[0].size.settled


def test_establishing_a_description_is_counted_apart_from_the_span() -> None:
    """
    Measured on Caterpillar, ten readings cited one sentence about
    Resource Industries eight ways — trimmed at "quarry", at "quarry and
    aggregates", with and without the full stop. As spans that is 2 of
    10; as an account of what the segment does it is 10 of 10, and only
    the second reaches a decision.
    """

    measured = calibrate(
        Sources(),
        Readings(
            knowledge(segment("A", quoted="supporting customers in mining")),
            knowledge(segment("A", quoted="supporting customers in mining.")),
            knowledge(segment("A", quoted="supporting customers in mining and quarry")),
        ),
    )

    described = measured.segments[0]

    assert described.described.settled
    assert described.described.stability == 1.0

    assert not described.description.settled
    assert described.description.agreeing == 1


def test_a_description_that_is_sometimes_refused_is_not_settled() -> None:
    """The span metric cannot see this on its own — every refusal quotes nothing."""

    described = knowledge(segment("A", quoted="what it does"))
    refused = knowledge(replace(segment("A"), description=None))

    measured = calibrate(Sources(), Readings(described, refused, described))

    assert not measured.segments[0].described.settled
    assert measured.segments[0].described.agreeing == 2
