"""Show what this platform knows from a company's own report, and how firmly.

Developer-level inspection, deliberately. It exists so the evidence
behind a stored size can be checked against the filing by hand — the
table, the rows, the printed figures — which is the only way to know the
applicability boundary is doing its job on a document nobody has read
before.

What it renders is a consensus, and every claim carries its width: 3 of
5 and 5 of 5 must never look identical, so any claim short of unanimity
prints its full distribution. Below quorum the same surface serves the
observations it has, labeled — one reading is presented as one reading,
never as the settled account.

It is not a presentation surface and must not become one. Nothing here
decides anything.
"""

from __future__ import annotations

from app.domain.agreement import Agreement
from app.domain.knowledge_consensus import (
    CompanyKnowledgeConsensus,
)
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


def _render_knowledge(consensus: CompanyKnowledgeConsensus) -> None:
    print(consensus.stated_source())
    print(f"read: {consensus.reading.source}")

    if not consensus.is_quorate:
        print(
            f"  {consensus.observation_count} of the {consensus.quorum} "
            "observations this platform wants before calling anything "
            "settled. Every claim below is what the observations so far "
            "say, at that width."
        )

    print()
    print(consensus.description)
    print("  (one observation's wording — the self-description is not yet calibrated)")
    print()

    if consensus.segments_because is not None:
        print(f"segments: unsettled — {consensus.segments_because}")
        return

    _agreement("segments", consensus.identity)

    for segment in consensus.segments:
        print(f"  {segment.name}")

        if segment.described is None:
            print("    does: unsettled")
            print(f"      because: {segment.undescribed_because or 'not stated'}")
        elif segment.described is False:
            # Three independent claims, and this one is not established.
            # The segment stands on the document naming it and on the
            # cells that measured it; what it does is simply unknown.
            print("    does: absent")
            print(f"      because: {segment.undescribed_because or 'not stated'}")
        else:
            models = ", ".join(model.value for model in segment.revenue_models)

            if models:
                print(f"    earns by: {models}")
            else:
                print("    earns by: not established")
                # No stored reason means the claim settled on absence:
                # the observations agree the description names no way of
                # earning, which is a fact about the filing rather than
                # a disagreement about it.
                print(
                    "      because: "
                    + (
                        segment.undescribed_because
                        or "the settled description names no way of earning"
                    )
                )

        _agreement("earns by", segment.earning_agreement, indent="    ")
        _agreement("described", segment.described_agreement, indent="    ")

        # The spans never settle — they are evidence attached to the
        # observations that produced them, and this is the record a
        # reader checks against the filing, minority answers included.
        _agreement("cited", segment.span_agreement, indent="    ", always=True)

        if segment.revenue is None:
            # Absent is a result, not a blank. A segment the filing
            # described without a figure this platform could locate in a
            # table is not a small segment.
            print("    size: absent — no settled table figure")
            print(f"      because: {segment.unmeasured_because or 'not stated'}")
            _agreement("size", segment.size_agreement, indent="    ")
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
        _agreement("size", segment.size_agreement, indent="    ")

    print()

    measured = consensus.measured_share

    if not measured:
        print("No segment size was settled.")
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


def _agreement(
    named: str,
    measured: Agreement,
    indent: str = "",
    always: bool = False,
) -> None:
    """One claim's width, and its full distribution short of unanimity.

    A unanimous claim prints one quiet line; a split one prints every
    answer with its count. The one thing this never does is show only
    the winner.
    """

    if measured.modal is None:
        return

    print(f"{indent}{named}: {measured.agreeing} of {measured.readings} agree")

    if measured.settled and not always:
        return

    for answer in measured.answers:
        print(f"{indent}  {answer.given}× {answer.stated}")


async def run(symbol: str) -> int:
    return await KnowledgeCommand().run(symbol)
