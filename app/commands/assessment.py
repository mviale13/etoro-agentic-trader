"""What MOVRvest can usefully tell an investor about an asset.

Read-only, deterministic, no model. It reads the evidence and the
recorded judgments and prints sentences.

**Every statement says how strongly it is held.** A figure the evidence
settles, a bound across estimates, a structural fact, something true
within a limit, something genuinely uncertain — all five are useful
information and the surface prints the shape beside each so a reader is
never left to guess which they are looking at.

There is no headline, no summary and no ordering by importance: deciding
which of an investor's questions matters most is the recommendation
layer, and it does not exist.
"""

from __future__ import annotations

from app.domain.investor_assessment import StatementShape
from app.services.investor_assessment_service import InvestorAssessmentService


class AssessmentCommand:
    async def run(self, symbol: str | None = None) -> int:
        service = InvestorAssessmentService()

        if symbol:
            self._asset(service, symbol.upper().strip())
        else:
            self._corpus(service)

        print()
        print(
            _wrap(
                "Each statement is as strong as the evidence beneath it and "
                "no stronger. A bound is reported as a bound rather than "
                "averaged into a figure nobody published, and a difference "
                "between sources is only called uncertain where the "
                "difference changes what can responsibly be said. Every "
                "reason a figure matters is quoted from the contract that "
                "established the question applies to this asset, and where "
                "none has, the measurement is shown without one. Nothing "
                "here is a recommendation, a score or a ranking.",
                "  ",
            )
        )

        return 0

    def _asset(self, service: InvestorAssessmentService, asset: str) -> None:
        assessment = service.for_asset(asset)

        print(f"{asset} — what can usefully be said")
        print()

        for statement in assessment.statements:
            print(f"  {statement.subject}  [{statement.shape.value}]")
            print(_wrap(statement.stated, "    "))

            if statement.qualification:
                print(_wrap(f"— {statement.qualification}", "    "))

            if statement.uncertainty:
                print(_wrap(f"still open: {statement.uncertainty}", "    "))

            for meaning in statement.why_it_matters:
                print(_wrap(f"why it matters: {meaning.stated}", "    "))
                print(_wrap(f"({meaning.question} — {meaning.licensed_by})", "      "))

            if statement.interpretation_withheld:
                print(
                    _wrap(
                        "what it means for this asset is not established here: "
                        + statement.interpretation_withheld,
                        "    ",
                    )
                )

            for value in statement.observed:
                print(f"      {value.source}: {value.value:,.4f} {value.unit}")

            print()

        if assessment.silent_about:
            print(
                _wrap(
                    "Nothing useful is held about: "
                    + ", ".join(assessment.silent_about)
                    + ".",
                    "  ",
                )
            )

    def _corpus(self, service: InvestorAssessmentService) -> None:
        print("What can usefully be said — the corpus")
        print()
        print(f"  {'asset':8}{'statements':>11}  by shape")
        print("  " + "-" * 62)

        for asset in _corpus():
            assessment = service.for_asset(asset)

            counts: dict[StatementShape, int] = {}

            for statement in assessment.statements:
                counts[statement.shape] = counts.get(statement.shape, 0) + 1

            shapes = ", ".join(
                f"{shape.value} x{count}" for shape, count in sorted(counts.items())
            )

            print(f"  {asset:8}{len(assessment.statements):>11}  {shapes or '—'}")


def _corpus() -> list[str]:
    from app.domain.crypto_archetype import ASSIGNMENTS

    return sorted(ASSIGNMENTS)


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + "  "

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return await AssessmentCommand().run(symbol)
