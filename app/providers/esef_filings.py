"""A European company's annual report, from the register that receives it.

Europe has no single regulator and no EDGAR. What it has is ESEF — the
European Single Electronic Format — which requires every listed issuer in
the EEA to file its annual financial report as Inline XBRL with its own
national officially appointed mechanism. XBRL International collects
those filings into one index at filings.xbrl.org, keyed by the filer's
LEI, and that index is what this reads.

The format is what makes this tractable, and it is a better document than
a 10-K in one specific way. An American filing is sectioned by convention
— `Item 1`, `Item 7` — and has to be found by looking for those words. An
ESEF filing is *tagged*: the filer marks up which passage is the
description of its operations and which is its segment note, using
elements from the IFRS taxonomy, and a national regulator validates that
it did. So the two passages this platform reads are asked for by name
rather than searched for by heading, which means the reading does not
depend on the language the report was written in.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date

import httpx

INDEX = "https://filings.xbrl.org"
ENTITY_FILINGS_URL = INDEX + "/api/entities/{lei}/filings"

#: Days a period end may sit either side of the filer's own year end and
#: still be the annual report. Retailers keep 52- and 53-week calendars,
#: so Ahold Delhaize's year has ended on 28 December, 29 December, 31
#: December, 1 January, 2 January and 3 January in six consecutive years.
#: Wide enough for that, and nowhere near the eighty-nine days that
#: separate an annual report from the nearest quarter.
ANNIVERSARY_DAYS = 14

_YEAR = 365.2425

#: Everything before the report itself: the XBRL contexts, the hidden
#: facts, the units. It repeats the names of tagged elements, so a search
#: that did not drop it first would find the declaration of a passage
#: rather than the passage. The namespace prefix is required, so that an
#: ordinary `<header>` in the report's own markup is left alone.
_HEADER = re.compile(r"(?is)<\w+:header\b.*?</\w+:header>")

_STYLE = re.compile(r"(?is)<(style|script)\b.*?</\1>")
_TAGS = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"[^\S\n]+")
_BLANK_LINES = re.compile(r"\n{3,}")

#: ESEF requires the filer to identify itself by LEI in every context, on
#: ISO 17442's scheme. It is the document saying who it belongs to, which
#: is the one claim worth checking against who it was fetched for.
_IDENTIFIER = re.compile(
    r"(?is)<(?:\w+:)?identifier[^>]*17442[^>]*>([^<]+)</(?:\w+:)?identifier>"
)

_LANGUAGE = re.compile(r'(?is)<html\b[^>]*?\b(?:xml:)?lang="([^"]+)"')

#: What the business is. The filer's own account of what it does, and the
#: note that says what its reportable segments are and how it arrived at
#: them — which is where the parts of a company are named.
BUSINESS_ELEMENTS = (
    "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities",
    "ifrs-full:DisclosureOfGeneralInformationAboutFinancialStatementsExplanatory",
    "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory",
    "ifrs-full:DisclosureOfOperatingSegmentsExplanatory",
)

#: How large each part is. IFRS 8 puts the figures in the operating
#: segment note; IFRS 15 requires revenue to be disaggregated into the
#: categories a filer actually sells in. Filers tag one, the other, or
#: both, so all of them are asked for and whatever comes back is read.
DISCUSSION_ELEMENTS = (
    "ifrs-full:DisclosureOfOperatingSegmentsExplanatory",
    "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory",
    "ifrs-full:DisclosureOfRevenueFromContractsWithCustomersExplanatory",
    "ifrs-full:DisclosureOfDisaggregationOfRevenueFromContractsWithCustomers"
    "Explanatory",
)


class EsefFilingUnavailable(Exception):
    """No ESEF annual report could be read, with the reason worded."""


class EsefRegisterError(EsefFilingUnavailable):
    """The register could not be reached. Worth asking again; a gap is not."""


@dataclass(frozen=True, slots=True)
class EsefFilingReference:
    """Which filing, precisely enough to fetch it and to keep it forever."""

    lei: str

    #: The index's own identifier, e.g.
    #: "R0MUWSFPU8MPRO8K5P83-2025-12-31-ESEF-FR-0".
    filing_id: str

    #: Where the filing was made, as an ISO country code. Europe files
    #: nationally, and which mechanism received a report is part of
    #: citing it.
    country: str

    #: The last day of the period the report accounts for.
    period_ends_on: date

    #: When the index received it. Not the same fact as the period, and
    #: the closest thing the index states to a publication date.
    added_on: date

    #: The hash of the filed package. A filing is not revised in place,
    #: and this is the bytes themselves rather than a name for them,
    #: which is what makes it safe to key permanent knowledge on.
    content_hash: str

    location: str


@dataclass(frozen=True, slots=True)
class EsefReport:
    """One annual report, and the parts of it this platform read."""

    #: The filer's own name for itself, from the document.
    company: str

    #: The LEI the document's contexts carry. Checked against the LEI the
    #: document was fetched for, because a register that served the wrong
    #: file is a failure no amount of careful reading would notice.
    lei: str

    #: The language the document declares itself to be in.
    language: str

    business_text: str

    discussion_text: str = ""


class EsefFilings:
    """
    Find and read a European issuer's annual financial report.

    Two jobs kept apart, because they cost differently. Asking which
    filing is current is one small JSON request; reading it means tens of
    megabytes of Inline XBRL. A caller that already holds knowledge from
    the current filing should only ever pay the first.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._client = client
        # A URD runs to forty megabytes before it is decompressed. Thirty
        # seconds is a timeout for an index; it is not one for a document.
        self._timeout = timeout

    # ── the index ───────────────────────────────────────────────────

    def latest_reference(
        self,
        lei: str,
        today: date | None = None,
    ) -> EsefFilingReference:
        """
        Which filing is this issuer's current annual report.

        Cheap on purpose. The filing's content hash names it exactly, so
        a caller holding knowledge already read from it can stop here.
        """

        return self._annual(self._references(lei), lei, today or date.today())

    def _references(self, lei: str) -> list[EsefFilingReference]:
        url = ENTITY_FILINGS_URL.format(lei=lei)

        try:
            payload = self._get(url).json()
        except Exception as error:
            raise EsefRegisterError(
                f"The European filing index could not be read for {lei}."
            ) from error

        data = payload.get("data") if isinstance(payload, dict) else None

        if not isinstance(data, list):
            raise EsefRegisterError(
                f"The European filing index returned no filing list for {lei}."
            )

        found: list[EsefFilingReference] = []

        for filing in data:
            if not isinstance(filing, dict):
                continue

            reference = self._reference(lei, filing.get("attributes"))

            if reference is not None:
                found.append(reference)

        return found

    @staticmethod
    def _reference(
        lei: str,
        attributes: object,
    ) -> EsefFilingReference | None:
        if not isinstance(attributes, dict):
            return None

        filing_id = str(attributes.get("fxo_id") or "")

        # The index also carries national schemes that are not ESEF — the
        # Ukrainian IFRS filings, for one. They are real documents and
        # they are not what this provider claims to read, so they are
        # left for a provider that does.
        if "-ESEF-" not in filing_id:
            return None

        location = str(attributes.get("report_url") or "")
        period = str(attributes.get("period_end") or "")
        added = str(attributes.get("date_added") or "")[:10]

        if not location or not period:
            return None

        try:
            period_ends_on = date.fromisoformat(period)
            added_on = date.fromisoformat(added)
        except ValueError:
            return None

        return EsefFilingReference(
            lei=lei,
            filing_id=filing_id,
            country=str(attributes.get("country") or ""),
            period_ends_on=period_ends_on,
            added_on=added_on,
            content_hash=str(attributes.get("sha256") or "") or filing_id,
            location=INDEX + location if location.startswith("/") else location,
        )

    @staticmethod
    def _annual(
        references: list[EsefFilingReference],
        lei: str,
        today: date,
    ) -> EsefFilingReference:
        """
        The current annual report, among everything the issuer has filed.

        Two things have to be excluded, and both were met in the index
        rather than imagined.

        A period that has not ended cannot have been reported on. The
        index carries a Hermès filing whose period is stated as ending in
        December 2026 and whose document is the report for 2025; taking
        the latest period would take that one and cite a year that has
        not happened.

        An interim report is not an annual one. Novo Nordisk files ESEF
        quarterly, so its most recent filing is usually three months of
        trading with none of the description of the business that makes a
        filing worth reading. ESEF mandates the annual report and nothing
        else, so the oldest filing on record establishes where the
        issuer's financial year ends, and the annual reports are the ones
        that land on that anniversary.
        """

        ended = [
            reference for reference in references if reference.period_ends_on <= today
        ]

        if not ended and references:
            raise EsefFilingUnavailable(
                f"Every ESEF filing indexed for {lei} accounts for a period "
                "that has not ended, so none of them was read as its annual "
                "report."
            )

        if not ended:
            raise EsefFilingUnavailable(
                f"{lei} has no ESEF filing in the European index, so no "
                "annual report was read for it. Not every national mechanism "
                "publishes to the index — Germany's does not — so this is a "
                "gap in what the index reaches rather than a company without "
                "an annual report."
            )

        year_end = min(ended, key=lambda reference: reference.period_ends_on)

        annual = [
            reference
            for reference in ended
            if _near_anniversary(reference.period_ends_on, year_end.period_ends_on)
        ]

        # Latest period first, and the mechanism's own ordering to break a
        # tie. An issuer that files the same year in two languages — BNP
        # Paribas files its registration document in French and in English
        # — leaves two filings for one period, and picking whichever the
        # index happened to list first would change the document's key
        # between two runs and re-read a filing already read. Which of the
        # two it is does not matter; that it is the same one every time
        # does. The language is recorded from whichever was chosen.
        return min(
            annual or ended,
            key=lambda reference: (
                -reference.period_ends_on.toordinal(),
                reference.filing_id,
            ),
        )

    # ── the document ────────────────────────────────────────────────

    def read_url(self, url: str) -> EsefReport:
        """The parts of the Inline XBRL report at this address."""

        filed = self._get(url).text

        # Who the document says it belongs to is declared in the header,
        # among the contexts every tagged fact points at — so it is read
        # before the header is dropped, not after.
        lei = _declared_lei(filed)
        language = _declared_language(filed)

        document = _HEADER.sub(" ", filed)

        continuations = _continuations(document)

        return EsefReport(
            company=_plain(
                _fact(
                    document,
                    "ifrs-full:NameOfReportingEntityOrOtherMeansOfIdentification",
                    continuations,
                )
                or ""
            ),
            lei=lei,
            language=language,
            business_text=_passage(document, BUSINESS_ELEMENTS, continuations),
            discussion_text=_passage(document, DISCUSSION_ELEMENTS, continuations),
        )

    # ── the wire ────────────────────────────────────────────────────

    def _get(self, url: str) -> httpx.Response:
        headers = {"Accept-Encoding": "gzip, deflate"}

        if self._client is not None:
            response = self._client.get(url, headers=headers)
        else:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers, follow_redirects=True)

        response.raise_for_status()

        return response


def _near_anniversary(period_end: date, year_end: date) -> bool:
    """Whether a period ends where this issuer's financial year ends."""

    elapsed = (period_end - year_end).days
    years = round(elapsed / _YEAR)

    return abs(elapsed - years * _YEAR) <= ANNIVERSARY_DAYS


def _continuations(document: str) -> dict[str, int]:
    """Where each `continuation` element begins, by the id it answers to.

    Inline XBRL lets one tagged fact be interrupted by untagged markup and
    resumed further down, which is how a filer tags a note that a page
    break runs through. A reader that stopped at the opening element would
    take the first paragraph of a segment note for the whole of it — and
    would take nothing at all from BNP Paribas, whose every block-tagged
    passage is empty and continued elsewhere.
    """

    return {
        match.group(2): match.start()
        for match in re.finditer(
            r'(?is)<(\w+:)?continuation\b[^>]*\bid="([^"]+)"[^>]*>',
            document,
        )
    }


def _element(document: str, start: int) -> tuple[str, int]:
    """The content of the element that opens at `start`, and where it ends.

    Depth is counted for this element's own name only, since another
    element nested inside it cannot close it. Facts do nest — a filer
    tags its legal form inside its description of its operations — so
    finding the first closing tag would truncate the outer one.
    """

    opening = re.match(r"(?is)<(\w+:)?(\w+)\b[^>]*?(/?)>", document[start:])

    if opening is None:
        return "", start

    prefix, name, empty = opening.groups()

    if empty:
        return "", start + opening.end()

    tag = re.compile(rf"(?is)<(/?)({re.escape(prefix or '')}{name})\b[^>]*?(/?)>")

    depth = 0

    for match in tag.finditer(document, start):
        closing, _, self_closing = match.groups()

        if closing:
            depth -= 1

            if depth == 0:
                return document[start + opening.end() : match.start()], match.end()
        elif not self_closing:
            depth += 1

    return document[start + opening.end() :], len(document)


def _fact(
    document: str,
    element: str,
    continuations: dict[str, int],
) -> str | None:
    """One tagged passage in full, following it through its continuations."""

    opening = re.search(
        rf'(?is)<(?:\w+:)?nonNumeric\b[^>]*\bname="{re.escape(element)}"[^>]*>',
        document,
    )

    if opening is None:
        return None

    content, _ = _element(document, opening.start())

    parts = [content]

    tag = opening.group(0)
    seen: set[str] = set()

    while True:
        resumes = re.search(r'(?i)continuedAt="([^"]+)"', tag)

        if resumes is None or resumes.group(1) in seen:
            break

        identifier = resumes.group(1)
        seen.add(identifier)

        start = continuations.get(identifier)

        if start is None:
            break

        continued, _ = _element(document, start)
        parts.append(continued)

        tag = document[start : document.find(">", start) + 1]

    return "".join(parts)


def _passage(
    document: str,
    elements: tuple[str, ...],
    continuations: dict[str, int],
) -> str:
    """
    Every one of these tagged passages the filer marked up, as plain text.

    All of them rather than the first, because the taxonomy gives a filer
    more than one place to put the same disclosure and filers differ. BNP
    Paribas tags its segment note as the operating segments; ASML tags
    the identical kind of note as its reportable segments. Asking for one
    and stopping would read one company and not the other.

    An empty string where the filer tagged none of them. A passage that
    is not there leaves what it would have said unstated, which is the
    honest outcome — the alternative is handing the extraction some other
    part of the document and reading it as though it were this one.
    """

    found = []

    for element in elements:
        content = _fact(document, element, continuations)

        if content is None:
            continue

        text = _plain(content)

        if text and text not in found:
            found.append(text)

    return "\n\n".join(found)


def _plain(fragment: str) -> str:
    """Markup reduced to the words a reader would see."""

    text = _STYLE.sub(" ", fragment)
    text = html.unescape(_TAGS.sub(" ", text))
    text = _WHITESPACE.sub(" ", text)

    return _BLANK_LINES.sub("\n\n", text).strip()


def _declared_lei(document: str) -> str:
    """The LEI the document's own contexts carry, or an empty string."""

    stated = _IDENTIFIER.search(document)

    return stated.group(1).strip() if stated else ""


def _declared_language(document: str) -> str:
    """The language the document declares, or an empty string.

    Read from the document rather than assumed from where it was filed. A
    French issuer may file in English, and an extraction from a
    translation is not an extraction from the original — so which one was
    read is recorded rather than inferred.
    """

    stated = _LANGUAGE.search(document[:4096])

    return stated.group(1).strip().casefold() if stated else ""
