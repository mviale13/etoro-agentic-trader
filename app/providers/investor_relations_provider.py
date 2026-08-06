"""The company's own published report, where no register holds one.

The first provider whose source no regulator received, and therefore the
first that has to establish for itself what EDGAR and ESEF could delegate.
Every provider answers the same three questions before extraction begins:

1. Can I retrieve the document?
2. Can I prove whose document it is?
3. Can I prove this issuer belongs to the requested security?

EDGAR answers all three from its own index. ESEF answers the first two
from the European index and the document's own LEI, and the third from
GLEIF. This provider has no index at all, so it answers the first from a
reviewed location and a hash, the second from the document's own LEI, and
the third from the same GLEIF boundary the ESEF provider uses.

The consequence is deliberately conservative. A document that cannot
identify its own issuer cannot become company knowledge, whatever else is
true about it — so a company publishing only a PDF is honestly
unavailable rather than read on the strength of the domain it sits on.
Coverage may expand later; trust does not contract to speed it up.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import httpx

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
    ReportingPeriod,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.providers.esef_filings import (
    EsefFilingUnavailable,
    EsefReport,
    read_package,
)
from app.providers.investor_relations_sources import (
    PUBLISHED_REPORTS,
    PublishedReport,
)
from app.providers.issuer_identity import (
    IssuerIdentity,
    IssuerIdentityRegistry,
    IssuerRegistryError,
    IssuerUnknown,
)

NAME = "Official Investor Relations"


class InvestorRelationsProvider:
    """
    A company's own account of itself, from the company.

    Last in the order on purpose. Where a regulator received the document
    it is the better source, because a filing obligation and a dated
    record are guarantees this provider cannot manufacture. What it can
    do is reach the companies no register this platform reads holds at
    all — which today is every German issuer.

    Nothing about the reading is weaker. Volkswagen publishes the ESEF
    package it filed, so the document is the same regulated artefact,
    read by the same tag-driven reader, and it identifies its own issuer
    exactly as a package from a register would. What is weaker is stated
    on the source rather than argued in prose: the authority is
    `ISSUER_PUBLISHED`, and the checks that actually succeeded travel
    with it.
    """

    name = NAME

    def __init__(
        self,
        reports: dict[str, PublishedReport] | None = None,
        issuers: IssuerIdentityRegistry | None = None,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._reports = dict(PUBLISHED_REPORTS if reports is None else reports)
        self._issuers = issuers or IssuerIdentityRegistry()
        self._client = client
        self._timeout = timeout

    def resolve(self, symbol: str) -> PrimarySource:
        """
        Which document this company published, without fetching it.

        Cheaper than either register, because there is no index to ask:
        everything about the *document* was established when the entry
        was reviewed. What it still costs is one small identity lookup,
        memoised for the run — and never the six megabytes of the
        document itself, which is the cost the seam exists to avoid.
        """

        identity = self._identity(symbol)

        report = self._reports.get(symbol.upper().strip())

        if report is None:
            raise PrimarySourceUnavailable(
                f"{identity.legal_name} publishes an annual report, and no "
                f"location for it has been reviewed for {symbol.upper().strip()}. "
                "A document location is reviewed rather than discovered, so "
                "one that has not been reviewed is absent rather than searched "
                "for."
            )

        return PrimarySource(
            symbol=symbol.upper().strip(),
            company=identity.legal_name,
            source_type=SourceType.ANNUAL_REPORT,
            identifier=report.identifier,
            # The bytes themselves. Nobody assigned this document a
            # number, so its identity is what it is made of.
            key=report.content_hash,
            published_on=report.published_on,
            reporting_period=ReportingPeriod(ends_on=report.period_ends_on),
            document_format="xhtml",
            # Stated by the document, and filled in by `fetch`.
            language="",
            location=report.location,
            provider=NAME,
            authority=SourceAuthority.ISSUER_PUBLISHED,
            verification=(IdentityCheck.SECURITY_REGISTRY,),
        )

    def fetch(self, source: PrimarySource) -> SourceDocument:
        identity = self._identity(source.symbol)

        report = self._reports.get(source.symbol.upper().strip())

        if report is None:
            raise PrimarySourceUnavailable(
                f"No reviewed location holds {source.symbol}, so nothing was "
                "fetched for it."
            )

        archive = self._retrieve(report, source)

        retrieved = hashlib.sha256(archive).hexdigest()

        if retrieved != report.content_hash:
            # Not an error, and not a silent update either. The document
            # at a reviewed location changed, so what is there now has
            # not been reviewed — most likely because the company
            # published its next annual report, which is exactly the
            # moment a person should look rather than a machine.
            raise PrimarySourceUnavailable(
                f"The document at {source.location} is no longer the one that "
                f"was reviewed: it now hashes to {retrieved[:16]}… rather than "
                f"{report.content_hash[:16]}…. Nothing was read from it until "
                "the entry is reviewed again."
            )

        document = self._read(archive, source)

        self._must_be_the_issuer(document, identity, source)
        self._must_be_the_period(document, report, source)

        if not document.business_text:
            raise PrimarySourceUnavailable(
                f"{source.stated()} tags no description of the company's "
                "operations or its segments, so there was nothing in it to "
                "read."
            )

        return SourceDocument(
            source=replace(
                source,
                company=document.company or source.company,
                language=document.language or source.language,
                verification=(
                    IdentityCheck.SECURITY_REGISTRY,
                    IdentityCheck.APPROVED_SOURCE,
                    IdentityCheck.CONTENT_HASHED,
                    IdentityCheck.DOCUMENT_LEI,
                ),
            ),
            business_description=document.business_text,
            performance_discussion=document.discussion_text,
        )

    # ── the three questions ─────────────────────────────────────────

    def _retrieve(self, report: PublishedReport, source: PrimarySource) -> bytes:
        """Can I retrieve the document — from somewhere this entry approves."""

        try:
            response = self._got(source.location)
        except Exception as error:
            raise PrimarySourceProviderError(
                f"{source.stated()} could not be retrieved."
            ) from error

        # Where the bytes finally came from, not where the request was
        # aimed. A redirect off an approved host is how a mirror, a
        # link-shortener or a compromised page would serve a document
        # that looks right and is not.
        landed = str(response.url)

        if not report.serves(landed):
            raise PrimarySourceProviderError(
                f"{source.stated()} was served from {landed}, which is not a "
                f"host reviewed for {source.symbol}. Nothing was read from it."
            )

        return response.content

    @staticmethod
    def _must_be_the_issuer(
        document: EsefReport,
        identity: IssuerIdentity,
        source: PrimarySource,
    ) -> None:
        """Can I prove whose document it is — from the document itself."""

        if not document.lei:
            # The hard line. Everything else about this document may be
            # in order, and without this it stays a document about some
            # company rather than about this one.
            raise PrimarySourceUnavailable(
                f"{source.stated()} does not identify its own issuer, so it "
                "cannot be shown to belong to "
                f"{identity.legal_name}. A document that cannot say whose it "
                "is does not become company knowledge."
            )

        if document.lei.upper() != identity.lei.upper():
            raise PrimarySourceProviderError(
                f"{source.stated()} identifies itself as {document.lei}, and "
                f"it was fetched for {identity.lei} ({identity.legal_name}). "
                "Nothing was read from it."
            )

    @staticmethod
    def _must_be_the_period(
        document: EsefReport,
        report: PublishedReport,
        source: PrimarySource,
    ) -> None:
        """The document's own account of which year this is."""

        if document.period_ends_on is None:
            return

        if document.period_ends_on != report.period_ends_on:
            raise PrimarySourceUnavailable(
                f"{source.stated()} accounts for a period ending "
                f"{document.period_ends_on.isoformat()}, and the reviewed "
                f"entry records {report.period_ends_on.isoformat()}. The "
                "document was not read under a period it does not state."
            )

    def _read(self, archive: bytes, source: PrimarySource) -> EsefReport:
        try:
            return read_package(archive)
        except EsefFilingUnavailable as unreadable:
            raise PrimarySourceUnavailable(str(unreadable)) from unreadable
        except Exception as error:
            raise PrimarySourceProviderError(
                f"{source.stated()} could not be read."
            ) from error

    def _identity(self, symbol: str) -> IssuerIdentity:
        """Can I prove this issuer belongs to the requested security."""

        try:
            return self._issuers.of(symbol)
        except IssuerRegistryError as unreachable:
            raise PrimarySourceProviderError(str(unreachable)) from unreachable
        except IssuerUnknown as unknown:
            raise PrimarySourceUnavailable(str(unknown)) from unknown

    # ── the wire ────────────────────────────────────────────────────

    def _got(self, url: str) -> httpx.Response:
        if self._client is not None:
            response = self._client.get(url)
        else:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, follow_redirects=True)

        response.raise_for_status()

        return response
