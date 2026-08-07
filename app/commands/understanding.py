"""Explain how a business creates value, from consensus knowledge alone.

The first surface of the Business Understanding layer. Everything it
prints is derived deterministically from `CompanyKnowledgeConsensus` —
no model is asked, nothing is re-read, and every line traces to a
settled claim or is an absence carrying its reason. Uncertainty is
printed beside the explanation it qualifies, never below the fold: a
mechanism carried by a 3/5 majority says so where the mechanism is
named, and a conclusion that could flip under an observed minority
answer names the answer and what it would conclude.
"""

from __future__ import annotations

from app.domain.business_understanding import BusinessUnderstanding
from app.services.company_knowledge_service import CompanyKnowledgeService
from app.services.understanding_engine import understand


class UnderstandingCommand:
    async def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = await CompanyKnowledgeService().knowledge(normalized)

        if outcome.knowledge is None:
            print(f"{normalized} — not understood")
            print()
            print(
                outcome.absent_because or "No filing has been read for this security."
            )
            print()
            print(
                "Business Understanding is derived from a company's own "
                "consensus knowledge. Without any, there is nothing to "
                "derive it from, and nothing is substituted."
            )
            return 1

        _render(understand(outcome.knowledge))

        return 0


def _render(understanding: BusinessUnderstanding) -> None:
    print(f"{understanding.symbol} — how this business creates value")
    print()
    print(f"  {understanding.source}")
    print(f"  read: {understanding.reading.source}")

    if not understanding.quorate:
        print(
            f"  {understanding.observation_count} of the quorum of "
            f"{understanding.quorum} — a single reading, and nothing "
            "below is authoritative."
        )

    print()

    if understanding.segments_because is not None:
        print(f"economic engine: not established — {understanding.segments_because}")
        return

    print("economic engine:")
    print(f"  {understanding.engine}")

    if understanding.sells:
        print("  sells through:")

        for sold in understanding.sells:
            share = (
                f"{sold.share:.0%} of revenue"
                if sold.share is not None
                else ("size not settled")
            )
            earns = (
                ", ".join(model.value for model in sold.mechanisms)
                or "ways of earning not established"
            )
            print(f"    {sold.name} — {share}; earns by {earns}")

    print()

    if understanding.mechanisms:
        print("revenue mechanisms:")

        for mechanism in understanding.mechanisms:
            coverage = (
                f"through segments worth {mechanism.coverage:.0%} of revenue"
                if mechanism.coverage is not None
                else "coverage unmeasured"
            )
            print(
                f"  {mechanism.model.value} — {coverage}; "
                f"support {mechanism.support.stated_majority()}"
            )
            print(f"    via {', '.join(mechanism.through)}")

        print()

    print("business characteristics:")
    print(f"  {understanding.characteristics.stated}")

    if understanding.characteristics.rests_on:
        print(f"  resting on {understanding.characteristics.rests_on}")

    for ruling in understanding.characteristics.basis:
        print(f"  {ruling.concluded}")

    print()

    if understanding.contingencies:
        print("what could change this conclusion:")

        for contingency in understanding.contingencies:
            print(f"  {contingency.claim} — {contingency.agreement.stated_majority()}")

            standing = (
                "consumed as settled"
                if contingency.consumed
                else "excluded — no answer carries a strict majority"
            )
            print(f"    as it stands ({standing}): {contingency.as_it_stands}")

            for alternative in contingency.alternatives:
                changed = (
                    "unchanged"
                    if alternative.concludes == contingency.as_it_stands
                    else f"would conclude: {alternative.concludes}"
                )
                print(f"    {alternative.given}× {alternative.answer} → {changed}")

            if not contingency.could_change_conclusion:
                print(
                    "    every observed answer leaves the conclusion "
                    "unchanged — the gap does not bear on it"
                )

        print()

    print("not established:")

    if not understanding.not_established:
        print("  none")
        return

    for gap in understanding.not_established:
        what = "size" if gap.dimension.value == "size" else "way of earning"
        print(f"  {gap.segment} — {what}")
        print(f"    {gap.because}")


async def run(symbol: str) -> int:
    return await UnderstandingCommand().run(symbol)
