"""What happened to a digital asset, and who says so.

The evidence surface beneath the brief. Where `crypto-intelligence`
shows the few developments that matter and what they may mean, this
shows the working: every event that survived, every account of it, what
each account asserts and what it merely reads into things.

Read-only. It serves what `movrvest acquire` stored and asks no surface,
so opening it costs nothing and shows nothing that was not already read.
"""

from __future__ import annotations

from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.crypto_event import CryptoEvent, EventStatus
from app.services.crypto_event_service import CryptoEventService


class CryptoEventsCommand:
    def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = CryptoEventService.stored()

        if symbol is None:
            _render_corpus(service)
            return 0

        normalized = symbol.upper().strip()

        feed = service.established(normalized)

        print(f"{normalized} — current developments")
        print()

        if not feed.events:
            print(
                _wrap(
                    "No material current event is held for this asset. Either "
                    "nothing recent enough was found, or the surfaces have "
                    "not been read — `movrvest acquire` reads them, and it is "
                    "an explicit spend.",
                    "  ",
                )
            )
        else:
            for event in feed.events:
                _render(event, evidence)

        if feed.health:
            print()
            print("  Surfaces")

            for item in feed.health:
                print(_wrap(f"· {item.stated}", "    "))

        return 0


def _render(event: CryptoEvent, evidence: bool) -> None:
    when = f"{event.at:%Y-%m-%d %H:%M}" if event.at else "undated"

    unsettled = (
        "" if event.status is EventStatus.COMPLETED else f" · {event.status.stated}"
    )

    print(_wrap(f"· [{event.family.stated}] {event.headline}", "  "))
    print(f"      {when} UTC · {event.tier.stated}{unsettled}")

    for fact in event.facts:
        mark = (
            f"  [also reported by {', '.join(fact.corroborated_by)}]"
            if fact.is_corroborated
            else ""
        )

        print(_wrap(f"fact: {fact.stated}{mark}", "      "))

    for reading in event.interpretations:
        tag = " [asserts a cause]" if reading.is_causal else ""

        print(_wrap(f"reads: “{reading.stated}” — {reading.source}{tag}", "      "))

    if evidence:
        for report in event.reports:
            where = f" — {report.url}" if report.url else ""

            print(
                _wrap(f"source: {report.source} ({report.tier.value}){where}", "      ")
            )

        print(f"      identity: {event.identity}")

    print()


def _render_corpus(service: CryptoEventService) -> None:
    print("Current developments — the corpus")
    print()
    print(
        _wrap(
            "What has been read for each asset. Events are ranked by what "
            "kind of development they are, then by whether they are still "
            "running, then by how close the reporting gets — never by a "
            "score. Stale ones are dropped rather than ranked last.",
            "  ",
        )
    )
    print()
    print(
        f"  {'':7s} {'events':>6s} {'sourced':>8s} {'primary':>8s}  leading development"
    )

    for symbol in sorted(ASSIGNMENTS):
        events = service.established(symbol).events

        if not events:
            print(f"  {symbol:7s} {0:>6d} {'—':>8s} {'—':>8s}  none held")
            continue

        multi = sum(1 for event in events if event.is_multi_source)
        primary = sum(1 for event in events if event.tier.value == "primary")

        print(
            f"  {symbol:7s} {len(events):>6d} {multi:>8d} {primary:>8d}  "
            f"{events[0].headline[:44]}"
        )


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + ("  " if text.startswith("·") else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None, evidence: bool = False) -> int:
    return CryptoEventsCommand().run(symbol, evidence)
