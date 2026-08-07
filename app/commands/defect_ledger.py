"""Show every defect pattern's engineering history, by historical cost.

The surface of the reader defect ledger: for each pattern, when the
served consensus first carried it, when a reading last found it, how
many claims it has ever blocked, and whether a rerun still finds it —
with any PR claim credited only where the measurement agrees. The
taxonomy beside it answers "where do absences concentrate now?"; this
answers "what has each pattern cost, and what actually got fixed?".
"""

from __future__ import annotations

from datetime import datetime

from app.domain.defect_ledger import DefectLedger, LedgerEntry, LedgerStatus
from app.services.defect_ledger_service import DefectLedgerService


class DefectLedgerCommand:
    async def run(self) -> int:
        _render(DefectLedgerService().ledger())

        return 0


def _render(ledger: DefectLedger) -> None:
    print("reader defect ledger — every pattern the served consensus has carried")
    print()

    entries = ledger.entries
    open_count = sum(1 for entry in entries if entry.status is LedgerStatus.OPEN)

    print(
        f"  {len(ledger.scanned)} companies replayed, "
        f"{len(entries)} patterns recorded: "
        f"{open_count} open, {len(entries) - open_count} resolved"
    )
    print()

    if not entries:
        print("the store's history carries no defect patterns.")
        return

    print("by historical cost — claims blocked, ever:")
    print()

    for entry in entries:
        _render_entry(entry)

    for claim in ledger.unadjudicated:
        print(
            f"  a claim the replay cannot adjudicate: PR "
            f"#{claim.pull_request} ({claim.shipped}) claims "
            f"'{claim.cause.value}', a pattern the store's reachable "
            "history never recorded."
        )
        print()

    print("what this ledger cannot show:")
    print(
        "  the replay reaches only readings the store's current schema "
        "restores — a reading a schema migration rewrote left no trace, "
        "and a reading the grounding contract refused stored nothing. "
        "'last observed' is the newest stored reading that found the "
        "pattern, never today: a pattern nothing has retested stays "
        "exactly as dated."
    )


def _render_entry(entry: LedgerEntry) -> None:
    label = entry.cause.value
    dots = "." * max(44 - len(label), 3)

    print(f"  {label} {dots} {entry.status.value.upper()}")

    plural = "company" if len(entry.companies) == 1 else "companies"

    print(
        f"    first {_dated(entry.first_observed)}, "
        f"last {_dated(entry.last_observed)} — "
        f"{entry.occurrences} claim(s) across "
        f"{len(entry.companies)} {plural} ({', '.join(entry.companies)})"
    )

    if entry.status is LedgerStatus.OPEN:
        print(
            f"    still found: {entry.open_claims} claim(s) "
            f"({', '.join(entry.open_companies)})"
        )
    elif entry.credited:
        for claim in entry.credited:
            print(
                f"    resolved — credited to PR #{claim.pull_request} "
                f"({claim.shipped}): this rerun no longer finds the pattern."
            )
    else:
        print(
            "    resolved — no PR claims this pattern; it stopped being "
            "found without a recorded slice (a new filing or new "
            "observations can do that too)."
        )

    for claim in entry.unconfirmed:
        print(
            f"    claimed resolved by PR #{claim.pull_request} "
            f"({claim.shipped}) — not credited: this rerun still finds it."
        )

    print()


def _dated(moment: datetime) -> str:
    """A store timestamp as the surface states it."""

    return moment.strftime("%Y-%m-%d %H:%M")


async def run() -> int:
    return await DefectLedgerCommand().run()
