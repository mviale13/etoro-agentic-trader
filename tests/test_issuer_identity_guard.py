"""A symbol that changed hands must not serve the new owner's filings.

Measured, not imagined: PR #190's harvest keyed on `PARA` returned seven
Item 5.02 filings belonging to **Banzai International**, because
Paramount was delisted and the SEC reassigned the ticker. Every filing
was genuine, every date was real, and none of it was about the company
the reader asked for.

Everything here is offline.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.issuer_identity import (
    IssuerIdentity,
    IssuerReassigned,
    issuer_id_in,
    reconcile,
)
from app.domain.primary_source import (
    PrimarySource,
    PrimarySourceUnavailable,
    SourceAuthority,
    SourceType,
)
from app.providers.primary_source_provider import PrimarySourceResolver

PARAMOUNT = "https://www.sec.gov/Archives/edgar/data/813828/000081382824000045/para.htm"
BANZAI = "https://www.sec.gov/Archives/edgar/data/1826011/000164117225018464/bnzi.htm"


def _identity(issuer: str, name: str, when: str = "2024-01-01") -> IssuerIdentity:
    return IssuerIdentity(
        symbol="PARA",
        registry="SEC EDGAR",
        issuer_id=issuer,
        name=name,
        observed_on=date.fromisoformat(when),
    )


# ── reading the issuer out of an address ────────────────────────────────


def test_the_issuer_number_is_read_from_the_document_s_own_address() -> None:
    """No new field was needed, so no stored record had to be rewritten."""

    assert issuer_id_in(PARAMOUNT) == "813828"
    assert issuer_id_in(BANZAI) == "1826011"


def test_two_spellings_of_one_number_are_one_issuer() -> None:
    """EDGAR prints `4962` in a path and `0000004962` in an accession."""

    padded = "https://www.sec.gov/Archives/edgar/data/0000004962/x/y.htm"
    bare = "https://www.sec.gov/Archives/edgar/data/4962/x/y.htm"

    assert issuer_id_in(padded) == issuer_id_in(bare) == "4962"


def test_an_address_this_cannot_read_yields_no_claim() -> None:
    """Absent is absent. A guess here is the failure being guarded."""

    assert issuer_id_in("https://www.example.com/annual-report.pdf") is None
    assert issuer_id_in("") is None


# ── the rule ────────────────────────────────────────────────────────────


def test_the_measured_reassignment_is_refused() -> None:
    with pytest.raises(IssuerReassigned) as refused:
        reconcile(
            _identity("813828", "Paramount Global"),
            _identity("1826011", "Banzai International, Inc.", "2025-07-09"),
        )

    said = str(refused.value)

    # The refusal has to be readable by a person, so it names both.
    assert "Paramount Global" in said
    assert "Banzai International, Inc." in said
    assert "813828" in said and "1826011" in said
    assert "different companies" in said


def test_the_same_issuer_under_a_new_filing_is_not_a_conflict() -> None:
    reconcile(
        _identity("813828", "Paramount Global", "2023-02-01"),
        _identity("813828", "Paramount Global", "2024-02-01"),
    )


def test_a_first_reading_has_nothing_to_disagree_with() -> None:
    """And the limit that follows is stated rather than hidden.

    This catches a symbol changing hands *between* two readings. It
    cannot catch one that was already pointing at the wrong issuer the
    first time it was read.
    """

    reconcile(None, _identity("1826011", "Banzai International, Inc."))


def test_two_registers_numbering_one_company_are_not_compared() -> None:
    """Otherwise every provider change would raise, which is noise."""

    held = IssuerIdentity(
        symbol="DB",
        registry="SEC EDGAR",
        issuer_id="1159508",
        name="DEUTSCHE BANK AKTIENGESELLSCHAFT",
        observed_on=date(2026, 3, 12),
    )
    elsewhere = IssuerIdentity(
        symbol="DB",
        registry="ESEF",
        issuer_id="7LTWFZYICNSX8D621K86",
        name="Deutsche Bank AG",
        observed_on=date(2026, 4, 1),
    )

    reconcile(held, elsewhere)


# ── the guard where it is wired ─────────────────────────────────────────


class _Provider:
    """A provider that resolves a symbol to whichever filer it is given."""

    name = "SEC EDGAR"

    def __init__(self, location: str, company: str) -> None:
        self._location = location
        self._company = company

    def resolve(self, symbol: str) -> PrimarySource:
        return PrimarySource(
            symbol=symbol,
            company=self._company,
            source_type=SourceType.ANNUAL_REPORT,
            identifier="8-K test",
            key="test",
            published_on=date(2025, 7, 9),
            reporting_period=None,
            document_format="html",
            language="en",
            location=self._location,
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(),
        )

    def fetch(self, source: PrimarySource) -> object:  # pragma: no cover
        raise AssertionError("the guard must refuse before anything is fetched")


def test_the_resolver_refuses_before_the_document_is_fetched() -> None:
    resolver = PrimarySourceResolver(
        providers=(_Provider(BANZAI, "Banzai International, Inc."),),
        held_identity=lambda symbol: _identity("813828", "Paramount Global"),
    )

    with pytest.raises(IssuerReassigned):
        resolver.resolve("PARA")


def test_a_reassignment_does_not_fall_through_to_the_next_provider() -> None:
    """The hazard a plain `except` would have created.

    `resolve` collects each provider's reason and tries the next one. A
    reassignment is not an outage: trying the next register for a symbol
    whose issuer is in doubt is how the wrong company's filing gets
    served anyway. So `IssuerReassigned` propagates.
    """

    tried: list[str] = []

    class _Second(_Provider):
        name = "ESEF"

        def resolve(self, symbol: str) -> PrimarySource:
            tried.append(self.name)
            return super().resolve(symbol)

    resolver = PrimarySourceResolver(
        providers=(
            _Provider(BANZAI, "Banzai International, Inc."),
            _Second(PARAMOUNT, "Paramount Global"),
        ),
        held_identity=lambda symbol: _identity("813828", "Paramount Global"),
    )

    with pytest.raises(IssuerReassigned):
        resolver.resolve("PARA")

    assert tried == []


def test_an_agreeing_symbol_resolves_exactly_as_before() -> None:
    resolver = PrimarySourceResolver(
        providers=(_Provider(PARAMOUNT, "Paramount Global"),),
        held_identity=lambda symbol: _identity("813828", "Paramount Global"),
    )

    source, provider = resolver.resolve("PARA")

    assert source.company == "Paramount Global"
    assert provider.name == "SEC EDGAR"


def test_an_unreadable_held_address_leaves_the_symbol_unguarded() -> None:
    """Honestly unguarded, and it must not become a refusal.

    A source whose address states no issuer number this can parse gives
    no claim. Refusing there would block every non-EDGAR provider to
    catch a reassignment that cannot be observed from it.
    """

    resolver = PrimarySourceResolver(
        providers=(_Provider(BANZAI, "Banzai International, Inc."),),
        held_identity=lambda symbol: None,
    )

    source, _ = resolver.resolve("PARA")

    assert source.company == "Banzai International, Inc."


def test_the_refusal_is_not_a_coverage_gap() -> None:
    """`IssuerReassigned` is its own exception, not an unavailability.

    A caller that treats "no source" and "two different companies" alike
    would word a reassignment as a company this platform does not cover,
    which is the opposite of what happened.
    """

    assert not issubclass(IssuerReassigned, PrimarySourceUnavailable)
