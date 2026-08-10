"""What this platform has seen over time, and how often it looked.

Read-only, deterministic, and asks no model. It renders the record and
the deterministic projection over it — never an interpretation, because
the journal is not an analyst and the surface that reads it must not
become one either.

The wording throughout says **captures**, never a bare duration. That is
the whole discipline of this surface: *"observed on 3 captures spanning
21 days, the longest gap between them 14 days"* is what the record
supports, and *"positive for three weeks"* is what it does not.
"""

from __future__ import annotations

from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.intelligence_journal import Capture, TemporalFact
from app.services.intelligence_journal_service import IntelligenceJournalService


class IntelligenceJournalCommand:
    def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = IntelligenceJournalService()

        if symbol is None:
            _render_corpus(service)
            return 0

        normalized = symbol.upper().strip()

        captures = service.captures(normalized)

        print(f"{normalized} — the intelligence record")
        print()

        if not captures:
            print(
                _wrap(
                    "Nothing has been recorded for this asset. The journal is "
                    "written by `movrvest acquire`, which is the explicit "
                    "spend — a page view never adds to it.",
                    "  ",
                )
            )
            return 0

        _render_coverage(captures)

        facts = service.history(normalized)

        _render_history(facts, evidence)

        print()
        print(
            _wrap(
                "Every line above is a reading of recorded observations, not "
                "an interpretation of them. A count of captures is not a "
                "duration of monitoring, and the wording says so wherever "
                "the difference could mislead. Nothing here is a "
                "recommendation, and nothing here changes one.",
                "  ",
            )
        )

        return 0


def _render_coverage(captures: list[Capture]) -> None:
    """How often this platform looked. The honesty section.

    Printed first and before any finding, because everything below it is
    only as good as this: a reader who does not know the platform looked
    three times cannot judge a claim built on three observations.
    """

    first = captures[0]
    last = captures[-1]

    span = (last.captured_at - first.captured_at).days

    print("  Coverage")
    print(
        _wrap(
            f"· {len(captures)} capture(s), the first {first.captured_at:%-d %B %H:%M} "
            f"and the most recent {last.captured_at:%-d %B %H:%M} UTC"
            + (f", spanning {span} day(s)." if span else ", on the same day."),
            "    ",
        )
    )

    gaps = [
        (later.captured_at - earlier.captured_at).days
        for earlier, later in zip(captures, captures[1:], strict=False)
    ]

    if gaps and max(gaps) >= 2:
        print(
            _wrap(
                f"· The longest gap between captures was {max(gaps)} day(s). "
                "Anything between them was not observed.",
                "    ",
            )
        )

    print()


def _render_history(facts: tuple[TemporalFact, ...], evidence: bool) -> None:
    if not facts:
        print("  Nothing in the record can be compared yet.")
        return

    grouped: dict[str, list[TemporalFact]] = {}

    for fact in facts:
        grouped.setdefault(fact.status.stated, []).append(fact)

    for status, group in grouped.items():
        print(f"  {status.capitalize()}")

        for fact in group:
            print(_wrap(f"· {fact.stated}", "    "))

            if fact.nature is not None:
                print(_wrap(f"— {fact.nature.stated}", "      "))

            if evidence:
                print(_wrap(f"journal: {', '.join(fact.entry_ids[-3:])}", "      "))

        print()


def _render_corpus(service: IntelligenceJournalService) -> None:
    print("The intelligence record — the corpus")
    print()
    print(
        _wrap(
            "How much history exists per asset. A temporal claim is only as "
            "good as the number of times this platform actually looked, so "
            "that number is what this table leads with.",
            "  ",
        )
    )
    print()
    print(f"  {'':7s} {'captures':>9s} {'span':>7s} {'changed':>8s}  first recorded")

    for symbol in sorted(ASSIGNMENTS):
        captures = service.captures(symbol)

        if not captures:
            print(f"  {symbol:7s} {0:>9d} {'—':>7s} {'—':>8s}  never")
            continue

        span = (captures[-1].captured_at - captures[0].captured_at).days

        changed = sum(1 for fact in service.history(symbol) if fact.status.is_change)

        print(
            f"  {symbol:7s} {len(captures):>9d} {span:>6d}d {changed:>8d}  "
            f"{captures[0].captured_at:%Y-%m-%d %H:%M}"
        )


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + ("  " if text.startswith(("·", "—")) else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None, evidence: bool = False) -> int:
    return IntelligenceJournalCommand().run(symbol, evidence)
