"""Structural facts about a business, read from its own annual report."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.primary_source import PrimarySource
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
class BusinessSegment:
    """One part of the business, as the company itself reports it.

    `quoted` is not decoration and not a citation the reader is asked to
    trust. It is the sentence in the filing this segment was read from,
    and the extraction is rejected outright unless those words appear in
    the document — so a segment that was never described cannot reach
    this object however confidently it was asserted.

    Two facts of two different kinds, evidenced two different ways. What
    a segment *is* is prose, and a span proves the filing described it.
    How large it is, is a quantity, and no span can prove that: a
    quantity means nothing without the row it sits on and the column it
    sits under. So a size arrives as the two printed figures it was
    computed from, and there is deliberately no way to state one without
    them.
    """

    name: str

    #: What this segment earned, as a fraction of a total the same table
    #: printed in the same column. None where the company described the
    #: segment without a figure this platform could locate in a table —
    #: which is common, and is not the same as the segment being small.
    revenue: MeasuredShare | None

    revenue_models: tuple[RevenueModel, ...]

    quoted: str

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

    def stated_source(self) -> str:
        """The document as an investor would cite it."""

        return self.source.stated()
