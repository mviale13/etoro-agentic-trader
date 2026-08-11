"""What every registered committee has concluded, side by side.

Read-only, no model, no fetch. It reads the judgment record and prints
it; it convenes nothing, so opening it can never manufacture a judgment
event.

**Side by side is not together.** With a symbol this prints each
committee's own question, conclusion, reasoning, confidence and
evidence as its own block, because the committees answer different
structural questions and two answers under one heading would invite a
reader to average them. Without a symbol it prints the corpus as a
grid — and the grid still names each column's question, because a
column header of *Supply Governance* alone tells a reader nothing about
what a cell means.

Nothing here totals, ranks, scores or agrees. There is no bottom row.
"""

from __future__ import annotations

from app.domain.committee_matrix import CommitteeAssessment
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.crypto_committees import CONTRACTS


class CommitteesCommand:
    async def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = CommitteeMatrixService()

        if symbol:
            self._dossier(service, symbol.upper().strip(), evidence)
        else:
            self._grid(service)

        print()
        print(
            _wrap(
                "Each committee answers its own question and nothing else. "
                "These are independent judgments placed beside one another, "
                "never combined: there is no overall verdict, no agreement "
                "between them, no score and no ranking, and two committees "
                "reaching answers of different shapes is the ordinary case "
                "rather than a conflict. Confidence is shown as each "
                "committee expresses it and is not comparable across them.",
                "  ",
            )
        )

        return 0

    # ── one asset, one block per committee ──────────────────────────

    def _dossier(
        self,
        service: CommitteeMatrixService,
        asset: str,
        evidence: bool,
    ) -> None:
        matrix = service.for_asset(asset)

        print(f"{asset} — what the committees have concluded")
        print()

        for cell in matrix.assessments:
            print(f"  {cell.committee.stated}")

            if cell.question:
                print(_wrap(f"question: {cell.question}", "    "))

            print(_wrap(f"conclusion: {cell.stated}", "    "))

            print(
                f"    confidence: {cell.confidence.stated if cell.confidence else '—'}"
            )

            print(
                f"    evidence: {cell.evidence_count} eligible finding(s)"
                + (f", cited {len(cell.refs)}" if cell.refs else "")
            )

            if not cell.is_current_contract and cell.comparability:
                print(_wrap(f"note: {cell.comparability.stated}", "    "))

            print(
                f"    recorded: {cell.judgments_recorded} judgment(s)"
                + (f", latest {cell.judged_at:%-d %B %Y}" if cell.judged_at else "")
            )

            if evidence:
                _render_basis(cell)

            print()

        for missing in matrix.unjudged:
            print(f"  {missing.committee.stated}")
            print(_wrap(f"question: {missing.question}", "    "))
            print(_wrap(f"conclusion: {missing.stated}", "    "))
            print()

    # ── the corpus, as a grid ───────────────────────────────────────

    def _grid(self, service: CommitteeMatrixService) -> None:
        print("What the committees have concluded — the corpus")
        print()

        for contract in CONTRACTS:
            print(f"  {contract.stated}")
            print(_wrap(contract.question, "    "))

        print()

        width = 34

        header = "  " + "asset".ljust(8)

        for contract in CONTRACTS:
            header += contract.name[:width].ljust(width + 2)

        print(header)
        print("  " + "-" * (8 + (width + 2) * len(CONTRACTS)))

        for asset in _corpus():
            matrix = service.for_asset(asset)

            row = "  " + asset.ljust(8)

            for contract in CONTRACTS:
                cell = matrix.for_committee(contract.key)

                row += _summary(cell)[:width].ljust(width + 2)

            print(row)


def _summary(cell: CommitteeAssessment | None) -> str:
    """One cell, in the shortest form that keeps its meaning.

    An unanswered cell shows *why* rather than a blank, because four
    different causes read as "no answer" across this corpus and a grid
    that printed them alike would be the flattening this layer exists to
    prevent.
    """

    if cell is None:
        return "not judged"

    if cell.is_answered and cell.verdict:
        return cell.verdict

    return cell.posture.value


def _render_basis(cell: CommitteeAssessment) -> None:
    """The committee's own reasoning and the refs it rests on."""

    if cell.because:
        print(_wrap(f"why: {cell.because}", "      "))

    if cell.unavailable_because:
        print(_wrap(f"why: {cell.unavailable_because}", "      "))

    if cell.refs:
        print(_wrap(f"resting on: {', '.join(cell.refs)}", "      "))

    if cell.economic_role:
        print(f"      economic role at judgment: {cell.economic_role}")


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


async def run(symbol: str | None = None, evidence: bool = False) -> int:
    return await CommitteesCommand().run(symbol, evidence)
