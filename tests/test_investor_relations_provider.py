"""The company's own report, where no register holds one.

The acceptance criteria for the first provider whose source no regulator
received, one test each:

1. the bytes come from an approved official source;
2. the document key is derived honestly;
3. the issuer is identified from the document and the location;
4. the issuer is matched to the security through the existing boundary;
5. the same grounded extraction pipeline works unchanged;
6. weak or ambiguous identity produces unavailability, never knowledge.
"""

import hashlib
import io
import zipfile
from datetime import date

import pytest

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceType,
)
from app.providers.investor_relations_provider import InvestorRelationsProvider
from app.providers.investor_relations_sources import (
    PUBLISHED_REPORTS,
    PublishedReport,
)
from app.providers.issuer_identity import IssuerIdentity, IssuerUnknown

LEI = "529900NNUPAGGOMPXZ31"

IDENTITY = IssuerIdentity(
    symbol="VOW3.DE",
    isin="DE0007664039",
    lei=LEI,
    legal_name="VOLKSWAGEN AKTIENGESELLSCHAFT",
)


def report_xhtml(lei: str = LEI, period: str = "2025-12-31") -> str:
    return f"""\
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xml:lang="de">
<body>
<ix:header><ix:hidden>
 <xbrli:context id="C1"><xbrli:entity>
  <xbrli:identifier scheme="http://standards.iso.org/iso/17442">{lei}</xbrli:identifier>
 </xbrli:entity>
 <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate>
 <xbrli:endDate>{period}</xbrli:endDate></xbrli:period></xbrli:context>
</ix:hidden></ix:header>
<p><ix:nonNumeric contextRef="C1"
  name="ifrs-full:NameOfReportingEntityOrOtherMeansOfIdentification"
  >Volkswagen AG</ix:nonNumeric></p>
<div><ix:nonNumeric contextRef="C1"
  name="ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory"
  >Der Konzern berichtet die Segmente Pkw, Nutzfahrzeuge und
  Finanzdienstleistungen.</ix:nonNumeric></div>
</body></html>
"""


UNTAGGED = "<html><body><p>Zusammengefasster Lagebericht.</p></body></html>"


def package(*members: str) -> bytes:
    """An ESEF package: several documents, only some of them tagged."""

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("vw/META-INF/catalog.xml", "<catalog/>")

        for index, member in enumerate(members):
            archive.writestr(f"vw/reports/report-{index}.xhtml", member)

    return buffer.getvalue()


PACKAGE = package(report_xhtml(), UNTAGGED)


def entry(archive: bytes = PACKAGE, **overrides: object) -> PublishedReport:
    fields: dict = {
        "symbol": "VOW3.DE",
        "location": "https://uploads.vw-mms.de/system/VWAG-2025-12-31-DE.zip",
        "approved_hosts": ("uploads.vw-mms.de",),
        "content_hash": hashlib.sha256(archive).hexdigest(),
        "period_ends_on": date(2025, 12, 31),
        "published_on": date(2026, 3, 10),
        "identifier": "VWAG_JFB_Konzern-2025-12-31-DE.zip",
    }
    fields.update(overrides)

    return PublishedReport(**fields)  # type: ignore[arg-type]


class Issuers:
    def __init__(self, identity: object = IDENTITY) -> None:
        self._identity = identity

    def of(self, symbol: str) -> IssuerIdentity:
        if isinstance(self._identity, Exception):
            raise self._identity

        assert isinstance(self._identity, IssuerIdentity)

        return self._identity


class Response:
    def __init__(self, content: bytes, url: str) -> None:
        self.content = content
        self.url = url


def provider(
    archive: bytes = PACKAGE,
    served_from: str | None = None,
    issuers: object = None,
    reports: object = None,
) -> InvestorRelationsProvider:
    published = entry(archive) if reports is None else reports

    built = InvestorRelationsProvider(
        reports=(
            {"VOW3.DE": published} if isinstance(published, PublishedReport) else {}
        ),
        issuers=issuers or Issuers(),  # type: ignore[arg-type]
    )

    landed = served_from or (
        published.location
        if isinstance(published, PublishedReport)
        else "https://uploads.vw-mms.de/x"
    )

    built._got = lambda url: Response(archive, landed)  # type: ignore[assignment]

    return built


# ── 1. the bytes come from an approved official source ──────────────


def test_bytes_served_from_an_unapproved_host_are_refused() -> None:
    """
    Where the bytes came from, not where the request was aimed.

    A redirect off an approved host is how a mirror, a link shortener or
    a compromised page serves a document that looks right and is not.
    """

    with pytest.raises(PrimarySourceProviderError) as refused:
        provider(served_from="https://cdn.mirror.example/vw.zip").fetch(
            provider().resolve("VOW3.DE")
        )

    assert "not a host reviewed" in str(refused.value)


def test_a_location_nobody_reviewed_is_absent_rather_than_searched_for() -> None:
    """
    A crawler finds something plausible; a review establishes something.

    Only the second is a claim about identity, and identity is the thing
    this platform refuses to guess at.
    """

    absent = InvestorRelationsProvider(
        reports={},
        issuers=Issuers(),  # type: ignore[arg-type]
    )

    with pytest.raises(PrimarySourceUnavailable) as gap:
        absent.resolve("VOW3.DE")

    assert "reviewed rather than discovered" in str(gap.value)


# ── 2. the document key is derived honestly ─────────────────────────


def test_the_key_is_the_hash_of_the_bytes_that_were_reviewed() -> None:
    """Nobody assigned this document a number, so it is what it is made of."""

    source = provider().resolve("VOW3.DE")

    assert source.key == hashlib.sha256(PACKAGE).hexdigest()
    assert source.authority is SourceAuthority.ISSUER_PUBLISHED
    assert source.source_type is SourceType.ANNUAL_REPORT


def test_a_document_that_changed_underneath_us_stops_rather_than_slides() -> None:
    """
    An issuer can replace a file at the same address.

    Most likely because it published its next annual report — which is
    exactly the moment a person should look, rather than a machine
    quietly reading something nobody reviewed.
    """

    replaced = package(report_xhtml(), "<html><body>Etwas anderes.</body></html>")

    # The entry still records the hash that was reviewed; the address now
    # serves something else. Note that the replacement is a *genuine*
    # Volkswagen document — it passes every identity check there is, and
    # is still refused, because nobody reviewed it.
    moved = provider(archive=replaced, reports=entry(PACKAGE))

    with pytest.raises(PrimarySourceUnavailable) as stale:
        moved.fetch(moved.resolve("VOW3.DE"))

    assert "no longer the one that was reviewed" in str(stale.value)


def test_resolving_costs_nothing_but_the_identity_lookup() -> None:
    """
    There is no index to ask, so the reviewed entry answers by itself.

    Which means a company whose report has already been read never
    downloads six megabytes to discover that.
    """

    built = InvestorRelationsProvider(
        reports={"VOW3.DE": entry()},
        issuers=Issuers(),  # type: ignore[arg-type]
    )

    def refuse(url: str) -> Response:
        raise AssertionError("resolve must not fetch the document")

    built._got = refuse  # type: ignore[assignment]

    assert built.resolve("VOW3.DE").key == hashlib.sha256(PACKAGE).hexdigest()


# ── 3. the issuer is identified from the document itself ────────────


def test_the_document_declares_its_own_issuer_and_that_is_recorded() -> None:
    document = provider().fetch(provider().resolve("VOW3.DE"))

    assert document.source.company == "Volkswagen AG"
    assert document.source.language == "de"
    assert IdentityCheck.DOCUMENT_LEI in document.source.verification


def test_a_document_that_cannot_say_whose_it_is_never_becomes_knowledge() -> None:
    """
    The hard line, and the reason PDF-only issuers stay out of reach.

    Everything else about such a document may be in order. Without this
    it stays a document about some company rather than about this one,
    and the domain it sits on is not an authority on which.
    """

    anonymous = package(UNTAGGED)

    with pytest.raises(PrimarySourceUnavailable) as refused:
        provider(archive=anonymous).fetch(
            provider(archive=anonymous).resolve("VOW3.DE")
        )

    assert "identifies its own issuer" in str(refused.value)


def test_a_package_whose_documents_disagree_about_the_issuer_is_refused() -> None:
    """Refused entire, rather than resolved in favour of one of them."""

    mixed = package(report_xhtml(), report_xhtml(lei="529900D6BF99LW9R2E68"))

    with pytest.raises(PrimarySourceUnavailable) as refused:
        provider(archive=mixed).fetch(provider(archive=mixed).resolve("VOW3.DE"))

    assert "more than one issuer" in str(refused.value)


# ── 4. the issuer is matched to the security ────────────────────────


def test_a_genuine_report_of_another_company_is_refused() -> None:
    """
    The `BTC` failure arriving by a different path.

    A real annual report, correctly read, entirely grounded — and about
    a company that is not the security being analysed.
    """

    subsidiary = package(report_xhtml(lei="529900W18LQJZN1LQ21"))

    with pytest.raises(PrimarySourceProviderError) as refused:
        provider(archive=subsidiary).fetch(
            provider(archive=subsidiary).resolve("VOW3.DE")
        )

    assert "529900W18LQJZN1LQ21" in str(refused.value)
    assert "Nothing was read from it" in str(refused.value)


def test_a_security_with_no_established_issuer_never_reaches_a_document() -> None:
    with pytest.raises(PrimarySourceUnavailable):
        provider(issuers=Issuers(IssuerUnknown("AAPL is not on the list."))).resolve(
            "AAPL"
        )


def test_a_document_dated_to_another_year_than_the_review_is_refused() -> None:
    """A reviewer's typo must not quietly re-date a company's report."""

    other_year = package(report_xhtml(period="2024-12-31"))

    with pytest.raises(PrimarySourceUnavailable) as refused:
        provider(archive=other_year).fetch(
            provider(archive=other_year).resolve("VOW3.DE")
        )

    assert "2024-12-31" in str(refused.value)


# ── 5. the extraction pipeline is handed exactly what it expects ────


def test_the_same_two_passages_reach_the_extraction_unchanged() -> None:
    """
    Nothing downstream may care that no regulator received this.

    The document is the ESEF package the issuer filed, read by the same
    tag-driven reader — so what the extraction receives is shaped
    identically to a document from a register.
    """

    document = provider().fetch(provider().resolve("VOW3.DE"))

    assert "Pkw" in document.business_description
    assert document.source.document_format == "xhtml"
    assert document.source.reporting_period is not None
    assert document.source.reporting_period.ends_on == date(2025, 12, 31)


# ── 6. authority and verification are stated, never argued ──────────


def test_a_citation_says_what_kind_of_source_it_was() -> None:
    """
    "Filed with a regulator" and "published by the company" are
    different claims, and a reader must not have to infer which.
    """

    source = provider().fetch(provider().resolve("VOW3.DE")).source

    assert source.attested() == "published by the issuer"
    assert "published by the issuer" in source.stated()


def test_the_checks_that_actually_succeeded_travel_with_the_document() -> None:
    """
    The audit trail: authority says what the source is, provenance says
    where it came from, and this says what was proven.

    No register indexed this document, and it is never claimed that one
    did.
    """

    verified = provider().fetch(provider().resolve("VOW3.DE")).source.verification

    assert set(verified) == {
        IdentityCheck.SECURITY_REGISTRY,
        IdentityCheck.APPROVED_SOURCE,
        IdentityCheck.CONTENT_HASHED,
        IdentityCheck.DOCUMENT_LEI,
    }
    assert IdentityCheck.REGISTER_INDEXED not in verified


# ── the reviewed list itself ────────────────────────────────────────


def test_every_reviewed_entry_is_checkable_by_hand() -> None:
    for symbol, published in PUBLISHED_REPORTS.items():
        assert published.symbol == symbol
        assert published.approved_hosts
        assert len(published.content_hash) == 64
        assert published.serves(published.location)
        assert not published.serves("https://cdn.mirror.example/anything.zip")
