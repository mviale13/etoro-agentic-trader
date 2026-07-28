from app.domain.company_facts import CompanyFacts
from app.domain.value_signal import ValueSignal


class ValueSignalService:
    def build(
        self,
        company: CompanyFacts,
    ) -> ValueSignal:
        evidence: list[str] = []

        if company.forward_pe is None:
            return ValueSignal(
                valuation="UNKNOWN",
                confidence=20,
                evidence=("Forward P/E unavailable.",),
            )

        pe = company.forward_pe

        if pe < 18:
            evidence.append("Forward P/E below historical market average.")

            return ValueSignal(
                valuation="CHEAP",
                confidence=90,
                evidence=tuple(evidence),
            )

        if pe < 28:
            evidence.append("Forward P/E within a reasonable range.")

            return ValueSignal(
                valuation="FAIR",
                confidence=80,
                evidence=tuple(evidence),
            )

        evidence.append("Forward P/E above historical market average.")

        return ValueSignal(
            valuation="EXPENSIVE",
            confidence=85,
            evidence=tuple(evidence),
        )
