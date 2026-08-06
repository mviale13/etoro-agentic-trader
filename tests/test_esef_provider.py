"""Europe behind the same seam, and the identity boundary it inherits."""

from datetime import date

import pytest

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceType,
)
from app.providers.esef_filings import (
    EsefFilingReference,
    EsefFilingUnavailable,
    EsefRegisterError,
    EsefReport,
)
from app.providers.esef_provider import EsefProvider
from app.providers.issuer_identity import (
    IssuerIdentity,
    IssuerRegistryError,
    IssuerUnknown,
)

LEI = "R0MUWSFPU8MPRO8K5P83"

IDENTITY = IssuerIdentity(
    symbol="BNP.PA",
    isin="FR0000131104",
    lei=LEI,
    legal_name="BNP PARIBAS",
)

REFERENCE = EsefFilingReference(
    lei=LEI,
    filing_id=f"{LEI}-2025-12-31-ESEF-FR-0",
    country="FR",
    period_ends_on=date(2025, 12, 31),
    added_on=date(2026, 3, 24),
    content_hash="fe1d9dc955469acb59668fb33da10d1a",
    location="https://filings.xbrl.org/report.xhtml",
)

REPORT = EsefReport(
    company="BNP Paribas Group",
    lei=LEI,
    language="en",
    business_text="The Group is composed of three operating divisions.",
    discussion_text="Income by business segment.",
)


class Issuers:
    def __init__(self, identity: object = IDENTITY) -> None:
        self._identity = identity

    def of(self, symbol: str) -> IssuerIdentity:
        if isinstance(self._identity, Exception):
            raise self._identity

        assert isinstance(self._identity, IssuerIdentity)

        return self._identity


class Filings:
    def __init__(
        self,
        reference: object = REFERENCE,
        report: object = REPORT,
    ) -> None:
        self._reference = reference
        self._report = report

    def latest_reference(self, lei: str) -> EsefFilingReference:
        if isinstance(self._reference, Exception):
            raise self._reference

        assert isinstance(self._reference, EsefFilingReference)

        return self._reference

    def read_url(self, url: str) -> EsefReport:
        if isinstance(self._report, Exception):
            raise self._report

        assert isinstance(self._report, EsefReport)

        return self._report


def provider(issuers: object = None, filings: object = None) -> EsefProvider:
    return EsefProvider(
        filings=filings or Filings(),  # type: ignore[arg-type]
        issuers=issuers or Issuers(),  # type: ignore[arg-type]
    )


def test_the_canonical_source_carries_what_the_extraction_needs() -> None:
    """
    Nothing downstream may care that this document came from Europe.

    Everything needed to fetch it, cite it and key it permanently is on
    the same object EDGAR builds, filled from a different register.
    """

    source = provider().resolve("bnp.pa")

    assert source.symbol == "BNP.PA"
    assert source.company == "BNP PARIBAS"
    assert source.source_type is SourceType.ANNUAL_REPORT
    assert source.identifier == REFERENCE.filing_id
    assert source.key == REFERENCE.content_hash
    assert source.published_on == date(2026, 3, 24)
    assert source.reporting_period is not None
    assert source.reporting_period.ends_on == date(2025, 12, 31)
    assert source.reporting_period.fiscal_year == 2025
    assert source.location == REFERENCE.location
    assert source.provider == "ESEF"


def test_an_esef_filing_is_regulator_filed_and_says_which_checks_held() -> None:
    """
    A register received it, and the document also answered for itself.

    Both are recorded, because they are different guarantees: the index
    said whose filing this is, and then the filing said so too. EDGAR
    can only offer the first.
    """

    source = provider().resolve("BNP.PA")

    assert source.authority is SourceAuthority.REGULATOR_FILED
    assert source.verification == (
        IdentityCheck.SECURITY_REGISTRY,
        IdentityCheck.REGISTER_INDEXED,
    )

    read = provider().fetch(source)

    assert IdentityCheck.DOCUMENT_LEI in read.source.verification


def test_a_filing_that_never_identified_itself_does_not_claim_it_did() -> None:
    """The check is recorded because it happened, not because it usually does."""

    silent = EsefReport(
        company="BNP Paribas Group",
        lei="",
        language="fr",
        business_text="The Group is composed of three operating divisions.",
    )

    read = provider(filings=Filings(report=silent)).fetch(provider().resolve("BNP.PA"))

    assert IdentityCheck.DOCUMENT_LEI not in read.source.verification


def test_the_key_is_the_bytes_and_not_a_name_for_them() -> None:
    """Knowledge read under it is never read again, so it must not move."""

    assert provider().resolve("BNP.PA").key == REFERENCE.content_hash


def test_the_period_reported_on_is_kept_apart_from_the_filing_date() -> None:
    """
    A report published in March accounts for the December before it.

    Comparing the wrong one compares the wrong thing, so both are stated
    and neither is derived from the other.
    """

    source = provider().resolve("BNP.PA")

    assert source.reporting_period is not None
    assert source.reporting_period.ends_on < source.published_on


def test_a_company_with_no_established_identity_is_a_gap() -> None:
    with pytest.raises(PrimarySourceUnavailable) as unavailable:
        provider(issuers=Issuers(IssuerUnknown("AAPL is not on the list."))).resolve(
            "AAPL"
        )

    assert not isinstance(unavailable.value, PrimarySourceProviderError)
    assert "not on the list" in str(unavailable.value)


def test_a_register_that_could_not_be_reached_is_not_a_gap() -> None:
    """
    Different situations, and only one of them is worth retrying.

    The knowledge service reads exactly this distinction to decide
    whether asking again could plausibly change the answer.
    """

    with pytest.raises(PrimarySourceProviderError):
        provider(issuers=Issuers(IssuerRegistryError("GLEIF timed out."))).resolve(
            "BNP.PA"
        )

    with pytest.raises(PrimarySourceProviderError):
        provider(filings=Filings(reference=EsefRegisterError("index down"))).resolve(
            "BNP.PA"
        )


def test_an_issuer_the_index_does_not_carry_stays_a_gap() -> None:
    with pytest.raises(PrimarySourceUnavailable) as failure:
        provider(
            filings=Filings(reference=EsefFilingUnavailable("Germany does not."))
        ).resolve("SAP.DE")

    assert not isinstance(failure.value, PrimarySourceProviderError)


def test_the_document_is_read_into_the_two_sections_the_extraction_asks_for() -> None:
    document = provider().fetch(provider().resolve("BNP.PA"))

    assert document.business_description == REPORT.business_text
    assert document.performance_discussion == REPORT.discussion_text


def test_the_document_s_own_name_and_language_are_what_is_recorded() -> None:
    """
    Two facts the index does not state and the report does.

    A reader of the stored knowledge can then see that a French group's
    report was read in English rather than assume it.
    """

    document = provider().fetch(provider().resolve("BNP.PA"))

    assert document.source.company == "BNP Paribas Group"
    assert document.source.language == "en"
    assert document.source.document_format == "xhtml"


def test_a_document_that_belongs_to_another_company_is_refused() -> None:
    """
    The identity boundary, held at the last moment it can be.

    Grounding proves that facts belong to a document; it cannot prove
    that the document belongs to the security. A register that served
    the wrong file produces a reading that is exactly cited, entirely
    grounded and about somebody else, and nothing downstream would ever
    notice.
    """

    served = EsefReport(
        company="SANOFI",
        lei="549300E9PC51EN656011",
        language="fr",
        business_text="Sanofi is a healthcare company.",
    )

    with pytest.raises(PrimarySourceProviderError) as refused:
        provider(filings=Filings(report=served)).fetch(provider().resolve("BNP.PA"))

    assert "549300E9PC51EN656011" in str(refused.value)
    assert "Nothing was read from it" in str(refused.value)


def test_a_filing_that_tags_nothing_this_platform_reads_says_so() -> None:
    """
    A real filing that contains none of what is looked for.

    Reported as the gap it is, rather than by handing the extraction
    some other part of the document.
    """

    untagged = EsefReport(company="Exemple", lei=LEI, language="fr", business_text="")

    with pytest.raises(PrimarySourceUnavailable) as gap:
        provider(filings=Filings(report=untagged)).fetch(provider().resolve("BNP.PA"))

    assert "tags no description" in str(gap.value)


def test_a_document_that_cannot_be_read_is_an_outage_not_a_gap() -> None:
    with pytest.raises(PrimarySourceProviderError):
        provider(filings=Filings(report=OSError("connection reset"))).fetch(
            provider().resolve("BNP.PA")
        )


def test_europe_is_asked_only_where_the_regulator_holds_nothing() -> None:
    """
    Order is priority, and it matters for the issuers that are in both.

    A European group listed in New York files a 20-F with the SEC and an
    annual financial report at home, and EDGAR's is the one already
    proven to read well.
    """

    from app.providers.primary_source_provider import PrimarySourceResolver

    names = [provider.name for provider in PrimarySourceResolver()._providers]

    assert names == ["SEC EDGAR", "ESEF", "Official Investor Relations"]
