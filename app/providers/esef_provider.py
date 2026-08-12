"""ESEF as a primary-source provider: Europe, behind the same seam."""

from __future__ import annotations

from dataclasses import replace

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
    EsefFilings,
    EsefFilingUnavailable,
    EsefRegisterError,
)
from app.providers.issuer_identity import (
    IssuerIdentity,
    IssuerIdentityRegistry,
    IssuerRegistryError,
    IssuerUnknown,
)

NAME = "ESEF"


class EsefProvider:
    """
    The company's own annual report, from the European register.

    What EDGAR is to an American issuer, ESEF is to a European one: the
    filer wrote it, a national regulator received and validated it, and
    the filed package is not revised in place. The rules the extraction
    holds it to do not change — this closes a gap in coverage, not a gap
    in standards.

    Two things are different from EDGAR and both are visible in this
    class. Europe indexes filers by LEI rather than by ticker, so the
    identity has to be established before anything can be asked for.
    And an ESEF filing marks up which passage is which, so the document
    is read by asking the filer's own tagging rather than by hunting for
    section headings in a language nobody guaranteed.
    """

    name = NAME

    def __init__(
        self,
        filings: EsefFilings | None = None,
        issuers: IssuerIdentityRegistry | None = None,
    ) -> None:
        self._filings = filings or EsefFilings()
        self._issuers = issuers or IssuerIdentityRegistry()

    def resolve(self, symbol: str) -> PrimarySource:
        identity = self._identity(symbol)

        try:
            reference = self._filings.latest_reference(identity.lei)
        except EsefFilingUnavailable as unavailable:
            raise self._as_source_failure(
                unavailable,
                isinstance(unavailable, EsefRegisterError),
            ) from unavailable

        return PrimarySource(
            symbol=symbol.upper().strip(),
            # GLEIF's legal name, not the ticker's display name. The
            # document states its own name too, and `fetch` prefers that
            # one — but resolving must not need the document.
            company=identity.legal_name,
            source_type=SourceType.ANNUAL_REPORT,
            identifier=reference.filing_id,
            # The hash of the filed package: the same key always means
            # the same bytes, which is what lets knowledge read under it
            # never be read again.
            key=reference.content_hash,
            # The index states when it received the filing, which is the
            # closest thing it states to a publication date. It is not
            # the reporting period, and the two are kept apart.
            published_on=reference.added_on,
            reporting_period=ReportingPeriod(ends_on=reference.period_ends_on),
            document_format="xhtml",
            # Unstated by the index, and stated by the document. `fetch`
            # fills it in from what the report declares itself to be.
            language="",
            location=reference.location,
            provider=NAME,
            authority=SourceAuthority.REGULATOR_FILED,
            # What is established before the document is opened. The
            # third check — the document declaring the expected LEI —
            # is added by `fetch`, because it is the document's answer
            # and it has not been asked yet.
            verification=(
                IdentityCheck.SECURITY_REGISTRY,
                IdentityCheck.REGISTER_INDEXED,
            ),
        )

    def fetch(self, source: PrimarySource) -> SourceDocument:
        identity = self._identity(source.symbol)

        try:
            report = self._filings.read_url(source.location)
        except Exception as error:
            # A document the index says exists could not be read, which
            # is an outage rather than a gap in coverage.
            raise PrimarySourceProviderError(
                f"{source.stated()} could not be read."
            ) from error

        if report.lei and report.lei.upper() != identity.lei.upper():
            # The identity boundary, held at the last moment it can be.
            # A register that served the wrong document produces a
            # reading that is grounded, cited and about another company,
            # and nothing downstream would ever notice.
            raise PrimarySourceProviderError(
                f"{source.stated()} identifies itself as {report.lei}, and it "
                f"was fetched for {identity.lei} ({identity.legal_name}). "
                "Nothing was read from it."
            )

        if not report.business_text:
            raise PrimarySourceUnavailable(
                f"{source.stated()} tags no description of the company's "
                "operations or its segments, so there was nothing in it to "
                "read. The filing is real; what this platform reads is not "
                "in it."
            )

        return SourceDocument(
            source=self._as_read(
                source,
                report.company,
                report.language,
                self._checked(source, report.lei),
            ),
            # No `business_regions`. An ESEF package's description is
            # assembled out of the blocks the filer tagged, from wherever
            # in the report they sit, so there is no laid-out section for
            # headings to divide. Ownership stays positional here, which
            # is the weaker mechanism and the honest one: the alternative
            # is inventing structure the document did not supply.
            business_description=report.business_text,
            unstructured_text=report.unstructured_text,
            performance_discussion=report.discussion_text,
            performance_tables=report.discussion_tables,
        )

    @staticmethod
    def _checked(source: PrimarySource, report_lei: str) -> tuple[IdentityCheck, ...]:
        """The checks that stand once the document has answered for itself."""

        if not report_lei:
            return source.verification

        return (*source.verification, IdentityCheck.DOCUMENT_LEI)

    # ── identity ────────────────────────────────────────────────────

    def _identity(self, symbol: str) -> IssuerIdentity:
        try:
            return self._issuers.of(symbol)
        except IssuerUnknown as unknown:
            raise self._as_source_failure(
                unknown,
                isinstance(unknown, IssuerRegistryError),
            ) from unknown

    @staticmethod
    def _as_source_failure(
        failure: Exception,
        reachable: bool,
    ) -> PrimarySourceUnavailable:
        """A gap and an outage, kept apart all the way up.

        Only one of the two is worth asking about again, and a caller
        told merely "no source" could not tell which it had.
        """

        if reachable:
            return PrimarySourceProviderError(str(failure))

        return PrimarySourceUnavailable(str(failure))

    @staticmethod
    def _as_read(
        source: PrimarySource,
        company: str,
        language: str,
        verification: tuple[IdentityCheck, ...],
    ) -> PrimarySource:
        """The source as the document itself describes it.

        Three facts the index does not state and the report does: what
        the filer calls itself, which language it published in, and
        whether it identified its own issuer. All three are stored with
        the knowledge, so a reader can see that a French group's report
        was read in English — and that the document said so itself —
        rather than assume either.
        """

        return replace(
            source,
            company=company or source.company,
            language=language or source.language,
            verification=verification,
        )
