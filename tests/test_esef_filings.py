"""Finding a European annual report, and reading what the filer tagged."""

from datetime import date

import pytest

from app.providers.esef_filings import (
    EsefFilings,
    EsefFilingUnavailable,
    EsefRegisterError,
)

LEI = "R0MUWSFPU8MPRO8K5P83"

TODAY = date(2026, 8, 6)


def filing(
    period: str,
    added: str,
    ordinal: int = 0,
    scheme: str = "ESEF",
    country: str = "FR",
) -> dict:
    identifier = f"{LEI}-{period}-{scheme}-{country}-{ordinal}"

    return {
        "attributes": {
            "fxo_id": identifier,
            "country": country,
            "period_end": period,
            "date_added": f"{added} 10:43:06.453467",
            "sha256": f"hash-of-{identifier}",
            "report_url": f"/{LEI}/{period}/{scheme}/{country}/{ordinal}/report.xhtml",
        }
    }


class Index(EsefFilings):
    """The real reader with the network call replaced."""

    def __init__(self, payload: object) -> None:
        super().__init__()
        self._payload = payload

    def _get(self, url: str):  # type: ignore[override]
        if isinstance(self._payload, Exception):
            raise self._payload

        class Response:
            def __init__(self, payload: object) -> None:
                self._payload = payload

            def json(self) -> object:
                return self._payload

            @property
            def text(self) -> str:
                assert isinstance(self._payload, str)
                return self._payload

        return Response(self._payload)


# ── which filing is the annual report ───────────────────────────────


def test_the_latest_annual_report_is_the_one_read() -> None:
    reference = Index(
        {
            "data": [
                filing("2023-12-31", "2024-03-18"),
                filing("2025-12-31", "2026-03-24"),
                filing("2024-12-31", "2025-04-15"),
            ]
        }
    ).latest_reference(LEI, today=TODAY)

    assert reference.period_ends_on == date(2025, 12, 31)
    assert reference.added_on == date(2026, 3, 24)
    assert reference.content_hash == f"hash-of-{LEI}-2025-12-31-ESEF-FR-0"
    assert reference.location.startswith("https://filings.xbrl.org/")


def test_an_interim_report_is_not_an_annual_one() -> None:
    """
    Novo Nordisk files ESEF quarterly, and most issuers do not.

    Its most recent filing is usually three months of trading with none
    of the description of the business that makes a filing worth reading.
    ESEF mandates the annual report and nothing else, so the oldest
    filing on record establishes where the financial year ends.
    """

    reference = Index(
        {
            "data": [
                filing("2024-12-31", "2025-02-05", country="DK"),
                filing("2025-03-31", "2025-05-07", country="DK"),
                filing("2025-06-30", "2025-08-06", country="DK"),
                filing("2025-09-30", "2025-11-05", country="DK"),
                filing("2025-12-31", "2026-02-04", country="DK"),
                filing("2026-03-31", "2026-05-06", country="DK"),
            ]
        }
    ).latest_reference(LEI, today=TODAY)

    assert reference.period_ends_on == date(2025, 12, 31)


def test_a_period_that_has_not_ended_cannot_have_been_reported_on() -> None:
    """
    Met in the index rather than imagined.

    The register carries a Hermès filing whose period is stated as ending
    in December 2026 and whose document is the report for 2025. Taking
    the latest period would cite a year that has not happened.
    """

    reference = Index(
        {
            "data": [
                filing("2023-12-31", "2024-04-02"),
                filing("2024-12-31", "2025-04-15"),
                filing("2026-12-31", "2026-03-24"),
            ]
        }
    ).latest_reference(LEI, today=TODAY)

    assert reference.period_ends_on == date(2024, 12, 31)


def test_a_retailer_s_fifty_two_week_year_still_lands_on_its_anniversary() -> None:
    """Ahold Delhaize's year has ended on six different dates in six years."""

    reference = Index(
        {
            "data": [
                filing("2020-01-03", "2020-03-04", country="NL"),
                filing("2021-01-02", "2021-03-03", country="NL"),
                filing("2022-01-01", "2022-03-02", country="NL"),
                filing("2022-12-31", "2023-03-01", country="NL"),
                filing("2023-12-29", "2024-03-06", country="NL"),
                filing("2025-12-28", "2026-03-04", country="NL"),
            ]
        }
    ).latest_reference(LEI, today=TODAY)

    assert reference.period_ends_on == date(2025, 12, 28)


def test_two_filings_for_one_year_resolve_to_the_same_one_every_time() -> None:
    """
    BNP Paribas files its registration document in French and in English.

    Both are ESEF filings for the same period. Picking whichever the
    index happened to list first would change the document's key between
    two runs, and knowledge already read would be read again.
    """

    listed = [filing("2025-12-31", "2026-03-24", ordinal=1)]
    listed.append(filing("2025-12-31", "2026-03-24", ordinal=0))

    first = Index({"data": listed}).latest_reference(LEI, today=TODAY)
    second = Index({"data": list(reversed(listed))}).latest_reference(LEI, today=TODAY)

    assert first.filing_id == second.filing_id
    assert first.content_hash == second.content_hash


def test_a_filing_under_another_national_scheme_is_left_alone() -> None:
    """The index also carries filings this provider does not claim to read."""

    ukrainian = filing("2022-12-31", "2023-11-09", scheme="UAIFRS", country="UA")

    with pytest.raises(EsefFilingUnavailable):
        Index({"data": [ukrainian]}).latest_reference(LEI, today=TODAY)


def test_an_issuer_the_index_does_not_reach_is_a_stated_gap() -> None:
    """
    Germany's mechanism does not publish to the index.

    Every German issuer therefore resolves to a real company and to no
    filing, which is a fact about where this platform reaches and is
    reported as one.
    """

    with pytest.raises(EsefFilingUnavailable) as gap:
        Index({"data": []}).latest_reference(LEI, today=TODAY)

    assert "Germany" in str(gap.value)
    assert not isinstance(gap.value, EsefRegisterError)


def test_a_register_that_cannot_be_reached_is_worth_asking_again() -> None:
    with pytest.raises(EsefRegisterError):
        Index(OSError("the index could not be reached")).latest_reference(LEI)


# ── reading the document ────────────────────────────────────────────


DOCUMENT = """\
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xml:lang="FR">
<head><style>.a::after{content:"DisclosureOfOperatingSegmentsExplanatory"}</style></head>
<body>
<ix:header><ix:hidden>
 <xbrli:context id="C1"><xbrli:entity>
  <xbrli:identifier scheme="http://standards.iso.org/iso/17442">R0MUWSFPU8MPRO8K5P83</xbrli:identifier>
 </xbrli:entity></xbrli:context>
 <ix:nonNumeric name="ifrs-full:NameOfReportingEntityOrOtherMeansOfIdentification"
   contextRef="C1">A placeholder nobody reads</ix:nonNumeric>
</ix:hidden></ix:header>
<header>Exemple &#8212; Annual report</header>
<p><ix:nonNumeric name="ifrs-full:NameOfReportingEntityOrOtherMeansOfIdentification"
  contextRef="C1">Exemple Groupe</ix:nonNumeric></p>
<p><ix:nonNumeric
  name="ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities"
  contextRef="C1" continuedAt="k1" escape="true"></ix:nonNumeric></p>
<p><ix:continuation id="k1" continuedAt="k2">Exemple, a <ix:nonNumeric
  name="ifrs-full:LegalFormOfEntity"
  contextRef="C1">soci&#233;t&#233; anonyme</ix:nonNumeric>,
  runs two divisions.</ix:continuation></p>
<p>Prose the filer tagged nothing in.</p>
<p><ix:continuation id="k2">The divisions are Trains and Boats.</ix:continuation></p>
<div><ix:nonNumeric name="ifrs-full:DisclosureOfOperatingSegmentsExplanatory"
  contextRef="C1"><table><tr><td>Trains</td><td>700</td></tr>
  <tr><td>Boats</td><td>300</td></tr></table></ix:nonNumeric></div>
</body></html>
"""


def read(document: str = DOCUMENT):
    return Index(document).read_url("https://filings.xbrl.org/example.xhtml")


def test_the_filer_s_own_tagging_is_what_is_read() -> None:
    """
    An ESEF filing marks up which passage is which; a 10-K does not.

    So the two passages are asked for by name rather than hunted for by
    heading, and the reading does not depend on the language the report
    was written in.
    """

    report = read()

    assert "runs two divisions" in report.business_text
    assert "Trains" in report.discussion_text
    assert "700" in report.discussion_text


def test_a_passage_interrupted_by_a_page_break_is_read_whole() -> None:
    """
    Inline XBRL lets a tagged fact stop and resume further down.

    A reader that stopped at the opening element would take the first
    paragraph of a segment note for the whole of it — and would take
    nothing at all from BNP Paribas, whose every block-tagged passage is
    empty and continued elsewhere.
    """

    business = read().business_text

    # The words and their order, not the typography the markup left
    # behind — which is the same rule the grounding check applies.
    assert "société anonyme" in business
    assert "runs two divisions" in business
    assert "The divisions are Trains and Boats." in business

    # The untagged paragraph the fact was interrupted by is not part of it.
    assert "Prose the filer tagged nothing in" not in business


def test_the_header_s_placeholders_are_not_mistaken_for_the_report() -> None:
    """
    Every tagged element's name appears in the header too.

    A search that did not drop it first would find the declaration of a
    passage rather than the passage — and the filer's own name for
    itself is declared there against a value no reader ever sees.
    """

    report = read()

    assert report.company == "Exemple Groupe"
    assert "placeholder" not in report.business_text


def test_the_document_states_who_it_belongs_to_and_what_language_it_is_in() -> None:
    """
    Neither is in the index, and both are facts a reader is owed.

    A French group may file in English, and an extraction from a
    translation is not an extraction from the original — so which one
    was read is recorded rather than inferred.
    """

    report = read()

    assert report.lei == "R0MUWSFPU8MPRO8K5P83"
    assert report.language == "fr"


def test_a_filing_that_tags_none_of_it_leaves_it_unstated() -> None:
    """
    The honest outcome. The alternative is handing the extraction some
    other part of the document and reading it as though it were this one.
    """

    report = read("<html xml:lang='en'><body><p>Nothing tagged here.</p></body></html>")

    assert report.business_text == ""
    assert report.discussion_text == ""
    assert report.lei == ""
