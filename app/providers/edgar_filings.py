"""The company's own annual report, from the regulator that receives it."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import httpx

from app.domain.prose_evidence import Region
from app.domain.tabular_evidence import SourceTable
from app.providers.document_text import (
    Flattened,
    begins_a_block,
    flatten,
    read_regions,
    read_tables,
    typesets_blocks,
)

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

#: The audited income statement is located by the title the filer
#: typeset over it, never by "Item 8": that item's heading often
#: stands over an index or a pointer while the statements themselves
#: are printed under their own names — which is the structural-section
#: rule's third application. The openings are the titles filers give
#: the statement; the closings are the titles of the statements that
#: follow it under either convention, and the notes heading that
#: follows them all. A title in the table of contents or quoted inside
#: the auditor's report does not begin a block, so the same discipline
#: that locates Items 1 and 7 separates the statement from every
#: mention of it.
_INCOME_STATEMENT = (
    "consolidated statements of income",
    "consolidated statement of income",
    "consolidated statements of operations",
    "consolidated statement of operations",
    "consolidated statements of earnings",
    "consolidated statement of earnings",
)
_INCOME_STATEMENT_ENDS = (
    "consolidated statements of comprehensive income",
    "consolidated statement of comprehensive income",
    "consolidated balance sheet",
    "consolidated statements of financial position",
    "consolidated statement of financial position",
    "consolidated statements of cash flows",
    "consolidated statement of cash flows",
    "consolidated statements of changes in",
    "consolidated statement of changes in",
    "consolidated statements of stockholders",
    "consolidated statements of shareholders",
    "notes to consolidated financial statements",
    "notes to the consolidated financial statements",
)

#: How a filer says that what a section would contain is printed
#: elsewhere in the same document, immediately before naming the place.
#:
#: English, like every other anchor in this module, because a 10-K or a
#: 20-F is filed with the SEC in English. What is deliberately *not*
#: assumed is the heading it names: that is quoted out of the filing
#: itself, so the address followed is always the filer's own words
#: rather than this platform's guess at what a section might be called.
#: Whitespace-tolerant throughout, because the prose this is read from
#: keeps the document's line breaks: a filer wraps "under the heading"
#: across two lines as readily as it prints it on one.
_REFERRED = re.compile(
    r'(?i)(?:under\s+the\s+(?:heading|caption)s?|entitled)\s*[“"]([^”"]{6,90})[”"]'
)

#: How much of a referenced section is read, in characters.
#:
#: Measured on the filing that earned this mechanism. JPMorgan's Item 1
#: names "Business Segment & Corporate Results", and that chapter runs
#: 62,774 characters from its heading to the next one the filer typeset
#: at the same size, with the three segment descriptions 8,225, 19,717
#: and 40,797 characters into it. Item 1 itself is 39,175, and the
#: sections across the calibration corpus run 28,000 to 80,000 — so this
#: is an ordinary section's width rather than a number fitted to one
#: document.
#:
#: Overshooting is the deliberately safe direction. Prose read past the
#: end of a referenced chapter cannot become a description, because a
#: span still has to be shown to belong to the segment it is cited for;
#: it costs tokens, where stopping short costs the evidence itself.
_FOLLOWED_WIDEST = 80_000


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

    #: The audited income statement, located where the filer typeset
    #: its title. Empty where no statement title begins a block in this
    #: document, which leaves the figures unstated rather than read out
    #: of whatever section mentioned them.
    income_statement_text: str = ""

    #: The tables printed under that title — the statement itself, with
    #: its structure kept.
    income_statement_tables: tuple[SourceTable, ...] = ()


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

        A section that says its content is printed elsewhere is followed.
        Measured on JPMorgan, whose Item 1 names its segments and then
        states that what they do "is provided in" the MD&A under a
        heading it quotes: reading Item 1 alone, this platform saw the
        names and no descriptions, and every reading of it honestly
        reported that the filing described nothing. It described them
        eighty pages away, in the same document, at an address the filer
        printed.
        """

        flat = flatten(document)

        business, _, regions = self._section(document, flat, _ITEM_1, _ITEM_1A)
        discussion, tables, _ = self._section(document, flat, _ITEM_7, _ITEM_7A)
        statement, statement_tables, _ = self._section(
            document, flat, _INCOME_STATEMENT, _INCOME_STATEMENT_ENDS
        )

        referenced, referred_regions, referred_tables = self._referenced(
            document, flat, business
        )

        return Filing(
            reference=reference,
            business_text=_joined(business, referenced),
            business_regions=(
                regions + _shifted(referred_regions, by=_offset(business))
            ),
            discussion_text=discussion,
            # The discussion's own tables where it prints any, and the
            # referenced chapter's where it prints none — which is the
            # pointer shape: JPMorgan's Item 7 is 395 characters naming
            # the pages its discussion appears on, and the figures are
            # in the chapter Item 1's reference already located. An
            # earlier pass declined this because the size reading could
            # not survive tables of that chapter's shape; the parse now
            # reads a spanned group header as covering its columns and a
            # page-split table as the one table it is, both measured on
            # this filing, so the decline is over on evidence rather
            # than on hope. A discussion with its own tables keeps
            # exactly those: mixing another chapter's in beside them
            # would put two tables' totals in one reading's reach.
            discussion_tables=tables or referred_tables,
            income_statement_text=statement,
            income_statement_tables=statement_tables,
        )

    @staticmethod
    def _referenced(
        document: str,
        flat: Flattened,
        within: str,
    ) -> tuple[str, tuple[Region, ...], tuple[SourceTable, ...]]:
        """
        The section this one names as the place its content is printed.

        Two conditions, and the second is the whole of the discipline.
        The filer has to *say* it is referring — "under the heading", in
        its own words — and the heading it then quotes has to occur
        exactly once in the document as something that begins a block.
        A heading two blocks carry is one the filing did not disambiguate
        and is refused rather than chosen between, which is the same rule
        `owning` applies to structural ownership and is refused for the
        same reason: where two regions could answer, none does.

        Measured on the filing that earned this: Item 1's reference to
        "Business Segment & Corporate Results" resolves to one block
        among nine occurrences, and Item 7's to "Management's discussion
        and analysis" resolves to forty-two — so the first is followed
        and the second is declined, on evidence rather than on which
        would have been more useful.
        """

        if not within:
            return ("", (), ())

        lowered = flat.text.casefold()

        for quoted in _REFERRED.findall(within):
            heading = quoted.strip().strip(",").strip()

            blocks = [
                at
                for at in _every(lowered, heading.casefold())
                if begins_a_block(document, flat, at)
            ]

            if len(blocks) != 1:
                continue

            at = blocks[0]
            ends = min(at + _FOLLOWED_WIDEST, len(flat.text))

            # The reference points out of the section that made it. One
            # that points back inside it would add nothing and would
            # double every region already read.
            if within.strip() and flat.text[at:ends].strip() in within:
                continue

            opens, closes = flat.markup_span(at, ends)

            return (
                flat.text[at:ends].strip(),
                read_regions(document, flat, at, ends),
                read_tables(document[opens:closes]),
            )

        return ("", (), ())

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
        paired with the closing that follows it.

        **A section heading begins a block; a cross-reference is part of
        a sentence.** That is what chooses between the pairs, and it is
        read from the markup the filer wrote rather than inferred from
        the words, because flattened to prose a heading and a reference
        to it are the same string. Width alone was the rule before and
        it is not a property of a section at all: Caterpillar's 10-K
        mentions Item 7 inside its forward-looking-statements note, and
        the span from that sentence to the next closing heading is
        wider than Item 7 itself — so the platform read forty-five
        thousand characters of the wrong section, containing none of
        the tables the segment sizes are measured from, and reported
        the sizes as absent from the filing.

        Among the openings that do begin a block, the widest pair still
        wins: a table-of-contents entry begins its block too, and what
        separates it from the section it points at is that it runs a few
        characters to its neighbour rather than tens of thousands.

        Where no opening begins a block, every candidate is considered
        again. A document whose markup offers no structure is read by
        width as before rather than left unread — the same order of
        preference the narrative half of this platform's evidence uses,
        structure first and position behind it.

        Nothing where no such pair exists. A section that could not be
        found leaves what it would have said unstated, which is the
        honest outcome — the alternative is returning the wrong part of
        the document and reading it as though it were the right one.
        """

        lowered = flat.text.casefold()

        pairs: list[tuple[int, int]] = []

        for start in _occurrences(lowered, opening):
            end = _first_heading(lowered, closing, after=start + 1)

            if end is not None:
                pairs.append((start, end))

        if not pairs:
            return ("", (), ())

        titled = (
            [pair for pair in pairs if begins_a_block(document, flat, pair[0])]
            if typesets_blocks(document)
            else []
        )

        widest = max(titled or pairs, key=lambda pair: pair[1] - pair[0])

        opens, closes = flat.markup_span(*widest)

        return (
            flat.text[widest[0] : widest[1]].strip(),
            read_tables(document[opens:closes]),
            read_regions(document, flat, *widest),
        )


#: What separates a section from the one it referred to, in the prose
#: the platform reads. A blank line, because that is what the two are
#: on the printed page: different parts of one document, not one
#: continuous sentence.
_BETWEEN = "\n\n"


def _joined(section: str, referenced: str) -> str:
    """A section, and what it said was printed elsewhere, as one text.

    Both, never one instead of the other. The section that referred is
    where the filer names its segments — the identity check reads it —
    and the referenced chapter is where it says what they do. Dropping
    either would trade one claim for another.
    """

    return f"{section}{_BETWEEN}{referenced}" if referenced else section


def _offset(section: str) -> int:
    """Where a referenced chapter begins in the joined text."""

    return len(section) + len(_BETWEEN) if section else 0


def _shifted(regions: tuple[Region, ...], by: int) -> tuple[Region, ...]:
    """A referenced chapter's regions, in the joined text's coordinates.

    Regions are read in the coordinates of the section they were found
    in, and structural ownership is checked against the text the reader
    is given. Carrying them across unshifted would place every heading
    at the wrong end of the document and quietly hand each segment
    another's words.
    """

    return tuple(
        Region(heading=region.heading, at=region.at + by, ends=region.ends + by)
        for region in regions
    )


def _every(text: str, needle: str) -> list[int]:
    """Every position this string appears at, in order."""

    found: list[int] = []
    at = text.find(needle)

    while at != -1:
        found.append(at)
        at = text.find(needle, at + 1)

    return found


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
