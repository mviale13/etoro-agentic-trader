"""One reading of a business's own annual report: an observation.

Not a deterministic artifact, and the name says so. The reader
calibration measured fifty readings of five immutable documents: every
claim a model contributes varies between readings of unchanged prose,
and the object this module defines is therefore *one draw* — admissible,
grounded, and one of several a quorum will hold. What the platform
treats as knowledge is the consensus derived over a set of these, in
`app.domain.knowledge_consensus`, and nothing downstream of the store
should consume a single observation directly.
"""

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
class DescriptionRepair:
    """
    Proof that a span was supplied by a second, bounded request.

    Carried so that a repaired reading is never presented as a first
    one. Two spans that both pass applicability are equally good
    evidence for the claim beside them — but how a platform arrived at
    a citation is part of what a reader is entitled to know, and a
    surface that showed the repaired span silently would be concealing
    that the first attempt cited something else.

    Its existence is also the audit trail for a boundary this platform
    is deliberately close to: a repair asks again, and asking again is
    one short step from asking until something passes. An unrecorded
    repair would make that step invisible.
    """

    #: Why the platform asked a second time, in the knowledge layer's
    #: own words: applicability's refusal of the first citation, or —
    #: for a segment the first reading described with no words at all —
    #: that very absence. Either way the sentence is what stood before
    #: the second request, and it is kept so the record shows what the
    #: request was answering.
    first_refused_because: str

    #: What performed the repair — the same wording the reading carries,
    #: because a repair is a reading and is exactly as trustworthy as
    #: whatever did it.
    reader: str


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

    #: Where this span came from, if not the first reading: a repair of
    #: a refused citation, or the asked-by-name follow-up a wordless
    #: arrival earns. None is the ordinary case and means the first
    #: citation was applicable.
    #:
    #: The ways of earning beside it are *never* supplied by the second
    #: request. It may return a span and nothing else, so the claim
    #: evidenced is the one the first reading made — for a segment that
    #: arrived with neither words nor models, that claim is "described,
    #: naming no way of earning", the narrower honest statement. This is
    #: what keeps "evidence this claim" from becoming "find an
    #: acceptable claim", and it is structural rather than instructed:
    #: there is nowhere in the one-field contract to put a revenue
    #: model.
    repair: DescriptionRepair | None = None

    @property
    def quoted(self) -> str:
        """The filing's own words."""

        return self.evidence.quoted

    @property
    def was_repaired(self) -> bool:
        """Whether this span came from a second, bounded request."""

        return self.repair is not None


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

    #: Why there is no size, in the same words and for the same reason.
    #:
    #: Three claims evidenced apart is three absences worded apart, and
    #: only two of the three were. A missing size read identically
    #: whether the filing printed no segment table, stated its figures
    #: in a document this one only points at, or reported a total this
    #: platform could not locate — and every one of those is a different
    #: fact, only some of which are about the company. That silence cost
    #: real coverage: Caterpillar's sizes were absent because this
    #: platform had located the wrong section of its 10-K, and the
    #: surface reported it as the filing not proving them.
    unmeasured_because: str | None = None

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
class CompanyKnowledgeObservation:
    """
    One reading of the document this company is legally answerable for.

    Facts, never conclusions — and *observed* facts, never the settled
    account. This object is what one pass of the reader found: it
    survived identity, grounding and applicability, which makes it
    admissible, and admissible is all one reading can be. Whether its
    answers are representative is a property of several observations
    together, and is decided by the consensus derived over them — never
    by promoting one observation because its answers please.

    Immutable once taken. An observation is a record of what a reading
    found at a moment; correcting it would destroy the very disagreement
    the consensus exists to measure.

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
