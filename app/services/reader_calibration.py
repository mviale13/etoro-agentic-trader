"""Read one unchanged document repeatedly, and report how far it agrees.

A measurement, and deliberately nothing else. This service improves no
reading, repairs no citation and stores no knowledge — and the last of
those is a boundary rather than an omission. A calibration that wrote
what it read would let whichever draw happened to run last become the
platform's account of the company, which is the exact failure it exists
to quantify.

It is also the reason the document is fetched once and handed to every
reading. A primary source is immutable, so one fetch *is* every
reading's document; anything that differed between the readings would
have come from this platform, and this is the instrument for saying how
much does.
"""

from __future__ import annotations

import asyncio

from app.domain.company_knowledge import BusinessSegment, CompanyKnowledgeObservation
from app.domain.knowledge_consensus import consensus_of
from app.domain.primary_source import (
    PrimarySourceUnavailable,
    SourceDocument,
)
from app.domain.reader_stability import (
    ReaderStability,
    SegmentStability,
    agreement,
)
from app.providers.primary_source_provider import PrimarySourceResolver
from app.services.archetype_engine import classify
from app.services.company_knowledge_extractor import (
    CompanyKnowledgeExtractor,
    ExtractionRejected,
)
from app.services.company_knowledge_reader import resolve_reader

#: How many readings a calibration runs when the caller names no number.
#: Enough to tell a settled answer from a split one; not a sample size
#: that supports an interval, which is why nothing here reports one.
DEFAULT_READINGS = 5

#: How many readings are in flight at once. The readings are independent
#: by construction — that is what is being measured — so this is only a
#: courtesy to the provider's rate limit.
CONCURRENT = 4


class ReaderCalibrationUnavailable(Exception):
    """No calibration could be run, with the reason worded."""


class ReaderCalibrationService:
    """The acquisition layer's own variance, measured on real documents."""

    def __init__(
        self,
        sources: PrimarySourceResolver | None = None,
        extractor: CompanyKnowledgeExtractor | None = None,
    ) -> None:
        self._sources = sources or PrimarySourceResolver()

        if extractor is not None:
            self._extractor = extractor
            return

        resolved = resolve_reader()

        if isinstance(resolved, str):
            # The same worded reason every other surface shows. A
            # calibration with no reader measures nothing, and saying so
            # is the whole answer.
            raise ReaderCalibrationUnavailable(resolved)

        self._extractor = resolved

    async def calibrate(
        self,
        symbol: str,
        readings: int = DEFAULT_READINGS,
    ) -> ReaderStability:
        """Read this company's current document `readings` times over."""

        if readings < 2:
            raise ReaderCalibrationUnavailable(
                "A calibration compares readings with each other, so it needs "
                f"at least two. {readings} was asked for."
            )

        try:
            source, provider = self._sources.resolve(symbol)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            raise ReaderCalibrationUnavailable(
                f"No document could be obtained for {symbol}, so the reader "
                f"could not be measured on it. {unavailable}"
            ) from unavailable

        outcomes = await self._read_repeatedly(symbol, document, readings)

        read = [
            outcome
            for outcome in outcomes
            if isinstance(outcome, CompanyKnowledgeObservation)
        ]

        return ReaderStability(
            symbol=symbol,
            source=source.stated(),
            reader=(read[0].reading.source if read else "no reading completed"),
            readings=readings,
            read=len(read),
            refusals=agreement(
                "why a reading produced nothing",
                (str(outcome) for outcome in outcomes if isinstance(outcome, str)),
            ),
            identity=agreement(
                "which segments the document names",
                (_identity(knowledge) for knowledge in read),
            ),
            segments=_segments(read),
            # What the rules would conclude from each single reading —
            # which is the question this instrument measures, so each
            # observation is classified alone, as a consensus of one at
            # a quorum of one. The decision path never does this: its
            # quorum is fixed in the domain and its archetype is
            # classify(consensus), not a vote over per-reading verdicts.
            archetype=agreement(
                "what the rules concluded",
                (
                    classify(consensus_of((knowledge,), quorum=1)).stated
                    for knowledge in read
                ),
            ),
        )

    async def _read_repeatedly(
        self,
        symbol: str,
        document: SourceDocument,
        readings: int,
    ) -> list[CompanyKnowledgeObservation | str]:
        """Every reading's outcome, in the order they were asked for.

        A refusal is an outcome rather than an error. The share of
        readings that come back with nothing is part of what is being
        measured, and a calibration that raised on the first one would
        report the noise floor of the documents that happen to be easy.
        """

        limit = asyncio.Semaphore(CONCURRENT)

        extractor = self._extractor

        async def once() -> CompanyKnowledgeObservation | str:
            async with limit:
                try:
                    return await extractor.extract(symbol, document)
                except ExtractionRejected as rejected:
                    return str(rejected)

        return list(await asyncio.gather(*(once() for _ in range(readings))))


def _identity(knowledge: CompanyKnowledgeObservation) -> str:
    """The set of segments one reading named, as a comparable answer.

    Sorted, because the order a filing's segments come back in is not a
    claim this platform makes about the company and two readings that
    differ only in it agree about everything that matters.
    """

    if not knowledge.segments:
        return "no segments"

    return ", ".join(sorted(segment.name for segment in knowledge.segments))


def _segments(
    readings: list[CompanyKnowledgeObservation],
) -> tuple[SegmentStability, ...]:
    """Each segment's stability, counted over the readings that named it."""

    by_name: dict[str, list[BusinessSegment]] = {}

    for knowledge in readings:
        for segment in knowledge.segments:
            by_name.setdefault(segment.name, []).append(segment)

    return tuple(
        SegmentStability(
            name=name,
            named_in=len(found),
            size=agreement(
                "its size",
                (_size(segment) for segment in found),
            ),
            earning=agreement(
                "how it earns",
                (_earning(segment) for segment in found),
            ),
            described=agreement(
                "whether the filing was shown to describe it",
                (_described(segment) for segment in found),
            ),
            description=agreement(
                "which span was cited for that",
                (_description(segment) for segment in found),
            ),
        )
        for name, found in sorted(by_name.items())
    )


def _size(segment: BusinessSegment) -> str:
    """A segment's size as a comparable answer, or its absence.

    To the whole percentage point. Two readings citing the same cells
    produce a share identical to every decimal place, so any looser
    rounding would only hide a genuine disagreement about which cell was
    read — and a tighter one would report float arithmetic as instability.
    """

    if segment.revenue is None:
        return "no size measured"

    return f"{segment.revenue.share:.0%} ({segment.revenue.numerator.cell.stated()})"


def _earning(segment: BusinessSegment) -> str:
    """The ways of earning one reading established, as a comparable answer."""

    if not segment.revenue_models:
        return "no way of earning established"

    return ", ".join(sorted(model.value for model in segment.revenue_models))


def _described(segment: BusinessSegment) -> str:
    """Whether this reading established a description at all.

    The question the rest of the platform actually consumes. A segment
    described is a segment whose ways of earning can be read; which
    sentence proved it is evidence, and is counted separately.
    """

    return "described" if segment.description is not None else "not described"


def _description(segment: BusinessSegment) -> str:
    """The span that survived applicability, or the fact that none did.

    The span itself, not merely whether there was one. Two readings that
    both establish a description have agreed on something real; two that
    quote different sentences have agreed on less, and a report that
    could not tell them apart would overstate how settled this platform's
    account of a business is.
    """

    if segment.description is None:
        return "no description established"

    return f'"{segment.quoted}"'
