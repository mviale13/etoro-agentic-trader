"""Show what this platform read from a company's own report, and from where.

Developer-level inspection, deliberately. It exists so the evidence
behind a stored size can be checked against the filing by hand — the
table, the rows, the printed figures — which is the only way to know the
applicability boundary is doing its job on a document nobody has read
before.

It is not a presentation surface and must not become one. Nothing here
decides anything, and the investor-facing question — what these facts add
up to — belongs to a rule and a page that do not exist yet.
"""

from __future__ import annotations

from app.domain.company_knowledge import CompanyKnowledge
from app.services.company_knowledge_service import (
    CompanyKnowledgeService,
    KnowledgeOutcome,
)


class KnowledgeCommand:
    async def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = await CompanyKnowledgeService().knowledge(normalized)

        _render(normalized, outcome)

        return 0 if outcome.state.is_available else 1


def _render(symbol: str, outcome: KnowledgeOutcome) -> None:
    print(f"{symbol} — {outcome.state.value}")
    print()

    if outcome.absent_because:
        print(outcome.absent_because)
        print()

    if outcome.knowledge is None:
        print("Nothing has been read for this security.")
        return

    _render_knowledge(outcome.knowledge)


def _render_knowledge(knowledge: CompanyKnowledge) -> None:
    print(knowledge.stated_source())
    print(f"read: {knowledge.reading.source}")
    print()
    print(knowledge.description)
    print()

    for segment in knowledge.segments:
        print(f"  {segment.name}")

        if segment.description is None:
            # Three independent claims, and this one is not established.
            # The segment stands on the document naming it and on the
            # cells that measured it; what it does is simply unknown.
            print("    does: absent")
            print(f"      because: {segment.undescribed_because or 'not stated'}")
        else:
            models = ", ".join(model.value for model in segment.revenue_models)
            print(f"    earns by: {models or 'not stated'}")
            print(f"    does: {segment.description.evidence.stated()}")

            repair = segment.description.repair

            if repair is not None:
                # A repaired span is never shown as though it were the
                # first answer. What the platform asked twice for is part
                # of what a reader is owed about how it knows this.
                print(f"      repaired: second request, by {repair.reader}")
                print(f"      first citation refused: {repair.first_refused_because}")

        if segment.revenue is None:
            # Absent is a result, not a blank. A segment the filing
            # described without a figure this platform could locate in a
            # table is not a small segment.
            print("    size: absent — no table figure was proven for it")
            print(f"      because: {segment.unmeasured_because or 'not stated'}")
            continue

        print(f"    size: {segment.revenue.stated()}")
        print(
            f"      part:  {segment.revenue.numerator.cell.stated()} "
            f"= {segment.revenue.numerator.printed}"
        )
        print(
            f"      whole: {segment.revenue.denominator.cell.stated()} "
            f"= {segment.revenue.denominator.printed}"
        )
        print(
            f"      shared: {segment.revenue.shared.value} — {segment.revenue.basis!r}"
        )

    print()

    measured = knowledge.measured_share

    if not measured:
        print("No segment size was measured.")
        return

    print(f"measured: {measured:.1%} of the total each was compared against")

    if measured > 1.0:
        # Not an error. A consolidated revenue line is the segments less
        # what they sold each other, so the parts exceed the whole by
        # however much of that trade there was.
        print(
            "  above 100% — segment figures include revenue the segments "
            "billed each other, which consolidation eliminates. The excess "
            "is that trade, not an error."
        )


async def run(symbol: str) -> int:
    return await KnowledgeCommand().run(symbol)
