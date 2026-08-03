from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.finding import Finding
from app.domain.value_signal import ValueSignal


class ValueSignalService:
    def build(
        self,
        company: CompanyFacts,
        asset_class: AssetClass | None = None,
    ) -> ValueSignal:
        if company.forward_pe is None:
            # "Unavailable" reads as a gap a later cycle might close. For an
            # asset with no earnings there is nothing to become available.
            no_earnings = asset_class is not None and asset_class.has_no_company

            return ValueSignal(
                valuation="UNKNOWN",
                confidence=20,
                evidence=(
                    Finding.neutral(
                        f"A {asset_class.noun} has no earnings to be priced against."
                        if no_earnings and asset_class is not None
                        else "Forward P/E unavailable."
                    ),
                ),
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
