"""How one bounded judgment has moved, and how far it may be trusted.

Read-only. It leads with coverage — how many judgments the record
actually holds — before any transition, for the journal's reason: a
count of judgments is not a duration of review, and a reader shown
*"unchanged"* without being shown *"across two judgments eleven days
apart"* has been told something firmer than the record supports.

Three things are kept visibly apart on every line, because collapsing
them is the defect this surface exists to prevent: what the committee
answered, how much observation stands beneath it, and what the evidence
did. Evidence moving under a steady answer is the ordinary case and is
printed as such.
"""

from __future__ import annotations

from app.domain.judgment_history import (
    JudgmentChange,
    StandingKind,
)
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.value_capture_committee import CONTRACT


class JudgmentHistoryCommand:
    async def run(self, symbol: str | None = None, evidence: bool = False) -> int:
        service = JudgmentHistoryService()

        print(f"{CONTRACT.stated}")
        print(_wrap(CONTRACT.question, "  "))
        print()

        assets = [symbol.upper().strip()] if symbol else _corpus()

        for asset in assets:
            self._render(service, asset, evidence and bool(symbol))

        print(
            _wrap(
                "A recorded judgment is what this committee concluded then. "
                "It is never restated as today's answer: where the current "
                "evidence cannot support running the committee, the record "
                "says so and the earlier answer stays in the past tense. A "
                "transition between two verdicts means exactly that "
                "transition — it is not a development, a change of view "
                "about the asset, or anything to act on.",
                "  ",
            )
        )

        return 0

    def _render(
        self,
        service: JudgmentHistoryService,
        asset: str,
        evidence: bool,
    ) -> None:
        print(f"  {asset}")

        coverage = service.coverage(asset, CONTRACT.key)

        print(_wrap(f"coverage: {coverage.stated}", "    "))

        records = service.history(asset, CONTRACT.key)

        if not records:
            print()
            return

        current = records[-1]

        standing = service.standing(current)

        print(_wrap(f"standing: {standing.stated}", "    "))

        if standing.kind is StandingKind.PREVIOUS_NOT_REFRESHED:
            print(
                _wrap(
                    "current answer: none — the line above is history, not a finding",
                    "    ",
                )
            )

        for transition in service.transitions(asset, CONTRACT.key):
            if transition.change is JudgmentChange.FIRST_JUDGMENT and len(records) > 1:
                continue

            print()
            print(
                f"    {transition.current.judged_at:%-d %B %Y} — "
                f"{transition.change.value}"
            )
            print(_wrap(transition.stated, "      "))

            if evidence:
                print(
                    f"        support: {transition.support.value} · "
                    f"evidence: {transition.evidence.value} · "
                    f"records: {', '.join(transition.record_ids)}"
                )

                if transition.current.refs:
                    print(
                        _wrap(
                            f"resting on: {', '.join(transition.current.refs)}",
                            "        ",
                        )
                    )

                if transition.current.unavailable_because:
                    print(
                        _wrap(
                            f"no judgment: {transition.current.unavailable_because}",
                            "        ",
                        )
                    )

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
    return await JudgmentHistoryCommand().run(symbol, evidence)
