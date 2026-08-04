from app.domain.brain_snapshot import BrainSnapshot


class BrainSummaryService:
    def summarize(
        self,
        brain: BrainSnapshot,
    ) -> str:
        return (
            f"{brain.observation.title}. "
            f"Investor understanding: "
            f"{brain.investor_dna.confidence}%."
        )
