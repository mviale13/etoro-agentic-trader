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
    #: The bands of `pe-bands@2`. Named so the provenance guard can
    #: fingerprint them: moving one under an unchanged rule version is a
    #: test failure, not a quiet edit.
    PE_CHEAP_BELOW = 18
    PE_FAIR_BELOW = 28

    #: The floor beneath which a price-to-earnings ratio measures
    #: nothing. **Not a band and not a threshold anyone chose** — it is
    #: where the arithmetic stops meaning what its name says. A P/E is a
    #: price divided by earnings; at or below zero the denominator is
    #: not earnings the price is being paid for, so a small negative
    #: number is not a low multiple and a large negative one is not a
    #: high multiple. Both say the same thing — this company is expected
    #: to lose money — and no multiple describes it.
    #:
    #: The measured defect (`SECURITY_VOLATILITY_DECISION_ROLE.md`,
    #: Finding 5): LUNR's forward P/E of **−328** satisfied `pe < 18`
    #: and banded **CHEAP at confidence 90**, the strongest valuation
    #: reading this platform can produce. The volatility veto was
    #: hiding it, and the owner's ruling of 2026-08-21 makes removing it
    #: a prerequisite of removing the veto.
    PE_MEASURABLE_ABOVE = 0.0

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
                # Not a gap in the evidence: a token or a fund has no
                # earnings to be priced against, so this question leaves
                # the decision's expected set rather than counting
                # against its coverage.
                applicable=not no_earnings,
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

        if pe <= self.PE_MEASURABLE_ABOVE:
            # Measured, and unbandable. The figure is preserved exactly
            # as the provider reported it — it is evidence about the
            # company, and a reader is entitled to see the number that
            # could not be interpreted. What is withheld is the
            # *meaning*: no band, and therefore no valuation score, so
            # the question leaves the answered set and lowers the
            # decision's coverage instead of scoring 80 for it.
            #
            # UNKNOWN and not `applicable=False`: the question applies.
            # This is a company with earnings, and they are negative —
            # unlike a fund or a token, where there are no earnings for
            # a price to be judged against and the question never
            # arises. Collapsing the two would tell an investor that a
            # loss-making company is the same kind of thing as a bond
            # ETF.
            #
            # And no substitute: nothing here reaches for price-to-book,
            # price-to-sales or a peer multiple. This platform holds one
            # unaudited multiple at a date (`VALUATION_AUTHORITY.md`),
            # and answering a question it cannot answer with a different
            # question it also cannot answer is not an improvement.
            return ValueSignal(
                valuation="UNKNOWN",
                confidence=20,
                # The rule that refused the band is the rule that owns
                # the band — identity, never endorsement.
                rule=PE_BANDS,
                evidence=finding,
                observation=observation,
                comparison=comparison,
                basis=(
                    f"Valuation is not scored: the forward P/E is {pe:.1f}, "
                    "so earnings-based valuation is not measurable through "
                    "P/E for this company. The figure is reported as read "
                    "and no other valuation method stands in for it."
                ),
            )

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
