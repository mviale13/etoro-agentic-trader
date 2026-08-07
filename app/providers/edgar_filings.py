"""The company's own annual report, from the regulator that receives it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx

from app.domain.prose_evidence import Region
from app.domain.tabular_evidence import SourceTable
from app.providers.document_text import Flattened, flatten, read_regions, read_tables

#: SEC's fair-access policy requires a request to identify who is making
#: it. A platform that scraped anonymously would be asking a public
#: regulator to serve it without saying who it is.
USER_AGENT = "MOVRvest research (contact: mviale@gmail.com)"

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"

#: The annual report, under whichever form the filer uses. A foreign
#: private issuer files 20-F and a domestic one 10-K; both carry the
#: business description this platform reads.
ANNUAL_FORMS = ("10-K", "20-F")

#: Where Item 1 ends: the risk factors that follow it, or Item 2 where a
#: filer omits them.
#: A section ends at the next item's heading — or, where the filer does
#: not repeat that heading in the body, at the title of the section that
#: follows it. Disney's latest 10-K prints "ITEM 7A" only in its table of
#: contents, so a search for the heading alone found the contents entry
#: and read ninety-seven characters as the whole discussion.
#:
#: A title used as an anchor has to be long enough to be unambiguous. A
#: short one appears inside the section it is meant to close: "risk
#: factors" is written a dozen times inside Item 1 as a cross-reference,
#: and anchoring on it truncated the business description mid-way. The
#: extractor's grounding check is what caught that — a segment it had
#: read from the filing was suddenly not in the text it was given.
_ITEM_1 = ("item 1.", "item 1 ", "item 1:")
_ITEM_1A = ("item 1a.", "item 1a ", "item 2.", "item 2 ")

#: Item 7 is Management's Discussion and Analysis, which is where a filer
#: states what each segment actually earned. Item 1 describes the
#: segments and reports no figures for them.
_ITEM_7 = ("item 7.", "item 7 ", "item 7:")
_ITEM_7A = (
    "item 7a.",
    "item 7a ",
    "item 8.",
    "item 8 ",
    "quantitative and qualitative disclosures about market risk",
    "report of independent registered public accounting firm",
)


class FilingUnavailable(Exception):
    """No annual report could be read, with the reason worded.

    A company this platform cannot read a filing for is a company it
    knows structurally nothing about, which is a fact about the platform
    and is reported as one. It is never a reason to invent a description.
    """


@dataclass(frozen=True, slots=True)
class FilingReference:
    """Which document a fact was read from, precisely enough to check."""

    #: The filer's own name on the filing.
    company: str

    #: "10-K" or "20-F".
    form: str

    #: When the regulator received it.
    filed_on: date

    #: The regulator's own identifier for this filing. A filing is never
    #: revised in place, so this doubles as a cache key that can never go
    #: stale: the same accession is the same document forever.
    accession: str

    url: str

    #: The last day of the period this filing accounts for, as the index
    #: states it. None where the index states none — a filing date minus
    #: a year is not a reporting period.
    period_ends_on: date | None = None


@dataclass(frozen=True, slots=True)
class Filing:
    """One annual report, and the parts of it this platform read."""

    reference: FilingReference

    #: The business description as plain text — the section a reader
    #: would turn to for what the company actually does.
    business_text: str

    #: The regions that section's own headings introduce, in the
    #: coordinates of `business_text`. What lets a description be owned
    #: by the part of the document it was printed in rather than by
    #: whichever segment the prose happened to name last. Empty where the
    #: filer typeset no headings this platform could find, which leaves
    #: ownership to the positional mechanism rather than to nothing.
    business_regions: tuple[Region, ...] = ()

    #: Management's discussion, where the filer states what each segment
    #: earned. Empty where the section could not be found, which leaves
    #: the segments described and their sizes unstated rather than
    #: apportioned.
    discussion_text: str = ""

    #: The tables printed inside that discussion, with their rows and
    #: columns kept. `discussion_text` contains the same figures with the
    #: structure flattened out of them, which is enough to read a
    #: sentence and not enough to prove which row a number sits on.
    discussion_tables: tuple[SourceTable, ...] = ()


class EdgarFilings:
    """
    Fetch a company's latest annual report from SEC EDGAR.

    EDGAR is the authoritative source for what a company says about
    itself: the filer wrote it, the regulator received it on a dated
    record, and it cannot be revised without a new filing.

    It covers filers registered with the SEC — every US issuer and the
    foreign ones listed there. A company listed only in Europe files with
    its own national regulator and is not here, and this raises rather
    than substituting a lesser source.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = client
        self._timeout = timeout

    def latest_reference(self, symbol: str) -> FilingReference:
        """
        Which filing is this company's latest word, without reading it.

        Cheap on purpose, and separate from reading the document. The
        accession names the filing exactly, so a caller holding knowledge
        already read from it can stop here — the expensive parts, the
        megabytes of markup and the model call over them, are only worth
        paying once per filing.
        """

        ticker = symbol.upper().strip()

        return self._latest_reference(self._cik(ticker), ticker)

    def read(self, reference: FilingReference) -> Filing:
        """The sections of one filing this platform reads."""

        return self._read(reference, self._get(reference.url).text)

    def read_url(self, url: str) -> Filing:
        """
        The sections of the filing at this address.

        For a caller holding a canonical primary source rather than an
        EDGAR reference: everything needed to read the document is in its
        location, and the identity travels on the source itself.
        """

        return self._read(
            FilingReference(
                company="",
                form="",
                filed_on=date.min,
                accession="",
                url=url,
            ),
            self._get(url).text,
        )

    def _read(self, reference: FilingReference, document: str) -> Filing:
        """
        The two sections this platform reads, and the discussion's tables.

        The document is flattened once and both sections are located in
        that one reduction, which is also what maps each section back to
        the markup it came from. The prose is read from the reduction and
        the tables from the markup underneath it, so the same section
        yields both without being parsed twice or differently.
        """

        flat = flatten(document)

        business, _, regions = self._section(document, flat, _ITEM_1, _ITEM_1A)
        discussion, tables, _ = self._section(document, flat, _ITEM_7, _ITEM_7A)

        return Filing(
            reference=reference,
            business_text=business,
            business_regions=regions,
            discussion_text=discussion,
            discussion_tables=tables,
        )

    def latest_annual_report(self, symbol: str) -> Filing:
        """The most recent 10-K or 20-F this company filed, read in full."""

        return self.read(self.latest_reference(symbol))

    # ── the wire ────────────────────────────────────────────────────

    def _get(self, url: str) -> httpx.Response:
        headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}

        if self._client is not None:
            response = self._client.get(url, headers=headers)
        else:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers, follow_redirects=True)

        response.raise_for_status()

        return response

    def _cik(self, ticker: str) -> int:
        """
        The regulator's own number for this ticker.

        A ticker EDGAR does not list is not a company this platform can
        read a filing for, and says so rather than guessing at a number.
        """

        try:
            listed = self._get(TICKERS_URL).json()
        except Exception as error:
            raise FilingUnavailable(
                "The SEC's company list could not be read, so no filing was looked for."
            ) from error

        for entry in listed.values():
            if str(entry.get("ticker", "")).upper() == ticker:
                return int(entry["cik_str"])

        raise FilingUnavailable(
            f"{ticker} is not listed with the SEC, so no annual report was "
            "read for it. Companies listed only outside the United States "
            "file with their own regulator, which this platform does not "
            "yet read."
        )

    def _latest_reference(
        self,
        cik: int,
        ticker: str,
    ) -> FilingReference:
        try:
            submissions = self._get(SUBMISSIONS_URL.format(cik=cik)).json()
        except Exception as error:
            raise FilingUnavailable(
                f"The SEC filing index for {ticker} could not be read."
            ) from error

        recent = submissions.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])

        for index, form in enumerate(forms):
            if form not in ANNUAL_FORMS:
                continue

            accession = str(recent["accessionNumber"][index])
            document = str(recent["primaryDocument"][index])

            url = ARCHIVE_URL.format(
                cik=cik,
                accession=accession.replace("-", ""),
                document=document,
            )

            reported = str(recent.get("reportDate", [])[index] or "")

            return FilingReference(
                company=str(submissions.get("name", ticker)),
                form=form,
                filed_on=date.fromisoformat(str(recent["filingDate"][index])),
                accession=accession,
                url=url,
                period_ends_on=date.fromisoformat(reported) if reported else None,
            )

        raise FilingUnavailable(
            f"{ticker} is listed with the SEC but has filed no annual "
            "report this platform could find."
        )

    # ── the document ────────────────────────────────────────────────

    @staticmethod
    def _section(
        document: str,
        flat: Flattened,
        opening: tuple[str, ...],
        closing: tuple[str, ...],
    ) -> tuple[str, tuple[SourceTable, ...], tuple[Region, ...]]:
        """
        One numbered item, as plain text, as its tables and as its structure.

        An annual report is megabytes of markup. The two sections this
        platform reads — what the business is, and what each part of it
        earned — are a small fraction of it, and taking them alone is
        what makes the document small enough to read carefully.

        Every heading appears at least twice: once in the table of
        contents and once over the section itself. So every opening is
        paired with the closing that follows it and the widest pair wins.
        A contents entry sits a few characters from its neighbour; the
        real section runs to tens of thousands.

        Nothing where no such pair exists. A section that could not be
        found leaves what it would have said unstated, which is the
        honest outcome — the alternative is returning the wrong part of
        the document and reading it as though it were the right one.
        """

        lowered = flat.text.casefold()

        widest: tuple[int, int] | None = None

        for start in _occurrences(lowered, opening):
            end = _first_heading(lowered, closing, after=start + 1)

            if end is None:
                continue

            if widest is None or end - start > widest[1] - widest[0]:
                widest = (start, end)

        if widest is None:
            return ("", (), ())

        opens, closes = flat.markup_span(*widest)

        return (
            flat.text[widest[0] : widest[1]].strip(),
            read_tables(document[opens:closes]),
            read_regions(document, flat, *widest),
        )


def _occurrences(text: str, headings: tuple[str, ...]) -> list[int]:
    """Every position any of these headings appears at, in order."""

    found: list[int] = []

    for heading in headings:
        position = text.find(heading)

        while position != -1:
            found.append(position)
            position = text.find(heading, position + 1)

    return sorted(found)


def _first_heading(
    text: str,
    headings: tuple[str, ...],
    after: int = 0,
) -> int | None:
    """Where one of these headings first appears past a point."""

    found = [
        position
        for position in (text.find(heading, after) for heading in headings)
        if position != -1
    ]

    return min(found) if found else None
