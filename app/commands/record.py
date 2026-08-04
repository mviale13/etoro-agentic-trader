"""Report what the Artificial CIO's own decisions have done since."""

from collections import Counter

from app.application.learning.decision_journal import DecisionJournal
from app.application.learning.decision_outcome_service import (
    DecisionOutcomeService,
)
from app.domain.decision_outcome import TrackRecord
from app.providers.yahoo_price_history import YahooPriceHistory
from app.repositories.json_event_repository import JsonEventRepository


class RecordCommand:
    async def run(self) -> int:
        record = await DecisionOutcomeService(
            journal=DecisionJournal(JsonEventRepository()),
            prices=YahooPriceHistory(),
        ).build()

        print()
        print("MOVRvest — decision track record")
        print("══════════════════════════════════════")
        print()

        self._render(record)

        return 0

    @staticmethod
    def _render(record: TrackRecord) -> None:
        scored = len(record.outcomes)
        calls = record.calls

        print(f"{'Decisions measured':<22}: {scored}")
        print(f"{'Of those, calls':<22}: {len(calls)}")
        print(f"{'Not yet measurable':<22}: {len(record.unscored)}")
        print()

        if record.hit_rate is None:
            # Not a modest way of saying zero. Below the minimum the
            # figure moves several points per decision, which would read
            # as a measurement of judgement and is arithmetic on a
            # handful of days.
            print(
                f"No hit rate: {TrackRecord.MINIMUM_CALLS} calls are needed "
                f"before one means anything, and {len(calls)} have been measured."
            )
        else:
            print(
                f"{'Hit rate':<22}: {record.hit_rate * 100:.0f}% "
                f"({record.agreed} of {len(calls)} calls)"
            )

        print()

        for outcome in sorted(
            record.outcomes,
            key=lambda item: item.change,
            reverse=True,
        ):
            agreed = outcome.moved_as_the_decision_implied

            verdict = (
                "not a call"
                if agreed is None
                else ("as decided" if agreed else "against the decision")
            )

            print(
                f"  {outcome.symbol:<10} {outcome.state.value:<12} "
                f"{outcome.change * 100:+7.1f}%  "
                f"{outcome.days_elapsed:>3}d  {verdict}"
            )

        if not record.unscored:
            return

        print()
        print("Not yet measurable")
        print("──────────────────────────────────────")

        # The reasons, not one line per decision: a young journal has the
        # same sentence sixty times, and the count is the information.
        for reason, count in Counter(
            item.reason for item in record.unscored
        ).most_common():
            print(f"  {count:>3} × {reason}")


async def run() -> int:
    return await RecordCommand().run()
