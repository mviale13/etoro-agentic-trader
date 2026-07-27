from app.domain.committee_outcome import CommitteeOutcome
from app.domain.reflection import Reflection


class ReflectionEngine:
    def reflect(
        self,
        outcome: CommitteeOutcome,
    ) -> Reflection:
        if outcome.successful:
            return Reflection(
                title="Successful Recommendation",
                summary=(
                    "The committee reached a decision that produced "
                    "a positive investment outcome."
                ),
            )

        return Reflection(
            title="Recommendation Review",
            summary=(
                "The recommendation did not achieve the expected "
                "result and should be reviewed."
            ),
        )
