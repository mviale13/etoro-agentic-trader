"""The company's own annual report, from the regulator that receives it."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date

import httpx

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
_ITEM_1A = ("item 1a.", "item 1a ", "item 2.", "item 2 ")

_TAGS = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")


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


@dataclass(frozen=True, slots=True)
class Filing:
    """One annual report, and the part of it this platform read."""

    reference: FilingReference

    #: The business description as plain text — the section a reader
    #: would turn to for what the company actually does.
    business_text: str


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

    def latest_annual_report(self, symbol: str) -> Filing:
        """The most recent 10-K or 20-F this company filed."""

        ticker = symbol.upper().strip()

        cik = self._cik(ticker)

        reference, document = self._latest_filing(cik, ticker)

        return Filing(
            reference=reference,
            business_text=self._business_section(document),
        )

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

    def _latest_filing(
        self,
        cik: int,
        ticker: str,
    ) -> tuple[FilingReference, str]:
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

            reference = FilingReference(
                company=str(submissions.get("name", ticker)),
                form=form,
                filed_on=date.fromisoformat(str(recent["filingDate"][index])),
                accession=accession,
                url=url,
            )

            return reference, self._get(url).text

        raise FilingUnavailable(
            f"{ticker} is listed with the SEC but has filed no annual "
            "report this platform could find."
        )

    # ── the document ────────────────────────────────────────────────

    @staticmethod
    def _business_section(document: str) -> str:
        """
        The business description, as plain text.

        An annual report is megabytes of markup, most of it financial
        statements. What describes the business — its segments, what each
        one sells, how it earns — is Item 1, and taking that alone is what
        makes the document small enough to read carefully.

        The heading appears at least twice: once in the table of contents
        and once over the section itself. Taking the first occurrence
        returns the contents line and nothing else, so every Item 1 is
        paired with the Item 1A that follows it and the widest pair wins.
        A contents entry is a few characters from its neighbour; the real
        section is tens of thousands.

        Where no such pair can be found the whole document is returned. A
        truncated read is worse than a large one: it would silently drop
        the segments this exists to find.
        """

        text = html.unescape(_TAGS.sub(" ", document))
        text = _WHITESPACE.sub(" ", text)
        text = _BLANK_LINES.sub("\n\n", text)

        lowered = text.casefold()

        widest: tuple[int, int] | None = None

        for start in _occurrences(lowered, ("item 1.", "item 1 ", "item 1:")):
            end = _first_heading(lowered, _ITEM_1A, after=start + 1)

            if end is None:
                continue

            if widest is None or end - start > widest[1] - widest[0]:
                widest = (start, end)

        if widest is None:
            return text.strip()

        return text[widest[0] : widest[1]].strip()


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
