"""An authoritative document a company published about itself."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class SourceType(StrEnum):
    """What kind of document this is, apart from who published it.

    A 10-K, a 20-F and a European annual financial report are the same
    kind of thing — the company's own yearly account of itself — filed
    with different regulators under different rules. What the extraction
    needs to know is the kind; which regulator received it is the
    provider's business.
    """

    ANNUAL_REPORT = "annual_report"
    INTERIM_REPORT = "interim_report"


@dataclass(frozen=True, slots=True)
class ReportingPeriod:
    """The business period a document accounts for.

    Kept apart from the date the document was published, because they are
    different facts and comparing the wrong one compares the wrong thing.
    A company that files late and one that files early are not describing
    different periods; two reports published a year apart may cover
    periods eleven months apart, or thirteen.

    `starts_on` is absent where the publisher states only the period end,
    which is what a regulator's filing index gives. A year subtracted
    from the end date would be an inference dressed as a fact.
    """

    ends_on: date

    starts_on: date | None = None

    def __post_init__(self) -> None:
        if self.starts_on is not None and self.starts_on > self.ends_on:
            raise ValueError("A reporting period cannot end before it starts")

    @property
    def fiscal_year(self) -> int:
        """
        The calendar year this period ended in.

        Not the filer's own label for its fiscal year, which it may name
        differently and which this platform does not read. The year the
        period ended in is a fact about the period; a fiscal-year label
        is a convention, and the two are not always the same number.
        """

        return self.ends_on.year

    def stated(self) -> str:
        """The period as an investor would read it."""

        if self.starts_on is None:
            return f"period ended {self.ends_on.isoformat()}"

        return f"{self.starts_on.isoformat()} to {self.ends_on.isoformat()}"


@dataclass(frozen=True, slots=True)
class PrimarySource:
    """
    One document, identified precisely enough to fetch it and to keep it.

    Canonical on purpose. The extraction layer must not care whether a
    report came from EDGAR, from an ESEF filing, from a company's own
    investor-relations page or from a document handed to it — the
    grounding rules are the same for all of them, and a layer that knew
    the difference would grow a branch per provider.

    `key` is the contract that makes knowledge permanent: it must
    identify this exact document and never be reused for a different one.
    A regulator's accession number is one; the hash of a published PDF is
    another. What matters is that the same key always means the same
    bytes, because knowledge read under it is never read again.
    """

    #: The security this document belongs to, as this platform names it.
    symbol: str

    #: The publisher's own name for itself, from the document.
    company: str

    source_type: SourceType

    #: The publisher's identifier for this document, where it has one.
    identifier: str

    #: The immutable identity of this exact document. Knowledge read
    #: under this key is reused for as long as the key stands.
    key: str

    published_on: date

    #: The business period the document accounts for, where the publisher
    #: states it. None where it does not — which is never a reason to
    #: infer one from the publication date, since a document published in
    #: November may account for a year ended in September.
    reporting_period: ReportingPeriod | None

    #: "html", "xhtml", "pdf". What the document arrived as, so a reader
    #: of the stored knowledge can tell how it was parsed.
    document_format: str

    #: The language the document was published in, as an ISO code. An
    #: extraction from a translation is not an extraction from the
    #: filing, so the original's language is recorded.
    language: str

    #: Where it can be opened.
    location: str

    #: Who supplied it, as a reader would name it: "SEC EDGAR".
    provider: str

    def stated(self) -> str:
        """The document as an investor would cite it."""

        covering = (
            f", {self.reporting_period.stated()}"
            if self.reporting_period is not None
            else ""
        )

        return (
            f"{self.identifier or self.source_type.value} published "
            f"{self.published_on.isoformat()}{covering}, via {self.provider}"
        )


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A primary source, and the parts of it this platform reads.

    Two sections, named for what they contain rather than for where a
    particular regulator files them. A 10-K calls them Item 1 and Item 7;
    a European annual report calls them something else and puts them in a
    different order. The extraction asks the same two questions of both.
    """

    source: PrimarySource

    #: What the business is: its parts, what each sells, how it earns.
    business_description: str

    #: How each part of it performed, which is where a publisher states
    #: what each segment earned. Empty where the document has no such
    #: section, which leaves the segments described and their sizes
    #: unstated rather than apportioned.
    performance_discussion: str = ""


class PrimarySourceUnavailable(Exception):
    """This provider holds no document for the security, and says why.

    A gap in coverage. It is a fact about where this platform reaches —
    a company registered with another regulator, a security that is not a
    company at all — and it calls for asking a different provider, not
    for trying again.

    Never a reason to describe the business from a lesser source.
    """


class PrimarySourceProviderError(PrimarySourceUnavailable):
    """The provider could not be reached or could not answer.

    Deliberately a different situation from a gap in coverage, and a
    subclass so a caller that does not care still catches both. "BNP
    Paribas is not registered with the SEC" is settled and will be true
    tomorrow; "the register could not be reached" may not be, and only
    one of the two is worth retrying.
    """
