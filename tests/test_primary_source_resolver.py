"""Which provider supplies a company's own account of itself."""

from datetime import date

import pytest

from app.domain.primary_source import (
    PrimarySource,
    PrimarySourceUnavailable,
    SourceDocument,
    SourceType,
)
from app.providers.primary_source_provider import PrimarySourceResolver


class ProviderStub:
    def __init__(self, name: str, unavailable: str | None = None) -> None:
        self.name = name
        self._unavailable = unavailable
        self.asked = 0

    def resolve(self, symbol: str) -> PrimarySource:
        self.asked += 1

        if self._unavailable is not None:
            raise PrimarySourceUnavailable(self._unavailable)

        return PrimarySource(
            symbol=symbol,
            company="Example",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="AR-2025",
            key=f"{self.name}:AR-2025",
            published_on=date(2025, 11, 13),
            reporting_period="FY2025",
            document_format="xhtml",
            language="fr",
            location="https://example.test/ar-2025",
            provider=self.name,
        )

    def fetch(self, source: PrimarySource) -> SourceDocument:
        return SourceDocument(source=source, business_description="")


def test_the_first_provider_that_holds_the_company_wins() -> None:
    """
    Order is priority: the most authoritative source that has it.

    A company the regulator does not hold is not a company without an
    annual report — it is one published somewhere the next provider
    reaches.
    """

    regulator = ProviderStub("SEC EDGAR", unavailable="Not listed with the SEC.")
    european = ProviderStub("ESEF")

    source, provider = PrimarySourceResolver((regulator, european)).resolve("BNP.PA")

    assert provider is european
    assert source.provider == "ESEF"
    assert source.language == "fr"

    assert regulator.asked == 1


def test_a_provider_that_answers_stops_the_search() -> None:
    regulator = ProviderStub("SEC EDGAR")
    european = ProviderStub("ESEF")

    PrimarySourceResolver((regulator, european)).resolve("DIS")

    assert european.asked == 0


def test_every_provider_s_reason_survives_when_none_can_answer() -> None:
    """
    "Not listed" and "could not be reached" are different situations.

    A caller told only "no source" cannot tell a gap in coverage from an
    outage, and those call for opposite responses.
    """

    resolver = PrimarySourceResolver(
        (
            ProviderStub("SEC EDGAR", unavailable="Not listed with the SEC."),
            ProviderStub("ESEF", unavailable="The register could not be reached."),
        )
    )

    with pytest.raises(PrimarySourceUnavailable) as unavailable:
        resolver.resolve("BNP.PA")

    reason = str(unavailable.value)

    assert "SEC EDGAR: Not listed with the SEC." in reason
    assert "ESEF: The register could not be reached." in reason


def test_the_canonical_source_carries_what_any_provider_must_state() -> None:
    """
    The extraction must not care where a document came from.

    Everything it needs to fetch, cite and permanently key the document
    is on this object, whichever provider built it.
    """

    source, _ = PrimarySourceResolver((ProviderStub("ESEF"),)).resolve("BNP.PA")

    assert source.key
    assert source.identifier
    assert source.published_on
    assert source.document_format
    assert source.language
    assert source.location
    assert source.provider
    assert source.source_type is SourceType.ANNUAL_REPORT
