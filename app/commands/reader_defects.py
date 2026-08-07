"""Show every reader-blocked claim in the store, counted by cause.

The surface of the reader defect taxonomy: counts first — the number
the unfreeze decision reads — then every defect with its verbatim
reason, then the verdict the pattern rule gives, then what the store
cannot show. Not a work queue: a measurement of where the reader's
absences actually concentrate.
"""

from __future__ import annotations

from app.domain.reader_defects import DefectTaxonomy
from app.services.reader_defect_service import ReaderDefectService


class ReaderDefectsCommand:
    async def run(self) -> int:
        _render(ReaderDefectService().taxonomy())

        return 0


def _render(taxonomy: DefectTaxonomy) -> None:
    print("reader defect taxonomy — every absent claim in the store, by cause")
    print()
    print(
        f"  {len(taxonomy.scanned)} companies scanned, "
        f"{len(taxonomy.affected)} carrying defects, "
        f"{len(taxonomy.defects)} absent claims"
    )
    print()

    if not taxonomy.defects:
        print("the store carries no absent claims.")
        return

    print("by structural cause:")

    for count in taxonomy.by_cause:
        label = count.cause.value
        dots = "." * max(44 - len(label), 3)
        plural = "company" if count.companies == 1 else "companies"
        print(f"  {label} {dots} {count.companies} {plural}, {count.claims} claim(s)")
        print(f"    {', '.join(count.symbols)}")

    print()
    print("every defect, with the knowledge layer's own reason:")

    for defect in taxonomy.defects:
        print(
            f"  {defect.symbol:<10} {defect.segment} — {defect.claim.value} "
            f"({defect.width} observation(s))"
        )
        print(f"    {defect.cause.value}: {defect.because}")

    print()

    earned = taxonomy.earned()

    if earned:
        print("the pattern rule's verdict — causes that reach 2+ companies:")

        for count in earned:
            print(
                f"  {count.cause.value} — {count.companies} companies "
                f"({', '.join(count.symbols)}): this pattern has earned "
                "an engineering slice."
            )
    else:
        print(
            "the pattern rule's verdict: no cause reaches 2 companies — "
            "every failure is unique, and reader work stays frozen."
        )

    print()
    print("what the store cannot show:")
    print(
        "  a reading the grounding contract refused outright stores "
        "nothing, so total refusals are visible only at the moment of "
        "refusal. Those live on the reader watchlist in MIGRATION_PLAN.md."
    )


async def run() -> int:
    return await ReaderDefectsCommand().run()
