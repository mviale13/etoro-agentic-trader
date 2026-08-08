"""An authoritative document a company published about itself."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.domain.prose_evidence import Region
from app.domain.tabular_evidence import SourceTable


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


class SourceAuthority(StrEnum):
    """What kind of source this document is, not how much to trust it.

    Descriptive rather than ranked. There is deliberately no number and
    no ordering: a numeric confidence invites arithmetic on it, and an
    ordering invites a caller to compare two sources without knowing
    what actually differs between them. What differs is written down —
    in `docs/architecture.md`, once per authority — and a reader is
    owed the fact, not a score derived from it.

    Authority belongs to the *source*, not to the provider that fetched
    it. One provider can legitimately return both: an Investor Relations
    page may publish the very ESEF package its issuer filed, and may also
    publish a PDF nobody received on a dated record.
    """

    #: A body received it, on a dated record, under a filing obligation.
    REGULATOR_FILED = "regulator_filed"

    #: The company published it itself. Genuine and unreceived: there is
    #: no third party who can confirm what was published or when.
    ISSUER_PUBLISHED = "issuer_published"


class IdentityCheck(StrEnum):
    """An identity check that actually succeeded for this document.

    Not a trust level — a record of what was established, so a reader
    can see which guarantees a particular document carries rather than
    inferring them from where it came from. The checks are independent
    and no source performs all of them: EDGAR's index names a filing for
    a ticker and the filing declares no LEI; an ESEF package declares its
    LEI and is also indexed; a document published by its issuer is
    neither indexed nor accessioned, and answers for itself.
    """

    #: The symbol was matched to a legal entity through the reviewed
    #: issuer list and GLEIF's ISIN-to-LEI mapping.
    SECURITY_REGISTRY = "security_registry"

    #: A register named this document as this filer's, on its own index.
    REGISTER_INDEXED = "register_indexed"

    #: The bytes came from a location reviewed as this issuer's own.
    APPROVED_SOURCE = "approved_source"

    #: The document declared the expected issuer's LEI in its own
    #: contexts. The strongest of these, because it is the document
    #: answering rather than something said about it.
    DOCUMENT_LEI = "document_lei"

    #: The document's identity is the hash of the bytes retrieved, and
    #: they matched the hash the location was reviewed against.
    CONTENT_HASHED = "content_hashed"


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

    #: Provenance: who supplied it, as a reader would name it — "SEC
    #: EDGAR", "ESEF", "Official Investor Relations".
    provider: str

    #: What kind of source this is. Stated by every provider, never
    #: defaulted, because a provider that did not have to say would
    #: eventually not know.
    authority: SourceAuthority

    #: Which identity checks succeeded on the way to this document. The
    #: audit trail: authority says what the source is, provenance says
    #: where it came from, and this says what was actually proven.
    verification: tuple[IdentityCheck, ...]

    def stated(self) -> str:
        """The document as an investor would cite it."""

        covering = (
            f", {self.reporting_period.stated()}"
            if self.reporting_period is not None
            else ""
        )

        return (
            f"{self.identifier or self.source_type.value} published "
            f"{self.published_on.isoformat()}{covering}, via {self.provider} "
            f"({self.attested()})"
        )

    def attested(self) -> str:
        """What kind of source this is, in words a reader can act on.

        Carried in every citation, because "filed with a regulator" and
        "published by the company" are different claims and a reader who
        had to infer which one they were looking at would infer wrongly
        about half the time.
        """

        if self.authority is SourceAuthority.REGULATOR_FILED:
            return "filed with a regulator"

        return "published by the issuer"


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

    #: The regions that section's own headings introduce, in the
    #: coordinates of `business_description`.
    #:
    #: Structure is what makes a description owned by the part of the
    #: document it was printed in, rather than by whichever segment the
    #: prose named most recently. Empty where the publisher offers none
    #: this platform can read — a report assembled from tagged blocks
    #: rather than laid out as a section has no headings to find — and
    #: ownership then falls back to position, which is weaker and still
    #: honest.
    business_regions: tuple[Region, ...] = ()

    #: How each part of it performed, which is where a publisher states
    #: what each segment earned. Empty where the document has no such
    #: section, which leaves the segments described and their sizes
    #: unstated rather than apportioned.
    performance_discussion: str = ""

    #: The tables printed inside that discussion, with their rows and
    #: columns kept rather than flattened into the prose beside them.
    #:
    #: Two sections of prose were enough while the platform only read
    #: what a business *is*. A quantity is different in kind: it means
    #: nothing without the row it sits on and the column it sits under,
    #: and prose that has been stripped of its table structure can no
    #: longer say which those were. Empty where the publisher printed no
    #: tables this platform could read, which leaves segment sizes
    #: unstated rather than read off a flattened row.
    performance_tables: tuple[SourceTable, ...] = ()

    #: The audited income statement, located where the publisher
    #: typeset its title. The text is kept beside the tables so an
    #: absence can say which fact it is: a statement this platform
    #: never located, and a located statement that printed no table it
    #: could read, are different findings and only one is about the
    #: document.
    income_statement_text: str = ""

    #: The tables printed under that title — the statement itself,
    #: structure kept. Empty leaves the figures unstated rather than
    #: read out of whatever section mentioned them.
    income_statement_tables: tuple[SourceTable, ...] = ()

    #: The other two primary statements, carried on the identical terms.
    #: Which of the three a reading is shown is decided by its
    #: `StatementKind`, in `app.domain.financial_statements`, which is
    #: where the mapping lives so that this module stays unaware of the
    #: vocabulary reading it — the dependency runs one way.
    balance_sheet_text: str = ""
    balance_sheet_tables: tuple[SourceTable, ...] = ()

    cash_flow_text: str = ""
    cash_flow_tables: tuple[SourceTable, ...] = ()


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
