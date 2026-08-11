"""What one committee judges, and the evidence it was allowed to see.

Read-only. It shows the three steps in order — is this question
meaningful here, is there eligible evidence, and what does the committee
conclude — because collapsing them is how a category error starts
looking like a finding.
"""

from __future__ import annotations

from app.domain.committee_judgment import JudgmentState
from app.domain.committee_protocol import Committee
from app.services.crypto_committees import committees


class CommitteeJudgmentCommand:
    async def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        assets = [symbol.upper().strip()] if symbol else _corpus()

        for committee in committees():
            contract = committee.contract

            print(f"{contract.stated}")
            print(_wrap(contract.question, "  "))
            print()

            for asset in assets:
                await self._render(committee, asset, evidence and bool(symbol))

        print(
            _wrap(
                "This committee answers one question and nothing else. It has "
                "no view on whether an asset is worth owning, and neither "
                "answer is favourable or adverse — a mechanism being "
                "evidenced is a structural fact, not a grade. No share is "
                "banded, because no threshold has been established.",
                "  ",
            )
        )

        return 0

    async def _render(
        self,
        committee: Committee,
        asset: str,
        evidence: bool,
    ) -> None:
        basis = committee.basis(asset)

        judgment = await committee.judge(asset)

        print(f"  {asset}")
        print(
            _wrap(
                f"applicability: {basis.applicability.value} — {basis.because}",
                "    ",
            )
        )

        held = committee.evidence(asset)

        print(f"    eligible evidence: {len(held)} finding(s)")

        if judgment.state is JudgmentState.JUDGED and judgment.verdict:
            confidence = judgment.confidence.stated if judgment.confidence else "—"

            print(_wrap(f"judgment: {judgment.verdict.stated}", "    "))
            print(f"    confidence: {confidence}")
            print(_wrap(f"“{judgment.because}”", "    "))
            print(f"    resting on: {', '.join(judgment.refs)}")
        elif judgment.state is JudgmentState.ABSTAINED:
            reason = judgment.abstained_because

            print(_wrap(f"abstained: {reason.stated if reason else ''}", "    "))
        else:
            print(_wrap(f"no judgment: {judgment.unavailable_because}", "    "))

        if evidence:
            for finding in held:
                print(_wrap(f"[{finding.ref}] {finding.stated}", "      "))
                print(f"        established by: {finding.established_by}")

        print()


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
    return await CommitteeJudgmentCommand().run(symbol, evidence)
