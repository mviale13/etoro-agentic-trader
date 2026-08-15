from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.decision_rules import PE_BANDS
from app.domain.finding import Finding
from app.domain.valuation_comparison import (
    AbsentComparison,
    ValuationObservation,
)
from app.domain.value_signal import ValueSignal


class ValueSignalService:
    #: The bands of `pe-bands@1`. Named so the provenance guard can
    #: fingerprint them: moving one under an unchanged rule version is a
    #: test failure, not a quiet edit.
    PE_CHEAP_BELOW = 18
    PE_FAIR_BELOW = 28

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
                # Carried out with the signal so the score's basis cannot
                # re-promise what this sentence just declined to: without
                # it, the builder explained the fund's UNKNOWN as figures
                # that "could not be read", which will never read.
                basis=(
                    (
                        f"Valuation is not scored: a {asset_class.noun} has "
                        "no earnings to be priced against, so there is no "
                        "figure a price could be judged by."
                    )
                    if no_earnings and asset_class is not None
                    else None
                ),
            )

        pe = company.forward_pe

        # The measured fact, and the honest state of comparison: a
        # multiple is held and no benchmark is. The finding each exit
        # below carries is the observation alone, with a neutral sense —
        # the sentences these replaced claimed a "historical market
        # average" this platform has never held, and read favourable or
        # adverse on the strength of that claim (VALUATION_AUTHORITY.md).
        # The band itself survives unchanged underneath, as what it
        # always was: pe-bands@1, a house policy the decision machine
        # still runs on, no longer dressed as an evidenced comparison.
        observation = ValuationObservation(
            metric="forward_pe",
            label="Forward P/E",
            value=pe,
            reading=company.fundamentals_reading,
        )

        comparison = AbsentComparison(
            observation=observation,
            because=(
                "No valuation benchmark is held for this security. The "
                "bands in pe-bands@1 are this platform's own policy "
                "constants, and a constant in code is not a benchmark "
                "in evidence."
            ),
        )

        finding = (Finding.neutral(comparison.stated),)

        if pe < self.PE_CHEAP_BELOW:
            return ValueSignal(
                valuation="CHEAP",
                confidence=90,
                rule=PE_BANDS,
                evidence=finding,
                observation=observation,
                comparison=comparison,
            )

        if pe < self.PE_FAIR_BELOW:
            return ValueSignal(
                valuation="FAIR",
                confidence=80,
                rule=PE_BANDS,
                evidence=finding,
                observation=observation,
                comparison=comparison,
            )

        return ValueSignal(
            valuation="EXPENSIVE",
            confidence=85,
            rule=PE_BANDS,
            evidence=finding,
            observation=observation,
            comparison=comparison,
        )
