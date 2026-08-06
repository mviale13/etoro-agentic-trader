"""What kind of business this is, decided from its own filing.

The first thing this platform *concludes* rather than reads. Everything
under it — segments, measured sizes, evidenced ways of earning — is a
fact taken from a document. This is a rule's answer to a question no
document is asked: what do those facts add up to?

So it is kept apart from `CompanyKnowledge` in the way the Brain is kept
apart from the Artificial CIO. The knowledge layer stores what a filing
says. This states what follows from it, names every rule that fired, and
carries the facts each rule read — because a classification a reader
cannot audit is a label, and this platform's whole argument is that a
label is what it refuses to be.

**Not an industry.** A sector says what a company sells and is assigned
by somebody else. This is computed from what the company's own segments
were shown to do, weighted by sizes measured out of its own tables. Two
companies filed under the same industry arrive here differently when
they earn differently, which is the point.

**Four regimes, and they are different facts.** Size and description
fail independently in the knowledge layer, so what can be concluded here
depends on which of them survived. Measured across the eight filings
this platform had read when these rules were written:

- **Ranked** — sizes and ways of earning both established, and one way
  of earning is more widespread than the rest. NVIDIA: every segment
  manufactures, and the segments that also license are 90% of revenue.
- **Diversified** — the same evidence, and no way of earning leads.
  Disney: licensing, transaction and services each run through 100% of
  measured revenue, and no arithmetic separates them.
- **Unranked** — the ways of earning are known and nothing was measured,
  so there is no basis to order them. Caterpillar, whose four segments
  are described and none of whose sizes were proven.
- **Undecided** — too little of the business was shown to earn any
  particular way. Meta, whose revenue is 100% measured and 0% explained
  because both segment descriptions were refused.

Diversified and unranked are deliberately not the same answer. One says
the business genuinely has no leading way of earning; the other says
this platform cannot tell. Collapsing them would report an absence of
measurement as a finding about the company.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.company_knowledge import RevenueModel
from app.domain.provenance import Provenance


class Archetype(StrEnum):
    """
    What a company is, as its own filing establishes it.

    A separate vocabulary from `RevenueModel`, and not a duplicate of it.
    A revenue model is a fact about a *segment* — this segment earns by
    subscription. An archetype is a conclusion about a *company* — this
    business is a subscription business. Different subjects, established
    by different means: one is read from a filing, the other is decided
    by a rule from several of them weighted by size.

    Today every member but `DIVERSIFIED` maps one-to-one from the way of
    earning that leads the coverage, because that is all the current evidence
    supports. The vocabulary is separate so that it can stop being
    one-to-one — "a manufacturer with a captive lender" is a real
    archetype and Caterpillar is one, but nothing this platform reads
    today establishes it.
    """

    SUBSCRIPTION_BUSINESS = "subscription_business"
    ADVERTISING_BUSINESS = "advertising_business"
    TRANSACTION_BUSINESS = "transaction_business"
    LICENSING_BUSINESS = "licensing_business"
    MANUFACTURER = "manufacturer"
    RETAILER = "retailer"
    SERVICE_BUSINESS = "service_business"
    COMMODITY_PRODUCER = "commodity_producer"
    LENDER = "lender"
    INSURER = "insurer"
    ASSET_MANAGER = "asset_manager"

    #: Several ways of earning run through the business and none leads.
    #: A finding, not an absence: it is reached only where the sizes were
    #: measured and the arithmetic genuinely does not separate them.
    DIVERSIFIED = "diversified"

    @property
    def stated(self) -> str:
        """The archetype as an investor reads it."""

        return _STATED[self]


#: How each archetype is named to a reader.
_STATED: dict[Archetype, str] = {
    Archetype.SUBSCRIPTION_BUSINESS: "Subscription business",
    Archetype.ADVERTISING_BUSINESS: "Advertising business",
    Archetype.TRANSACTION_BUSINESS: "Transaction business",
    Archetype.LICENSING_BUSINESS: "Licensing business",
    Archetype.MANUFACTURER: "Manufacturer",
    Archetype.RETAILER: "Retailer",
    Archetype.SERVICE_BUSINESS: "Service business",
    Archetype.COMMODITY_PRODUCER: "Commodity producer",
    Archetype.LENDER: "Lender",
    Archetype.INSURER: "Insurer",
    Archetype.ASSET_MANAGER: "Asset manager",
    Archetype.DIVERSIFIED: "Diversified",
}


#: The archetype each way of earning names, where it leads the business.
#:
#: Exhaustive over `RevenueModel` on purpose. A way of earning with no
#: archetype beside it would be silently unclassifiable — the company
#: would come back undecided and no rule would say why — so a new
#: revenue model must be given its archetype here, and the test suite
#: fails until it is.
ARCHETYPE_OF: dict[RevenueModel, Archetype] = {
    RevenueModel.SUBSCRIPTION: Archetype.SUBSCRIPTION_BUSINESS,
    RevenueModel.ADVERTISING: Archetype.ADVERTISING_BUSINESS,
    RevenueModel.TRANSACTION: Archetype.TRANSACTION_BUSINESS,
    RevenueModel.LICENSING: Archetype.LICENSING_BUSINESS,
    RevenueModel.MANUFACTURING: Archetype.MANUFACTURER,
    RevenueModel.RETAIL: Archetype.RETAILER,
    RevenueModel.SERVICES: Archetype.SERVICE_BUSINESS,
    RevenueModel.COMMODITY: Archetype.COMMODITY_PRODUCER,
    RevenueModel.FINANCIAL_SPREAD: Archetype.LENDER,
    RevenueModel.PREMIUMS: Archetype.INSURER,
    RevenueModel.ASSET_MANAGEMENT_FEES: Archetype.ASSET_MANAGER,
}


class Dimension(StrEnum):
    """A thing about a segment that has to be established separately."""

    #: What the segment earned, as a share of a printed total.
    SIZE = "size"

    #: How the segment earns, read from a description shown to be of it.
    EARNING = "earning"


@dataclass(frozen=True, slots=True)
class Unestablished:
    """One thing the rules needed about one segment and did not have.

    Carried rather than counted. "Three of five segments are
    unexplained" tells a reader that something is missing; naming the
    segments and quoting the knowledge layer's own reason tells them
    whether the gap is in the filing or in the reading of it, and only
    one of those is worth acting on.
    """

    segment: str
    dimension: Dimension

    #: Why, in the words the knowledge layer used. Passed through
    #: unaltered: an absence carries its reason across every layer of
    #: this platform, and a rule restating it in its own words would be
    #: a second, unevidenced account of the same event.
    because: str


@dataclass(frozen=True, slots=True)
class ModelCoverage:
    """How much of the business earns one particular way.

    Deliberately *coverage*, never revenue. A filing reports what each
    segment earned and which ways of earning that segment uses; it does
    not split a segment's revenue between them. So this says "segments
    worth 90% of measured revenue license as well as manufacture" — it
    does not say 90% of revenue is licensing revenue, which nothing this
    platform has read establishes and which the number would be taken
    for if it were called a share.

    A consequence: coverages do not sum to 1 and are not meant to. One
    segment earning five ways contributes its whole size to all five.
    """

    model: RevenueModel

    #: The sizes of the segments that earn this way, added up — as a
    #: share of the revenue total those segments were measured against.
    #: None where nothing was measured, and the ways of earning are
    #: therefore known but unrankable.
    #:
    #: It can exceed 1, and that is not an error. Segment figures include
    #: revenue the segments billed each other, which consolidation
    #: removes from the total they are divided by, so the parts exceed
    #: the whole by however much of that trade there was. Disney's three
    #: segments sum to 102%.
    covers: float | None

    #: The segments that evidenced it, named so the coverage can be
    #: checked back against the filing.
    segments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Ruling:
    """One rule that fired, and the facts it read to fire.

    The unit of auditability here. A reader who disagrees with an
    archetype should be able to find the rule that produced it, see the
    grounded facts it was given, and check those against the filing —
    without reading this platform's source.
    """

    #: What the rule is called, in the engine and in this record.
    rule: str

    #: The grounded facts it read, worded.
    read: str

    #: What it concluded from them.
    concluded: str


@dataclass(frozen=True, slots=True)
class CompanyArchetype:
    """
    What kind of business a company is, and everything that decided it.

    An undecided archetype is a first-class outcome, not a failure to
    render. It carries the reason, the coverage that fell short, and the
    segments whose missing dimension caused it — because "this platform
    has not established what Meta earns from" is a fact about the
    reading, and hiding it behind an industry label is the substitution
    this whole layer exists to stop making.
    """

    symbol: str

    #: The way of earning that leads the business, as an archetype. None
    #: where the rules could not decide — always with a reason beside it.
    primary: Archetype | None

    #: The next-widest way of earning, where one stands apart from the
    #: rest. Optional in the ordinary case rather than exceptional: most
    #: businesses earn one way.
    secondary: Archetype | None

    #: What this business might be, where the ways of earning are known
    #: and nothing was measured to rank them. Never populated alongside
    #: a primary: a rule either ordered them or it did not.
    candidates: tuple[Archetype, ...]

    #: Every way of earning the filing evidenced, with its coverage.
    #:
    #: Named coverage rather than mix, deliberately. "Revenue mix"
    #: means a split of revenue between things, which is precisely what
    #: this is not and what no filing establishes. A surface that
    #: relabels it would be asserting a measurement nobody printed.
    coverage: tuple[ModelCoverage, ...]

    #: The share of revenue the segments account for with a measured
    #: size. Passed through from the knowledge layer.
    measured: float

    #: The share of measured revenue whose segments were also shown to
    #: earn some particular way. The number that decides whether an
    #: archetype can be reached at all, and the one that separates "this
    #: company has no leading way of earning" from "this platform did
    #: not establish how it earns".
    explained: float

    #: What the rules needed and did not have, per segment.
    missing: tuple[Unestablished, ...]

    #: Every rule that fired, in the order it fired.
    basis: tuple[Ruling, ...]

    #: Why no archetype was decided, where none was.
    undecided_because: str | None

    #: The document all of this was ultimately read from, as an investor
    #: would cite it.
    source: str

    #: When that reading happened, and by what.
    reading: Provenance

    @property
    def is_decided(self) -> bool:
        """Whether the rules reached an archetype at all."""

        return self.primary is not None

    @property
    def is_ranked(self) -> bool:
        """Whether the ways of earning could be ordered by size."""

        return self.primary is not None and self.primary is not Archetype.DIVERSIFIED

    @property
    def stated(self) -> str:
        """The archetype in one line, absence included."""

        if self.primary is None:
            return "Not classified"

        if self.secondary is None:
            return self.primary.stated

        return f"{self.primary.stated}, then {self.secondary.stated.lower()}"
