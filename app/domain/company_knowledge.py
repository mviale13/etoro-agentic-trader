"""Structural facts about a business, read from its own annual report."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.primary_source import PrimarySource
from app.domain.prose_evidence import DescribedSegment
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import MeasuredShare


class RevenueModel(StrEnum):
    """How a segment actually earns.

    The dimension an industry code cannot express. Disney, Netflix and
    Meta share a sector; one sells tickets and licences, one sells
    subscriptions, one sells advertising, and no classification built on
    the sector can tell them apart.
    """

    SUBSCRIPTION = "subscription"
    ADVERTISING = "advertising"
    TRANSACTION = "transaction"
    LICENSING = "licensing"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    SERVICES = "services"
    COMMODITY = "commodity"
    FINANCIAL_SPREAD = "financial_spread"
    PREMIUMS = "premiums"
    ASSET_MANAGEMENT_FEES = "asset_management_fees"


@dataclass(frozen=True, slots=True)
class SegmentDescription:
    """
    What a segment does and how it earns, with proof it is said of *it*.

    One evidence contract for both, because both are read from the same
    prose. How a segment earns is a reading of what it does, so a
    description this platform cannot show applies to the segment cannot
    support a claim about its revenue model either — the two travel
    together or neither does.
    """

    #: The span, and the proof that the document says it of this segment
    #: rather than merely near it.
    evidence: DescribedSegment

    revenue_models: tuple[RevenueModel, ...]

    @property
    def quoted(self) -> str:
        """The filing's own words."""

        return self.evidence.quoted


@dataclass(frozen=True, slots=True)
class BusinessSegment:
    """One part of the business, as the company itself reports it.

    Three claims, evidenced three ways and degrading independently. They
    were once a single span asserting all of them at once, which meant a
    citation that failed took the whole segment with it — including facts
    that had been proven by something else entirely.

    - **Identity** — that the company has a part it calls this. Proven by
      the document naming it, which this platform locates rather than
      accepts.
    - **Size** — what it earned, as a fraction of a printed total. Proven
      by two cells of one table, checked against the document.
    - **Description** — what it does and how it earns. Proven by a span
      the document prints under this segment's own name.

    A segment whose size cannot be measured is still a segment. A segment
    whose description cannot be shown to apply keeps its name and its
    size, and says nothing about what it does — which is the honest
    outcome and the one that stops a footnote about restated prior-year
    figures being reported as what a company's car division sells.
    """

    #: The segment's name, as the document names it.
    name: str

    #: What this segment earned, as a fraction of a total the same table
    #: printed. None where the company described the segment without a
    #: figure this platform could locate in a table — which is common,
    #: and is not the same as the segment being small.
    revenue: MeasuredShare | None

    #: What it does and how it earns. None where the filing described the
    #: segment in words this platform could not show were about it.
    description: SegmentDescription | None

    #: Why there is no description, in words. An absence carries its
    #: reason everywhere else in this platform and this is no different:
    #: "the filing says nothing about this segment" and "the words cited
    #: for it are the ones it prints under another segment" are different
    #: facts about the reading, and only one of them is about the filing.
    undescribed_because: str | None = None

    @property
    def revenue_share(self) -> float | None:
        """
        The share of revenue this segment produced, 0.0 to 1.0.

        Derived rather than stored, and that is the point. The number is
        arithmetic over two figures a filer printed, so it is computed
        here from evidence that has been checked against the document
        rather than accepted from whatever read it.
        """

        return self.revenue.share if self.revenue is not None else None

    @property
    def revenue_models(self) -> tuple[RevenueModel, ...]:
        """How this segment earns, where the filing was shown to say so."""

        return self.description.revenue_models if self.description else ()

    @property
    def quoted(self) -> str:
        """The filing's own words about this segment, where there are any."""

        return self.description.quoted if self.description else ""


@dataclass(frozen=True, slots=True)
class CompanyKnowledge:
    """
    What this company does, from the document it is legally answerable for.

    Facts, never conclusions. What kind of investment this makes the
    company is a rule's decision, taken from these facts and stated
    separately — the same separation the Brain keeps between what it
    perceives and what the Artificial CIO decides.

    Every part of it is traceable to a dated filing a reader can open.
    """

    symbol: str

    #: What the company says it does, in its own words.
    description: str

    segments: tuple[BusinessSegment, ...]

    #: The document this was read from, whoever published it. Canonical:
    #: nothing downstream needs to know which regulator received it.
    source: PrimarySource

    reading: Provenance

    @property
    def has_segments(self) -> bool:
        """Whether the filing described the business in parts at all."""

        return bool(self.segments)

    @property
    def measured_share(self) -> float:
        """How much of revenue the segments with a figure account for."""

        return sum(
            segment.revenue_share
            for segment in self.segments
            if segment.revenue_share is not None
        )

    @property
    def described_segments(self) -> tuple[BusinessSegment, ...]:
        """The segments the filing was shown to say something about."""

        return tuple(
            segment for segment in self.segments if segment.description is not None
        )

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()
