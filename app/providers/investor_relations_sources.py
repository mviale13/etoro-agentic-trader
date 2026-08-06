"""Where a company publishes its own annual report, reviewed by hand.

The second curated trust boundary in this platform, and it exists for the
same reason as the first: no authority answers the question. GLEIF will
say which legal entity issued a security; nobody will say which website
belongs to that entity. So a document location is not discovered, it is
*reviewed* — and the difference between those two verbs is the whole
point of this file.

A crawler answers "I found something at this address that looks like an
annual report". A reviewed entry answers "a person checked that this
company publishes this document here". Only the second is a claim about
identity, and identity is what the platform refuses to guess at.

Each entry therefore carries the hash of the bytes that were reviewed.
That does three things at once:

- `resolve` becomes free. There is no register to ask, and no download
  is needed to know the document's key, so a company whose report has
  already been read costs nothing at all.
- A document that changes underneath us stops rather than slides. An
  issuer can replace a file at the same address, and a hash mismatch is
  reported as a document awaiting review — never read as though the
  review had covered it.
- The key is honest. It is the bytes themselves, so knowledge kept under
  it can never describe different bytes.

The cost is deliberate and is not hidden: an entry goes stale every year,
when the company publishes its next report. The platform then keeps
serving the reviewed document and *states the period it covers*, so a
reader sees a year-old report described as a year-old report. Silently
following a moving URL would be the alternative, and that trades a
visible staleness for an invisible one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class PublishedReport:
    """One document a company publishes about itself, as reviewed."""

    #: The symbol as this platform names the security. The issuer behind
    #: it is not recorded here — `IssuerIdentityRegistry` establishes
    #: that, and one business concept keeps one implementation.
    symbol: str

    #: Where the bytes were retrieved from when the entry was reviewed.
    location: str

    #: Every host the retrieval may touch, including redirects. Kept
    #: apart from the location because they genuinely differ: Volkswagen
    #: lists its reports on `volkswagen-group.com` and serves the files
    #: from `uploads.vw-mms.de`, so a reviewer has to approve the host
    #: the bytes actually come from rather than the one that linked them.
    approved_hosts: tuple[str, ...]

    #: SHA-256 of the reviewed bytes. Any other bytes at this location
    #: are a different document, and a different document has not been
    #: reviewed.
    content_hash: str

    #: The last day of the period the reviewed document accounts for.
    #: Checked against the document's own XBRL contexts on every fetch,
    #: so a reviewer's typo cannot quietly re-date a report.
    period_ends_on: date

    #: The date the publisher states it published the document. Reviewed
    #: rather than verified: unlike a regulator's receipt, there is no
    #: record of it anywhere but the publisher's own page.
    published_on: date

    #: The publisher's own filename, which is the closest thing an
    #: unfiled document has to an identifier.
    identifier: str

    def serves(self, url: str) -> bool:
        """Whether these bytes came from somewhere this entry approves."""

        host = (urlparse(url).hostname or "").casefold()

        return any(host == approved.casefold() for approved in self.approved_hosts)


#: Reviewed 2026-08-06.
#:
#: Volkswagen is the first entry because it is the gap ESEF cannot close:
#: Germany's officially appointed mechanism does not publish to
#: filings.xbrl.org, so a German issuer resolves to a real company and to
#: no filing. Volkswagen publishes the ESEF package it filed — the same
#: regulated artefact, from the issuer instead of from a register — which
#: is why this entry can be read at all. An issuer that publishes only a
#: PDF cannot identify its own issuer in machine-readable form and is
#: left honestly unavailable rather than read on weaker evidence.
_REPORTS: tuple[PublishedReport, ...] = (
    PublishedReport(
        symbol="VOW3.DE",
        location=(
            "https://uploads.vw-mms.de/system/production/files/cws/041/941/file/"
            "00d8d2096bb900de99e1115b0bb6a000f60579c0/"
            "VWAG_JFB_Konzern-2025-12-31-DE.zip"
        ),
        approved_hosts=("uploads.vw-mms.de",),
        content_hash=(
            "c14269a137c3fd41d6909ec889535b41dc1ea7480ac640105c59f59f6544c17a"
        ),
        period_ends_on=date(2025, 12, 31),
        published_on=date(2026, 3, 10),
        identifier="VWAG_JFB_Konzern-2025-12-31-DE.zip",
    ),
)


PUBLISHED_REPORTS: Mapping[str, PublishedReport] = {
    report.symbol: report for report in _REPORTS
}
