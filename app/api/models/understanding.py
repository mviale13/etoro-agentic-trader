"""What this platform understands about a company, over the wire.

Composed from `BusinessUnderstanding` and `FinancialUnderstanding` and
from nothing else. No figure is derived at the API layer, and no field
here exists that the domain does not already hold: a share is the share
the consensus settled, a margin is the margin the engine computed from
two checked cells, and a width is the width beneath it.

Every claim carries how firmly it is known, beside the claim rather than
below the fold. That is the whole point of showing this: an investor
reading that a business earns three ways is owed the fact that one of
those rests on three readings out of five.
"""

from pydantic import BaseModel


class AgreementResponse(BaseModel):
    """How firmly one claim is held, as counted."""

    agreeing: int
    readings: int

    #: True where every reading that addressed the claim agreed.
    settled: bool


class SegmentResponse(BaseModel):
    """One part of the business, as consensus establishes it."""

    name: str

    #: The settled share of revenue, or None with the reason beside it.
    share: float | None
    unmeasured_because: str | None

    #: The settled ways this part earns, in the filer's terms.
    earns: list[str]
    earns_because: str | None

    #: The filer's stated economic dependence of this business on
    #: another, already worded for the investor with the filer's own
    #: degree intact — plus the verbatim span and the agreement width.
    #: All three null in the ordinary case, which is an evidence state
    #: and never a finding of independence.
    depends: str | None = None
    depends_quoted: str | None = None
    depends_support: str | None = None


class MechanismResponse(BaseModel):
    """One way the business earns, and how much of it earns that way."""

    model: str

    #: The segments whose settled earning includes it.
    through: list[str]

    #: The share of *measured* revenue those segments account for.
    #: Deliberately coverage, never a revenue mix: no filing splits a
    #: segment's revenue between its ways of earning.
    coverage: float | None

    support: AgreementResponse


class UnestablishedResponse(BaseModel):
    """One thing the rules needed and did not have, with its own reason."""

    segment: str
    dimension: str
    because: str


class BusinessUnderstandingResponse(BaseModel):
    """How a business creates value, from its own filing's consensus."""

    source: str
    read: str

    #: The width beneath the whole.
    quorate: bool
    observation_count: int
    quorum: int

    #: The engine in one sentence, worded from the archetype.
    engine: str

    #: What the rules concluded this business is, and why. None where
    #: they could not decide — then `undecided_because` says so.
    archetype: str | None
    undecided_because: str | None

    #: The narrowest agreement among the claims the rules consumed. A
    #: conclusion is exactly as firm as the weakest claim beneath it.
    narrowest: AgreementResponse | None

    segments: list[SegmentResponse]
    segments_because: str | None

    mechanisms: list[MechanismResponse]

    not_established: list[UnestablishedResponse]


class MeasureResponse(BaseModel):
    """One measure, computed from checked figures or absent with its reason."""

    measure: str
    label: str

    #: The number, or None. How to read it is `unit`: a fraction is a
    #: percentage, a multiple is "times", a currency is a quantity at
    #: the scale its own caption states.
    value: float | None
    unit: str

    #: The arithmetic as an investor would check it against the filing.
    stated: str

    #: The narrowest agreement among the figures it consumed.
    support: AgreementResponse | None

    absent_because: str | None


class FinancialUnderstandingResponse(BaseModel):
    """What the filer's own statements measure, and how firmly."""

    source: str
    read: str

    quorate: bool
    observation_count: int
    quorum: int

    #: Which statements this rests on.
    statements: list[str]

    #: Which financial language the income statement establishes, from
    #: the lines the filer printed. Reported and consumed by nothing:
    #: the financial model is still derived from the business playbook.
    #: See `docs/architecture/FINANCIAL_DOMAIN_BOUNDARY.md`.
    language: str | None
    language_because: str | None

    measures: list[MeasureResponse]


class UnderstandingResponse(BaseModel):
    """Both halves, each present or worded absent.

    Two independent halves rather than one merged view: they rest on
    different sections, reach quorum separately and fail separately, and
    a company whose segments are established and whose statements are
    not is a real state this must not flatten.
    """

    business: BusinessUnderstandingResponse | None
    business_absent_because: str | None

    financial: FinancialUnderstandingResponse | None
    financial_absent_because: str | None
