from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.value_signal import ValueSignal


class ValueSignalService:
    def build(
        self,
        company: CompanyFacts,
    ) -> ValueSignal:
        if company.forward_pe is None:
            return ValueSignal(
                valuation="UNKNOWN",
                confidence=20,
                evidence=(Finding.neutral("Forward P/E unavailable."),),
            )

        pe = company.forward_pe

        if pe < 18:
            return ValueSignal(
                valuation="CHEAP",
                confidence=90,
                evidence=(
                    Finding.favourable("Forward P/E below historical market average."),
                ),
            )

        if pe < 28:
            return ValueSignal(
                valuation="FAIR",
                confidence=80,
                evidence=(Finding.neutral("Forward P/E within a reasonable range."),),
            )

        return ValueSignal(
            valuation="EXPENSIVE",
            confidence=85,
            evidence=(Finding.adverse("Forward P/E above historical market average."),),
        )
