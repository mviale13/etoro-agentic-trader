"""CoinGecko's per-asset development timeline, and what it costs to use it.

The ruling named this surface as the acceptance case, and §5 asked for
its terms before anything was built on it. They were measured on
2026-08-10 and they are these:

```text
API accessible?    NO. /api/v3/news is 401 — "limited to PRO API
                   subscribers". /coins/{id}/status_updates is 404, the
                   endpoint no longer exists. There is no free JSON
                   surface carrying this content.
Web accessible?    YES, keyless: /en/coins/{id}/insights returns a ~20KB
                   server-rendered fragment, and /insights/{id} returns
                   the per-source breakdown.
Freshness          minute-resolution ISO timestamps, newest ~30 minutes
                   old at the time of measurement.
Per asset?         YES — the asset is the URL. Eight of eight corpus
                   assets returned eight entries each.
Coverage           BTC, ETH and HYPE all covered richly.
Source links?      YES — each entry names its sources, and the detail
                   page carries each source's own text and its URL.
Generated from?    identifiable news and on-chain reports, cited.
Cost               free, no key, no attribution requirement found.
```

**So it is web-only, and §5 says to report that before scraping it.**
Reported here, and the shape of the risk stated plainly: this is not a
published interface, nothing obliges CoinGecko to keep it, and a page
change breaks it. Two things make it worth taking anyway. The parse
reads **`data-` attributes and two component classes** — the machine
scaffolding — rather than visual layout or text position, so it fails
loudly rather than silently mis-reading. And when it does break, it
reports `EventFeedHealth` instead of an empty brief: **a surface that
returns nothing and a surface that returns nothing *because it changed*
must not look the same**, which is a lesson this platform has already
paid for once in section location.

Nothing acquired here is ever more than **attributed**. It is a vendor's
editorial summary over other people's reporting — one step further from
the event than the press it summarises — and the whole point of §2 is
that its sentences decompose rather than land whole.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

import requests

from app.domain.crypto_event import (
    CryptoEvent,
    EventFamily,
    EventFeedHealth,
    EventStatus,
    SourceReport,
    SourceTier,
    decompose,
    identity_of,
)

TIMEOUT = 25

HEADERS = {
    "User-Agent": "movrvest/1.0",
    "Accept": "text/html,application/xhtml+xml",
}

#: The provider's own identifier for each asset. The same map the facts
#: provider verified by hand in S1, repeated rather than imported: this
#: module must not depend on the facts stack, and eight entries is not a
#: duplication worth a coupling.
INSIGHT_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "ARB": "arbitrum",
    "1INCH": "1inch",
    "HYPE": "hyperliquid",
    "TAO": "bittensor",
}


# ── the family rules ────────────────────────────────────────────────


#: Headlines that are the price saying what the price did.
#:
#: **Price commentary is not an event**, and declining it is the single
#: most valuable rule in this module. Eight of the sixty-four entries
#: measured were of this shape — *"Price Holds Key $1,900 Support"*,
#: *"Breaks Two-Month Price Barrier"* — and every one of them is a worse
#: reading of something this platform already measures itself, with
#: S4's interval-safe arithmetic and a named comparator. Admitting them
#: would double-count one move as both market behaviour and a
#: development, and would turn the brief into the news list the ruling
#: forbids.
_PRICE_COMMENTARY = (
    "price holds",
    "price recovers",
    "price jump",
    "highest price",
    "price barrier",
    "price target",
    "price prediction",
    "price analysis",
    "double-digit gains",
    "weekly gains",
    "support level",
    "resistance",
    "reaches $",
    "breaks $",
    "climbs to $",
    "falls to $",
    "trading at",
    "price slip",
    "rally",
    "pullback",
    "consolidat",
    "price surge",
)

#: Families decided by any mention, headline or body. These three are
#: decisive because their vocabulary is not shared: nothing else is an
#: exploit, and a regulator's action is a regulator's action wherever
#: the sentence puts it.
_DECISIVE: tuple[tuple[EventFamily, tuple[str, ...]], ...] = (
    (
        EventFamily.SECURITY,
        (
            "exploit",
            "hack",
            "drain",
            "breach",
            "stolen",
            "steal",
            "vulnerab",
            "compromis",
            "phishing",
            "attack",
            "rug pull",
            "malicious",
            "scam",
        ),
    ),
    (
        EventFamily.REGULATORY,
        (
            "regulat",
            "cftc",
            "court",
            "lawsuit",
            "ruling",
            "approval",
            "approves",
            "licens",
            "registration",
            "banned",
            "sanction",
            "austrac",
            "mica",
            "subpoena",
            "enforcement",
            "watchdog",
            "judge",
            "complianc",
            "suspends",
        ),
    ),
    (
        EventFamily.PROTOCOL_UPGRADE,
        (
            "upgrade",
            "hard fork",
            "hardfork",
            "mainnet",
            "testnet",
            "eip-",
            "bip-",
            "hip-",
            "consensus change",
            "client release",
            "protocol update",
        ),
    ),
)

#: Everything else, decided on the **headline** first.
#:
#: The headline names the event and the body elaborates it, so a body
#: keyword decides badly: *"Ethereum Sees Record Staked Supply"* has
#: "inflow" in its body and is not a fund flow. Ordering is by how
#: specific the vocabulary is, and `supply` appears only in its
#: compounds for the same reason — bare, it captured staking.
_BY_HEADLINE: tuple[tuple[EventFamily, tuple[str, ...]], ...] = (
    (EventFamily.CAPITAL_FLOW, ("etf", "inflow", "outflow", "fund flow")),
    (
        EventFamily.INSTITUTIONAL_ADOPTION,
        (
            "holdings",
            "treasury",
            "allocat",
            "public compan",
            "corporate",
            "acquires",
            "acquired",
            "buys",
            "bought",
            "sells",
            "sold",
            "purchase",
            "reserve",
            "stake in",
        ),
    ),
    (
        EventFamily.TOKENOMICS,
        (
            "burn",
            "unlock",
            "vesting",
            "emission",
            "halving",
            "issuance",
            "mint",
            "destroy",
            "supply cap",
            "max supply",
            "token supply",
            "circulating supply",
            "token release",
            "buyback",
        ),
    ),
    (
        EventFamily.ECOSYSTEM_ADOPTION,
        (
            "integrat",
            "partnership",
            "launch",
            "deploy",
            "rwa",
            "real world asset",
            "nft",
            "dapp",
            "built on",
            "ecosystem",
            "registers",
            "tokenized",
            "bridge",
            "stablecoin",
            "propos",
        ),
    ),
    (
        EventFamily.NETWORK_OPERATION,
        (
            "difficulty",
            "hashrate",
            "hash rate",
            "staked",
            "staking",
            "validator",
            "active address",
            "on-chain",
            "onchain",
            "tvl",
            "revenue",
            "fees",
            "miner",
            "mining",
            "deposits",
            "throughput",
            "network growth",
            "transactions",
        ),
    ),
    (
        EventFamily.MARKET_STRUCTURE,
        (
            "futures",
            "open interest",
            "listing",
            "listed",
            "exchange",
            "whale",
            "liquidat",
            "perp",
            "positioning",
            "custody",
            "withdrew",
            "withdraw",
            "transfer",
            "volume",
            "traders",
            "liquidity",
            "net-long",
            "net-short",
            "dormant",
            "exits",
            "outnumber",
        ),
    ),
)


def family_of(headline: str, body: str) -> EventFamily | None:
    """Which development this is, or None where the words do not say.

    None is a real answer and is acted on: an entry this platform cannot
    place is declined with its reason rather than filed under a family
    that happens to sort last. Three of sixty-four entries landed here
    in the measurement — a corporate resignation, a stablecoin ranking,
    a founder's clarification — and none of them is worth a tenth
    family.
    """

    head = headline.lower()
    both = f"{headline} {body}".lower()

    for family, keys in _DECISIVE:
        if any(key in both for key in keys):
            return family

    if any(key in head for key in _PRICE_COMMENTARY):
        return None

    for family, keys in _BY_HEADLINE:
        if any(key in head for key in keys):
            return family

    for family, keys in _BY_HEADLINE:
        if any(key in both for key in keys):
            return family

    return None


def is_price_commentary(headline: str, body: str) -> bool:
    """Whether the entry is the price restated as news."""

    both = f"{headline} {body}".lower()

    if any(key in both for family, keys in _DECISIVE for key in keys):
        return False

    return any(key in headline.lower() for key in _PRICE_COMMENTARY)


# ── the parse ───────────────────────────────────────────────────────


_WRAPPER = 'class="gecko-timeline-entry-wrapper"'
_SECTION_DATE = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"')
_ENTRY_ID = re.compile(r'data-insight-source-id="(\d+)"')
_ENTRY_URL = re.compile(r'data-url="([^"]+)"')
_REL_TIME = re.compile(r'data-rel-time="([^"]+)"')
_SPAN = re.compile(r"<span[^>]*>(.*?)</span>", re.S)
_TOOLTIP = re.compile(r'data-tooltip="([^"]+)"')
_SOURCE_COUNT = re.compile(r"(\d+)\s+sources?")
_TAGS = re.compile(r"<[^>]+>")

#: The detail page's per-source block: the outbound link, the source's
#: name, and the source's own paragraph.
_OUTBOUND = re.compile(r'<a[^>]+href="(https?://(?!www\.coingecko\.com)[^"]+)"')
_SOURCE_NAME = re.compile(
    r'class="[^"]*tw-font-semibold tw-text-sm[^"]*"[^>]*>(.*?)</div>', re.S
)
_SOURCE_TEXT = re.compile(
    r'class="[^"]*tw-font-normal[^"]*tw-text-sm[^"]*"[^>]*>(.*?)</div>', re.S
)


def _flatten(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAGS.sub("", raw))).strip()


@dataclass(frozen=True, slots=True)
class InsightEntry:
    """One timeline entry, exactly as the surface rendered it."""

    insight_id: str
    url: str | None
    headline: str
    body: str
    at: datetime | None
    source_names: tuple[str, ...]
    source_count: int


class CoinInsightProvider:
    """One asset's development timeline, from CoinGecko's own page."""

    SOURCE = "CoinGecko Insights"

    BASE = "https://www.coingecko.com/en/coins"

    def __init__(self, detail_budget: int = 3) -> None:
        #: How many entries per asset to open for their per-source
        #: breakdown. The list page carries the summary and the source
        #: names; only the detail page carries each source's own words
        #: and its link. Budgeted because it is one request each, and
        #: the events that earn it are the ones several sources carry.
        self._detail_budget = detail_budget

    def events(
        self,
        symbol: str,
        now: datetime | None = None,
    ) -> tuple[tuple[CryptoEvent, ...], EventFeedHealth]:
        """This asset's timeline as canonical events, and the parse health."""

        normalized = symbol.upper().strip()
        coin = INSIGHT_IDS.get(normalized)

        if coin is None:
            return (), EventFeedHealth(
                source=self.SOURCE,
                reached=False,
                because=f"{normalized} is not mapped to a page on this surface",
            )

        try:
            page = self._fetch(f"{self.BASE}/{coin}/insights")
        except Exception as exc:  # noqa: BLE001
            return (), EventFeedHealth(
                source=self.SOURCE,
                reached=False,
                because=f"{type(exc).__name__} reading the timeline",
            )

        entries, seen = self._parse(page, now)

        opened = self._open_details(entries)

        events: list[CryptoEvent] = []
        declined: list[str] = []

        for entry in entries:
            event = self._event(normalized, entry, opened.get(entry.insight_id, ()))

            if event is None:
                declined.append(entry.headline)
                continue

            events.append(event)

        return tuple(events), EventFeedHealth(
            source=self.SOURCE,
            reached=True,
            entries_seen=seen,
            entries_parsed=len(events),
            declined=tuple(declined),
        )

    def _open_details(
        self,
        entries: list[InsightEntry],
    ) -> dict[str, tuple[SourceReport, ...]]:
        """Open the multi-source entries for their per-source breakdown.

        The list page says *"3 sources"* and names them; only the detail
        page carries what each one actually wrote and where to read it.
        That costs a request each, so it is spent where it buys most —
        on the events more than one source carried, which are also the
        events the dedup rule most needs provenance for.
        """

        wanted = sorted(
            (entry for entry in entries if entry.source_count > 1 and entry.url),
            key=lambda entry: entry.source_count,
            reverse=True,
        )[: self._detail_budget]

        return {
            entry.insight_id: self.detail(entry.url)
            for entry in wanted
            if entry.url is not None
        }

    # ── html → entries ──────────────────────────────────────────────

    def _parse(
        self,
        page: str,
        now: datetime | None,
    ) -> tuple[list[InsightEntry], int]:
        """Read the fragment's own scaffolding, never its layout.

        The date is the trap. Entries under *Today* carry an absolute
        `data-rel-time`; entries under *Yesterday* carry none at all and
        inherit the section's `data-date`. A parse that read only the
        per-entry attribute would leave those undated — and undated is
        never current, so a whole day of events would drop out of the
        brief while the page looked fine.
        """

        entries: list[InsightEntry] = []

        chunks = page.split(_WRAPPER)

        seen = len(chunks) - 1

        section = _SECTION_DATE.search(page)

        fallback = _at_start_of(section.group(1)) if section else None

        for chunk in chunks[1:]:
            entry = self._entry(chunk, fallback)

            if entry is not None:
                entries.append(entry)

            later = _SECTION_DATE.search(chunk)

            if later:
                fallback = _at_start_of(later.group(1))

        return entries, seen

    @staticmethod
    def _entry(chunk: str, fallback: datetime | None) -> InsightEntry | None:
        identifier = _ENTRY_ID.search(chunk)

        if identifier is None:
            return None

        spans = [
            re.sub(r"\s+", " ", html.unescape(_TAGS.sub("", raw))).strip()
            for raw in _SPAN.findall(chunk)
        ]

        text = [span for span in spans if len(span) > 10]

        if not text:
            return None

        headline = text[0].rstrip(": ").strip()
        body = text[1] if len(text) > 1 else ""

        stamp = _REL_TIME.search(chunk)

        when = _parse_time(stamp.group(1)) if stamp else fallback

        count = _SOURCE_COUNT.search(chunk)

        # The tooltip carries each source's name; the source-count text
        # is the surface's own tally and is trusted over the tooltips,
        # which render only the icons that fit.
        names = tuple(
            dict.fromkeys(
                name
                for name in _TOOLTIP.findall(chunk)
                if name and not name.lower().startswith("http")
            )
        )

        url = _ENTRY_URL.search(chunk)

        return InsightEntry(
            insight_id=identifier.group(1),
            url=html.unescape(url.group(1)) if url else None,
            headline=headline,
            body=body,
            at=when,
            source_names=names,
            source_count=int(count.group(1)) if count else len(names),
        )

    # ── entries → events ────────────────────────────────────────────

    def _event(
        self,
        symbol: str,
        entry: InsightEntry,
        opened: tuple[SourceReport, ...],
    ) -> CryptoEvent | None:
        family = family_of(entry.headline, entry.body)

        if family is None:
            return None

        text = f"{entry.headline}. {entry.body}".strip()

        # The body only: the headline is this vendor's framing of the
        # event and is already carried as the event's name.
        facts, readings = decompose(entry.body, self.SOURCE)

        # The summary itself, attributed to the vendor that wrote it.
        reports = [
            SourceReport(
                source=self.SOURCE,
                tier=SourceTier.AGGREGATOR,
                text=text,
                url=entry.url,
                published_at=entry.at,
            )
        ]

        # The accounts it was written over. Where the detail page was
        # opened, each carries that source's own words and its link;
        # otherwise the timeline's names alone, which still tell a
        # reader who is behind the summary. §9's "retain all useful
        # source provenance beneath one event".
        if opened:
            reports.extend(opened)
        else:
            reports.extend(
                SourceReport(
                    source=name,
                    tier=SourceTier.SECONDARY,
                    text="",
                    published_at=entry.at,
                )
                for name in entry.source_names
                if name != self.SOURCE
            )

        # Each source's own sentences decompose too, so a fact stated by
        # a named outlet is not filed as the aggregator's.
        for report in opened:
            if not report.text:
                continue

            more_facts, more_readings = decompose(report.text, report.source)

            facts = facts + more_facts
            readings = readings + more_readings

        return CryptoEvent(
            identity=identity_of((symbol,), family, entry.headline, entry.at),
            symbols=(symbol,),
            family=family,
            headline=entry.headline,
            occurred_at=entry.at,
            published_at=entry.at,
            observed_at=datetime.now(UTC),
            reports=tuple(reports),
            facts=facts,
            interpretations=readings,
            status=(
                EventStatus.UNRESOLVED
                if any(item.is_causal for item in readings)
                else EventStatus.COMPLETED
            ),
        )

    def detail(self, url: str) -> tuple[SourceReport, ...]:
        """Each source's own account of one event, from its detail page.

        The list page says *"2 sources"*; this says which two, what each
        one wrote, and where to read it. That is the difference between
        an event with provenance and an event with a number beside it.

        Each source is one `gecko-timeline-entry-wrapper` carrying an
        outbound `href`, a name and a paragraph — so the wrapper is what
        is split on, and a source's link is read from its own block
        rather than by pairing two lists by position, which would
        mis-attribute every account after the first missing one.
        """

        try:
            page = self._fetch(url)
        except Exception:  # noqa: BLE001
            return ()

        reports: list[SourceReport] = []

        for chunk in page.split(_WRAPPER)[1:]:
            link = _OUTBOUND.search(chunk)

            name = _SOURCE_NAME.search(chunk)

            body = _SOURCE_TEXT.search(chunk)

            if name is None:
                continue

            reports.append(
                SourceReport(
                    source=_flatten(name.group(1)),
                    tier=SourceTier.SECONDARY,
                    text=_flatten(body.group(1)) if body else "",
                    url=html.unescape(link.group(1)) if link else None,
                )
            )

        return tuple(reports)

    @staticmethod
    def _fetch(url: str) -> str:
        response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)

        response.raise_for_status()

        return response.text


def _parse_time(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _at_start_of(value: str) -> datetime | None:
    try:
        day = date.fromisoformat(value)
    except ValueError:
        return None

    return datetime.combine(day, datetime.min.time(), tzinfo=UTC)
