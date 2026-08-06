"""Show what kind of business a company is, and what decided it.

The first surface for something this platform *concludes*. It shows the
answer, then every rule that produced it, then the facts each rule read,
then what was missing — in that order, because a reader who trusts the
answer stops at the first line and a reader who does not can follow it
all the way back to a table cell in a filing.

An undecided archetype is rendered as fully as a decided one. The
question a reader has when a company comes back unclassified is *why*,
and answering it with a blank would make the platform look ignorant of
the company rather than honest about its own reading.
"""

from __future__ import annotations

from app.domain.company_archetype import CompanyArchetype, Dimension
from app.services.archetype_engine import classify
from app.services.company_knowledge_service import CompanyKnowledgeService


class ArchetypeCommand:
    async def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = await CompanyKnowledgeService().knowledge(normalized)

        if outcome.knowledge is None:
            print(f"{normalized} — not classified")
            print()
            print(
                outcome.absent_because or "No filing has been read for this security."
            )
            print()
            print(
                "An archetype is decided from a company's own report. Without "
                "one there is nothing to decide it from, and no industry is "
                "substituted for it."
            )
            return 1

        _render(classify(outcome.knowledge))

        return 0


def _render(archetype: CompanyArchetype) -> None:
    print(f"{archetype.symbol} — {archetype.stated}")
    print()
    print(archetype.source)
    print(f"read: {archetype.reading.source}")
    print()

    if archetype.candidates:
        # Known ways of earning, no measured sizes to order them by. The
        # list is what the platform can say; the ranking is what it
        # cannot, and the reason sits below.
        print("could be, unranked:")
        for candidate in archetype.candidates:
            print(f"  {candidate.stated}")
        print()

    if archetype.undecided_because:
        print(archetype.undecided_because)
        print()

    if archetype.coverage:
        # Worded so it cannot be read — or later relabelled — as a split
        # of revenue between these ways of earning. No filing states one.
        print("how this business earns, by coverage:")
        print("  (how much of the business earns this way, among others —")
        print("   not how much revenue comes from it, which no filing states)")
        print()
        for coverage in archetype.coverage:
            covers = (
                f"segments worth {coverage.covers:.0%} of the revenue total"
                if coverage.covers is not None
                else "segment sizes unmeasured"
            )
            print(f"  {coverage.model.value}: {covers}")
            print(f"    via {', '.join(coverage.segments)}")
        print()

    print(f"measured: {archetype.measured:.0%} of the total each was compared against")
    print(f"explained: {archetype.explained:.0%} of it is also shown to earn a way")

    if archetype.measured > 1.0:
        # The same artefact the knowledge command explains, and it has to
        # be explained here too: a coverage above 100% reads as an error
        # to anyone who has not been told what the denominator is.
        print(
            "  above 100% — segment figures include revenue the segments "
            "billed each other, which consolidation eliminates. The excess "
            "is that trade, not an error."
        )

    print()

    print("rules:")
    for ruling in archetype.basis:
        print(f"  {ruling.rule}")
        print(f"    read: {ruling.read}")
        print(f"    concluded: {ruling.concluded}")
    print()

    if not archetype.missing:
        return

    print("not established:")
    for gap in archetype.missing:
        what = "size" if gap.dimension is Dimension.SIZE else "way of earning"
        print(f"  {gap.segment} — {what}")
        print(f"    {gap.because}")


async def run(symbol: str) -> int:
    return await ArchetypeCommand().run(symbol)
