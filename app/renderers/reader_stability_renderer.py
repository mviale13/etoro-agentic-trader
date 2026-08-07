"""Present what repeated readings of one document agreed and disagreed on.

Developer-level, like `movrvest knowledge`, and for the same reason: it
reports on the platform rather than on a company, and an investor asked
to read it would learn nothing about an investment.

Every disagreement is printed in full. A stability figure alone would be
the same mistake this platform spent several slices removing elsewhere —
a two-significant-figure summary standing in front of the evidence, with
no way to see whether 8 of 10 means two readings that missed one word or
two readings that described a different business.
"""

from __future__ import annotations

from app.domain.reader_stability import Agreement, ReaderStability


class ReaderStabilityRenderer:
    """One document's calibration, answers and disagreements included."""

    @staticmethod
    def render(stability: ReaderStability) -> None:
        print(f"{stability.symbol} — {stability.readings} independent readings")
        print()
        print(stability.source)
        print(f"read: {stability.reader}")
        print()
        print(
            f"completed: {stability.read} of {stability.readings} "
            f"{_share(stability.completed)}"
        )

        if not stability.refusals.settled or stability.refusals.readings:
            for answer in stability.refusals.answers:
                print(f"  refused {answer.given}×: {answer.stated}")

        print()

        if not stability.read:
            print(
                "No reading of this document produced knowledge, so there is "
                "nothing to compare. That is the measurement."
            )
            return

        _agreement("segments named", stability.identity)

        for segment in stability.segments:
            print()
            print(f"  {segment.name} — named in {segment.named_in} of {stability.read}")

            for measured in (
                segment.size,
                segment.earning,
                segment.described,
                segment.description,
            ):
                _agreement(measured.question, measured, indent="    ")

        print()
        _agreement("archetype", stability.archetype)

        print()
        print(
            "Agreement observed over these readings, on this document. It is "
            "not the chance that a further reading agrees, and nothing here "
            "reports one."
        )


def _agreement(named: str, measured: Agreement, indent: str = "") -> None:
    """One question, its winning answer, and every answer that lost."""

    if measured.modal is None:
        print(f"{indent}{named}: no reading answered")
        return

    print(
        f"{indent}{named}: {measured.agreeing} of {measured.readings} "
        f"{_share(measured.stability)}"
    )

    for answer in measured.answers:
        print(f"{indent}  {answer.given}× {answer.stated}")


def _share(measured: float | None) -> str:
    """A share as an investor reads it, or an honest blank."""

    return "" if measured is None else f"({measured:.0%})"
