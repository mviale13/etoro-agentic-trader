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
from app.domain.crypto_intelligence import (
    ClaimType,
    CryptoIntelligenceSnapshot,
    Driver,
)
from app.services.crypto_intelligence_service import CryptoIntelligenceService

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
    def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = CryptoIntelligenceService()

        if symbol is None:
            _render_corpus(service)
            return 0

        normalized = symbol.upper().strip()

        snapshot = service.snapshot(normalized, AssetClass.CRYPTO)

        if snapshot is None:
            print(f"{normalized} — no intelligence: this is not a digital asset.")
            return 1

        _render(snapshot, evidence)

        return 0


def _render(snapshot: CryptoIntelligenceSnapshot, evidence: bool) -> None:
    assignment = archetype_for(snapshot.symbol)

    print(f"{snapshot.symbol} — current intelligence")
    print(f"  {assignment.definition.name} · read {snapshot.as_of:%Y-%m-%d %H:%M} UTC")

    if snapshot.thin_because:
        print()
        print(_wrap(snapshot.thin_because, "  "))
        return

    _section("What changed", _changes(snapshot, evidence))
    _section("What appears to be driving it", _drivers(snapshot, evidence))
    _section("Tailwinds", [_driver_line(d) for d in snapshot.tailwinds])
    _section("Headwinds", [_driver_line(d) for d in snapshot.headwinds])
    _section("Relative context", list(snapshot.relative_context))
    _section("Held in tension", list(snapshot.conflicting))
    _section("Foundation", list(snapshot.foundation.lines))
    _section("Unresolved", list(snapshot.foundation.unresolved))
    _section("Watch next", list(snapshot.watch_next))

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


def _changes(snapshot: CryptoIntelligenceSnapshot, evidence: bool) -> list[str]:
    lines: list[str] = []

    for claim in snapshot.live:
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
    return IntelligenceBriefCommand().run(symbol, evidence)
