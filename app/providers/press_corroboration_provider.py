"""The press, admitted as a witness and never as a discoverer.

Five crypto feeds were measured on 2026-08-10. All five answer, all five
are free and keyless, all five are fresh to the minute, and all five
parse as ordinary RSS:

```text
CoinDesk        25 items, newest 13 minutes old
Cointelegraph   30 items, newest 5 minutes old
The Block       20 items, newest ~1 hour old
Decrypt         30 items
Bitcoin Magazine 30 items
```

So the question was never availability. It was what letting them in
would do to the product, and the answer is the rule this module exists
to enforce:

> **A press item may corroborate an event that another source already
> established. It may never introduce one.**

The reasoning is the ruling's own: *"if the result is merely a longer
news list, the slice failed."* A feed of a hundred headlines a day
contains perhaps three developments that bear on a held asset, and this
platform has no way to tell which three — a keyword gate over headlines
is a relevance model, and a bad one, and it would fill the brief with
whatever the wire happened to carry. What the press *can* do without any
judgement at all is answer a question already asked: **did anyone else
report this?** That is a matching problem, not a selection problem, and
matching is something a deterministic rule does honestly.

What this buys, concretely: when CoinGecko summarises *"H100 Group
Increases Bitcoin Holdings to 3,506 BTC"* and The Block runs *"Adam
Back-backed H100 more than triples bitcoin holdings to 3,506 BTC"*, the
two collapse into one event with two independent accounts beneath it —
and the shared figure, not the shared words, is what proves they are the
same event.

**Nothing here is ever primary.** A publication reporting an exploit is
not the exploit's register, and corroboration raises a claim's
provenance, never its standing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import requests

from app.domain.crypto_event import (
    CryptoEvent,
    EventFeedHealth,
    SourceReport,
    SourceTier,
    anchors_in,
    keywords_in,
)

TIMEOUT = 25

HEADERS = {"User-Agent": "movrvest/1.0", "Accept": "application/rss+xml, text/xml"}

#: Nothing larger than this is parsed. Two reasons, and the second is
#: the one that matters: a feed that grew to megabytes is a feed whose
#: shape changed, and `ElementTree` is documented as vulnerable to
#: entity-expansion attacks on hostile XML. This platform declares no
#: XML dependency, so the defence is a byte cap and a refusal to parse
#: anything declaring a DTD.
MAX_BYTES = 2_000_000

_DOCTYPE = re.compile(rb"<!(DOCTYPE|ENTITY)", re.I)

#: The feeds, named. A source list is a product decision and belongs
#: where it can be read, not spread through the code.
FEEDS: tuple[tuple[str, str], ...] = (
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("The Block", "https://www.theblock.co/rss.xml"),
    ("Decrypt", "https://decrypt.co/feed"),
)

_ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass(frozen=True, slots=True)
class PressItem:
    """One headline, with what it can be matched on."""

    source: str
    title: str
    url: str | None
    published_at: datetime | None

    @property
    def anchors(self) -> tuple[str, ...]:
        return anchors_in(self.title)

    @property
    def keywords(self) -> tuple[str, ...]:
        return keywords_in(self.title, limit=10)


class PressCorroborationProvider:
    """Headlines, held only to be matched against events already found."""

    def items(self) -> tuple[tuple[PressItem, ...], tuple[EventFeedHealth, ...]]:
        collected: list[PressItem] = []
        health: list[EventFeedHealth] = []

        for name, url in FEEDS:
            items, status = self._feed(name, url)

            collected.extend(items)
            health.append(status)

        return tuple(collected), tuple(health)

    def _feed(
        self,
        name: str,
        url: str,
    ) -> tuple[tuple[PressItem, ...], EventFeedHealth]:
        try:
            response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)

            response.raise_for_status()

            body = response.content
        except Exception as exc:  # noqa: BLE001
            return (), EventFeedHealth(
                source=name, reached=False, because=type(exc).__name__
            )

        if len(body) > MAX_BYTES or _DOCTYPE.search(body[:4000]):
            return (), EventFeedHealth(
                source=name,
                reached=False,
                because="the feed was too large or declared a DTD, and was not parsed",
            )

        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError:
            return (), EventFeedHealth(
                source=name, reached=False, because="the feed did not parse as XML"
            )

        nodes = root.findall(".//item") or root.findall(f".//{_ATOM}entry")

        items: list[PressItem] = []

        for node in nodes:
            title = _text(node, "title", f"{_ATOM}title")

            if not title:
                continue

            items.append(
                PressItem(
                    source=name,
                    title=title,
                    url=_link(node),
                    published_at=_when(node),
                )
            )

        return tuple(items), EventFeedHealth(
            source=name,
            reached=True,
            entries_seen=len(nodes),
            entries_parsed=len(items),
        )


#: What a headline must call the asset before it can be read as
#: reporting on it.
#:
#: A gate, not a hint, and it was added because the first live run
#: without it attached four *bitcoin* ETF stories to Ethereum's ETF
#: event — the two headlines shared "spot", "ETFs", "inflows" and
#: "week", which is four words and no subject. A story that never names
#: the asset is not corroboration for it however well its words line up.
ASSET_NAMES = {
    "BTC": ("btc", "bitcoin"),
    "ETH": ("eth", "ethereum", "ether"),
    "SOL": ("sol", "solana"),
    "ADA": ("ada", "cardano"),
    "ARB": ("arb", "arbitrum"),
    "1INCH": ("1inch",),
    "HYPE": ("hype", "hyperliquid"),
    "TAO": ("tao", "bittensor"),
}

#: How many of an event's own figures a headline must repeat before it
#: counts as reporting the same event. One is enough *when it is a
#: distinctive figure*: two stories quoting "3,506 BTC" on the same day
#: are the same story.
_ANCHOR_MATCH = 1

#: Below this, a bare integer is not distinctive enough to identify an
#: event on its own.
#:
#: *"MicroStrategy sold 1,690 BTC between August 3-9"* yields `3` and
#: `9` alongside the figures that matter, and a headline is very likely
#: to contain a small number for reasons of its own. A percentage is
#: exempt: "19%" is specific in a way "3" is not.
_DISTINCTIVE = 1000

#: How many distinguishing words must overlap where no figure is shared.
#: Higher, because words are cheap: "bitcoin" and "ethereum" appear in
#: half the wire on any given day, so a keyword-only match has to earn
#: it. Below this an item is simply not matched, which is the correct
#: outcome — the event keeps the accounts it already had.
_KEYWORD_MATCH = 3


def corroborate(
    event: CryptoEvent,
    items: tuple[PressItem, ...],
    within_hours: int = 48,
) -> CryptoEvent:
    """Attach any press account of *this* event, and add no others.

    Three tests, and all three must pass: the headline **names the
    asset**, it falls within the window, and it shares either a figure
    or enough distinguishing words. A false match invents corroboration,
    which is worse than none at all — it tells a reader two independent
    sources agree when one of them was reporting something else.
    """

    when = event.at

    already = {report.source for report in event.reports}

    found: list[SourceReport] = []

    anchors = distinctive(
        {anchor for fact in event.facts for anchor in fact.anchors}
        | set(anchors_in(event.headline))
    )

    words = set(keywords_in(event.headline, limit=10))

    names = tuple(
        name for symbol in event.symbols for name in ASSET_NAMES.get(symbol, ())
    )

    for item in items:
        if item.source in already:
            continue

        if names and not _names_asset(item.title, names):
            continue

        if when is not None and item.published_at is not None:
            gap = abs((item.published_at - when).total_seconds())

            if gap > within_hours * 3600:
                continue

        shared_anchors = anchors & distinctive(set(item.anchors))
        shared_words = words & set(item.keywords)

        if len(shared_anchors) >= _ANCHOR_MATCH:
            matched = True
        elif len(shared_words) >= _KEYWORD_MATCH:
            matched = True
        else:
            matched = False

        if not matched:
            continue

        already.add(item.source)

        found.append(
            SourceReport(
                source=item.source,
                tier=SourceTier.SECONDARY,
                text=item.title,
                url=item.url,
                published_at=item.published_at,
            )
        )

    if not found:
        return event

    # A fact is corroborated by the outlets whose own headline carries
    # one of *its* figures — not by every outlet that mentioned the
    # event. Two accounts of one exploit may agree on the date and
    # differ on the amount, and only the shared figure is corroborated.
    corroborated = tuple(
        fact.also_reported_by(
            tuple(
                report.source
                for report in found
                if set(fact.anchors) & set(anchors_in(report.text))
            )
        )
        for fact in event.facts
    )

    return CryptoEvent(
        identity=event.identity,
        symbols=event.symbols,
        family=event.family,
        headline=event.headline,
        occurred_at=event.occurred_at,
        published_at=event.published_at,
        observed_at=event.observed_at,
        reports=event.reports + tuple(found),
        facts=corroborated,
        interpretations=event.interpretations,
        status=event.status,
        entity=event.entity,
    )


def distinctive(anchors: set[str]) -> set[str]:
    """The figures specific enough to identify an event by themselves."""

    kept: set[str] = set()

    for anchor in anchors:
        if anchor.endswith("%"):
            kept.add(anchor)
            continue

        try:
            if abs(float(anchor)) >= _DISTINCTIVE:
                kept.add(anchor)
        except ValueError:
            continue

    return kept


def _names_asset(title: str, names: tuple[str, ...]) -> bool:
    """Whether the headline calls the asset by one of its names.

    On word boundaries, because a substring test makes "eth" match
    "Ethena", "together" and "whether" — three ways to attach a story to
    an asset it never mentioned.
    """

    words = set(re.findall(r"[a-z0-9]+", title.lower()))

    return any(name in words for name in names)


def _text(node: ElementTree.Element, *names: str) -> str | None:
    for name in names:
        found = node.find(name)

        if found is not None and found.text:
            return re.sub(r"\s+", " ", found.text).strip()

    return None


def _link(node: ElementTree.Element) -> str | None:
    found = node.find("link")

    if found is not None and found.text:
        return found.text.strip()

    atom = node.find(f"{_ATOM}link")

    if atom is not None:
        href = atom.get("href")

        if href:
            return href

    return None


def _when(node: ElementTree.Element) -> datetime | None:
    raw = _text(
        node,
        "pubDate",
        f"{_ATOM}updated",
        f"{_ATOM}published",
        "{http://purl.org/dc/elements/1.1/}date",
    )

    if raw is None:
        return None

    for parse in (_rfc2822, _iso):
        parsed = parse(raw)

        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    return None


def _rfc2822(raw: str) -> datetime | None:
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def _iso(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
