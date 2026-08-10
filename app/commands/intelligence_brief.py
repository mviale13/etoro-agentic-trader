"""What is happening to a digital asset, and why it matters.

The investor-facing end of the intelligence layer, and the deterministic
one: no model is asked, and the whole brief renders from the structured
snapshot alone. A writer may later order and word this; nothing here
depends on one existing.

Two things it deliberately does not do. It does not print the ledger —
every claim carries a drill-down and the default view shows the
statement, with the epistemic label beside it rather than a paragraph of
provenance. And it does not pick a side: where the evidence points both
ways, the tension is stated as tension.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import ASSIGNMENTS, archetype_for
from app.domain.crypto_event import EventStatus
from app.domain.crypto_intelligence import (
    ClaimType,
    CryptoIntelligenceSnapshot,
    Driver,
)
from app.domain.intelligence_synthesis import IntelligenceSynthesis
from app.services.crypto_intelligence_service import CryptoIntelligenceService
from app.services.intelligence_synthesis_service import IntelligenceSynthesisService

#: How each epistemic type appears beside a statement. Short, because
#: the label must not outweigh the sentence it qualifies.
_MARK = {
    ClaimType.MEASURED: "measured",
    ClaimType.REPORTED: "reported",
    ClaimType.ATTRIBUTED: "attributed",
    ClaimType.INFERRED: "MOVRvest",
    ClaimType.UNRESOLVED: "unresolved",
}


class IntelligenceBriefCommand:
    async def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = CryptoIntelligenceService()

        if symbol is None:
            _render_corpus(service)
            return 0

        normalized = symbol.upper().strip()

        snapshot = service.snapshot(normalized, AssetClass.CRYPTO)

        if snapshot is None:
            print(f"{normalized} — no intelligence: this is not a digital asset.")
            return 1

        # The reading is asked for *after* the evidence is assembled and
        # is allowed to be absent. Nothing below depends on it.
        synthesis = await IntelligenceSynthesisService().synthesise(snapshot)

        _render(snapshot, evidence, synthesis)

        return 0


def _render(
    snapshot: CryptoIntelligenceSnapshot,
    evidence: bool,
    synthesis: IntelligenceSynthesis | None = None,
) -> None:
    assignment = archetype_for(snapshot.symbol)

    print(f"{snapshot.symbol} — current intelligence")
    print(f"  {assignment.definition.name} · read {snapshot.as_of:%Y-%m-%d %H:%M} UTC")

    if snapshot.thin_because:
        print()
        print(_wrap(snapshot.thin_because, "  "))
        return

    # The answer first, the evidence second. A reader who wants only the
    # reading stops here; a reader who wants to check it reads on, and
    # every statement above names the findings it rests on.
    if synthesis is not None:
        _render_synthesis(synthesis, evidence)

    _section("What changed", _changes(snapshot, evidence))
    _section("Material developments", _events(snapshot, evidence))
    _section("What appears to be driving it", _drivers(snapshot, evidence))
    _section("Tailwinds", [_driver_line(d) for d in snapshot.tailwinds])
    _section("Headwinds", [_driver_line(d) for d in snapshot.headwinds])
    _section("What sources are saying", _narratives(snapshot))
    _section("Relative context", list(snapshot.relative_context))
    _section("Held in tension", list(snapshot.conflicting))
    _section("Foundation", list(snapshot.foundation.lines))
    _section("Unresolved", list(snapshot.foundation.unresolved))
    _section("Watch next", _watch(snapshot))
    _section("Surfaces not read", list(snapshot.surfaces_unread))

    print()
    print(
        _wrap(
            "Every line above resolves to a structured claim. `measured` is "
            "this platform's arithmetic, `reported` is a source's fact, "
            "`attributed` is a source's opinion and `MOVRvest` is this "
            "platform's reading. Nothing here is a recommendation, and "
            "nothing here changes one.",
            "  ",
        )
    )


def _render_synthesis(synthesis: IntelligenceSynthesis, evidence: bool) -> None:
    """The reading, or the worded reason there is none. Never both.

    An absent synthesis is printed as a single line rather than
    swallowed: an investor who cannot tell whether the model was off,
    refused, or wrote something that failed grounding is being told less
    than this platform knows.
    """

    if not synthesis.status.is_written:
        print()
        print(_wrap(f"MOVRvest reading — {synthesis.absent_because}", "  "))
        return

    for title, items in (
        ("What matters now", synthesis.what_matters),
        ("Why it matters", synthesis.why_it_matters),
        ("Watch next", synthesis.watch_next),
    ):
        lines: list[str] = []

        for item in items:
            tail = f"\n      [{', '.join(item.refs)}]" if evidence else ""

            label = f"{item.theme} — " if item.theme else ""

            lines.append(f"{label}{item.stated}{tail}")

        _section(title, lines)

    print()
    print(
        _wrap(
            f"The three sections above are a reading of the evidence below, "
            f"written by {synthesis.model} over the findings this platform "
            "holds and nothing else. Every statement cites them; run with "
            "--evidence to see which. It is not a recommendation.",
            "  ",
        )
    )


def _changes(snapshot: CryptoIntelligenceSnapshot, evidence: bool) -> list[str]:
    """The readings, without the developments.

    Every event is also a claim, so that a driver can reference one — but
    printing it here as well as under *Material developments* said each
    thing twice, and a brief that repeats itself reads as though it had
    found twice as much.
    """

    events = {event.identity for event in snapshot.events}

    lines: list[str] = []

    for claim in snapshot.live:
        if claim.ref in events:
            continue

        stale = "" if claim.is_live else "  [stale]"

        lines.append(
            f"{claim.stated}{stale}\n"
            f"      ({_MARK[claim.claim_type]} · {claim.source} · "
            f"{claim.relevance.stated.lower()})"
        )

        if evidence and claim.does_not_establish:
            lines.append(f"      does not establish: {claim.does_not_establish}")

    return lines


def _drivers(snapshot: CryptoIntelligenceSnapshot, evidence: bool) -> list[str]:
    lines: list[str] = []

    for driver in snapshot.drivers:
        lines.append(f"{driver.stated}\n      ({driver.support.stated.lower()})")

        if driver.matters_because:
            lines.append(f"      why it matters: {driver.matters_because}")

        if evidence:
            for ref in driver.claims:
                claim = snapshot.claim(ref)

                if claim is not None:
                    lines.append(f"      ← {ref}: {claim.stated}")

    return lines


def _events(snapshot: CryptoIntelligenceSnapshot, evidence: bool) -> list[str]:
    """The developments themselves.

    The section §10 says must be allowed to be empty. Where nothing
    survived the age and materiality rules the brief says so, because a
    fortnight-old headline dressed as today's news is worse than a blank
    line — and the reader cannot tell which they are looking at unless
    the platform says.
    """

    if not snapshot.events:
        return [
            "No material current event identified. Nothing recent enough "
            "and material enough was found — this is a stated absence, "
            "not an empty section."
        ]

    lines: list[str] = []

    for event in snapshot.events:
        witnesses = (
            f"{len(event.sources)} sources"
            if event.is_multi_source
            else event.sources[0]
        )

        when = f"{event.at:%-d %b %H:%M}" if event.at else "undated"

        unsettled = (
            "" if event.status is EventStatus.COMPLETED else f" · {event.status.stated}"
        )

        lines.append(
            f"[{event.family.stated}] {event.headline}\n"
            f"      ({when} · {witnesses} · {event.tier.stated}{unsettled})"
        )

        if not evidence:
            continue

        for fact in event.facts[:3]:
            mark = (
                f"  [corroborated by {', '.join(fact.corroborated_by)}]"
                if fact.is_corroborated
                else ""
            )

            lines.append(f"      fact: {fact.stated}{mark}")

        for report in event.reports:
            if report.url:
                lines.append(f"      {report.source}: {report.url}")

    return lines


def _narratives(snapshot: CryptoIntelligenceSnapshot) -> list[str]:
    """Published readings, each with its author, none of them promoted."""

    lines: list[str] = []

    for narrative in snapshot.narratives[:6]:
        mark = " [asserts a cause — not checked here]" if narrative.is_causal else ""

        lines.append(f"“{narrative.stated}”\n      — {narrative.source}{mark}")

    return lines


def _watch(snapshot: CryptoIntelligenceSnapshot) -> list[str]:
    lines: list[str] = []

    for item in snapshot.watch_next:
        when = f" (scheduled {item.scheduled_for:%-d %B})" if item.is_scheduled else ""

        lines.append(f"{item.stated}{when}\n      measured by: {item.measured_by}")

    return lines


def _driver_line(driver: Driver) -> str:
    return f"{driver.stated} ({driver.support.stated.lower()})"


def _section(title: str, lines: list[str]) -> None:
    if not lines:
        return

    print()
    print(f"  {title}")

    for line in lines:
        head, _, tail = line.partition("\n")
        print(_wrap(f"· {head}", "    "))

        for extra in tail.splitlines():
            print(_wrap(extra.strip(), "      "))


def _render_corpus(service: CryptoIntelligenceService) -> None:
    print("Current intelligence — the corpus")
    print()
    print(
        _wrap(
            "What this platform can say about each asset right now. It does "
            "not depend on Asset Quality: an asset whose quality reads "
            "UNKNOWN is not one there is nothing to say about.",
            "  ",
        )
    )
    print()
    print(
        f"  {'':7s} {'claims':>7s} {'drivers':>8s} {'tail':>5s} {'head':>5s}"
        "  foundation"
    )

    for symbol in sorted(ASSIGNMENTS):
        snapshot = service.snapshot(symbol, AssetClass.CRYPTO)

        if snapshot is None:
            continue

        print(
            f"  {symbol:7s} {len(snapshot.live):>7d} {len(snapshot.drivers):>8d} "
            f"{len(snapshot.tailwinds):>5d} {len(snapshot.headwinds):>5d}  "
            f"{len(snapshot.foundation.lines)} line(s)"
        )


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + (" " * 2 if text.startswith(("-", "·")) else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None, evidence: bool = False) -> int:
    return await IntelligenceBriefCommand().run(symbol, evidence)
