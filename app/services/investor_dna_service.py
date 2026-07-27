from app.domain.investor_dna import InvestorDNA
from app.domain.memory_event import MemoryEvent


class InvestorDNAService:
    def analyze(
        self,
        events: list[MemoryEvent],
    ) -> InvestorDNA:
        confidence = min(len(events) * 5, 100)

        return InvestorDNA(
            confidence=confidence,
            prefers_quality=False,
            prefers_diversification=False,
            prefers_value=False,
            avoids_high_volatility=False,
        )
