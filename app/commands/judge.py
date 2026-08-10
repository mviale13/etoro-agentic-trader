"""Convene the committee and record what it concluded. The explicit spend.

The write half of judgment history, and a separate verb for the same
reason `observe` is separate from `knowledge`: rendering must not
manufacture events. If judging wrote history, opening a surface would
append a judgment, and *"the committee has reviewed this eleven times"*
would be a count of page views wearing the language of review.

So this command is the only thing that writes. It runs the committee,
appends one event, and states what changed against the last comparable
judgment — which is already decided by code before it is printed.
"""

from __future__ import annotations

from app.domain.judgment_history import JudgmentChange
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.value_capture_committee import VERSION, ValueCaptureCommittee


class JudgeCommand:
    async def run(self, symbol: str | None = None) -> int:
        committee = ValueCaptureCommittee()
        history = JudgmentHistoryService()

        print(f"{VERSION.stated}")
        print(_wrap(VERSION.remit.question, "  "))
        print()

        assets = [symbol.upper().strip()] if symbol else _corpus()

        for asset in assets:
            await self._judge(committee, history, asset)

        print(
            _wrap(
                "Each judgment above is now part of an append-only record. "
                "Nothing rewrites it: a later committee appends, and a "
                "correction is a new judgment rather than an edit. Neither "
                "verdict is favourable or adverse and no transition between "
                "them is a recommendation.",
                "  ",
            )
        )

        return 0

    async def _judge(
        self,
        committee: ValueCaptureCommittee,
        history: JudgmentHistoryService,
        asset: str,
    ) -> None:
        judgment = await committee.judge(asset)

        # The evidence the committee was actually given, captured in the
        # same breath as the answer. Read later it would be different
        # evidence, and the whole separation of evidence movement from
        # judgment movement rests on knowing which produced which.
        evidence = committee.evidence(asset)

        record = history.record(judgment, VERSION, evidence)

        print(f"  {asset}")

        if record is None:
            print(
                _wrap(
                    "this exact judgment is already recorded, so nothing was appended",
                    "    ",
                )
            )
            print()
            return

        transition = history.against_history(record)

        print(_wrap(record.stated, "    "))
        print(f"    recorded: {record.record_id}")

        if transition.change is not JudgmentChange.FIRST_JUDGMENT:
            print(_wrap(f"since the last judgment: {transition.stated}", "    "))
        else:
            print(_wrap(f"this is {transition.change.stated}.", "    "))

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


async def run(symbol: str | None = None) -> int:
    return await JudgeCommand().run(symbol)
