"""SEC EDGAR as a primary-source provider: the first of several."""

from __future__ import annotations

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
from app.providers.edgar_filings import EdgarFilings, FilingUnavailable

NAME = "SEC EDGAR"


class EdgarProvider:
    """
    The regulator's own record, for the companies it registers.

    EDGAR is the strongest form of the document: the filer wrote it, the
    regulator received it on a dated record, and an accession number
    identifies it forever. That immutability is what lets knowledge read
    from it be kept rather than re-read.

    Its limit is jurisdiction, not quality. A company listed only in
    Europe files with its own regulator and is not here — which this
    reports as the coverage gap it is, for the next provider to close.
    """

    name = NAME

    def __init__(self, filings: EdgarFilings | None = None) -> None:
        self._filings = filings or EdgarFilings()

    def resolve(self, symbol: str) -> PrimarySource:
        try:
            reference = self._filings.latest_reference(symbol)
        except FilingUnavailable as unavailable:
            raise PrimarySourceUnavailable(str(unavailable)) from unavailable

        return PrimarySource(
            symbol=symbol.upper().strip(),
            company=reference.company,
            source_type=SourceType.ANNUAL_REPORT,
            identifier=f"{reference.form} {reference.accession}",
            # The accession is already an immutable identity: a filing is
            # never revised in place, so nothing needs hashing here.
            key=reference.accession,
            published_on=reference.filed_on,
            # The index states the period end; it states no start, and a
            # year subtracted from the end would be an inference.
            reporting_period=(
                ReportingPeriod(ends_on=reference.period_ends_on)
                if reference.period_ends_on is not None
                else None
            ),
            document_format="html",
            language="en",
            location=reference.url,
            provider=NAME,
            authority=SourceAuthority.REGULATOR_FILED,
            # One check, and it does two jobs: EDGAR's own index names
            # this filing as this ticker's filer's. The filing itself
            # declares no LEI, so there is no second, independent
            # statement of identity from the document — which is a real
            # difference from an ESEF package and is recorded as one
            # rather than assumed away because EDGAR is a regulator.
            verification=(IdentityCheck.REGISTER_INDEXED,),
            # The regulator stated the form; it is carried as data
            # rather than left to be parsed back out of `identifier`.
            form=reference.form,
        )

    def fetch(self, source: PrimarySource) -> SourceDocument:
        try:
            # The form travels with the source, so the section reader
            # is told which document it is reading. It is read from
            # the field and never parsed back out of `identifier`.
            filing = self._filings.read_url(source.location, form=source.form)
        except Exception as error:
            # Reaching a document that the index says exists failed, which
            # is an outage rather than a gap in coverage.
            raise PrimarySourceProviderError(
                f"{source.stated()} could not be read."
            ) from error

        return SourceDocument(
            source=source,
            # Carried, not raised. A filing whose business section is a
            # page range into another component still prints audited
            # statements this platform reads, and an exception would
            # take all three away to report the first.
            business_refusal=filing.business_refusal,
            discussion_refusal=filing.discussion_refusal,
            business_description=filing.business_text,
            business_regions=filing.business_regions,
            performance_discussion=filing.discussion_text,
            performance_tables=filing.discussion_tables,
            income_statement_text=filing.income_statement_text,
            income_statement_tables=filing.income_statement_tables,
            balance_sheet_text=filing.balance_sheet_text,
            balance_sheet_tables=filing.balance_sheet_tables,
            cash_flow_text=filing.cash_flow_text,
            cash_flow_tables=filing.cash_flow_tables,
            income_statement_contenders=filing.income_statement_contenders,
            balance_sheet_contenders=filing.balance_sheet_contenders,
            cash_flow_contenders=filing.cash_flow_contenders,
        )
