"""Investment Committee."""

from __future__ import annotations

from app.application.committees.opinion_builder import Input, build
from app.brain import Brain
from app.domain.committee.opinion import (
    CommitteeOpinion,
    Uncertainty,
    UncertaintyKind,
)
from app.domain.finding import Dimension, FindingLedger

#: The readings this committee speaks for: what the business is worth
#: paying for. Risk is deliberately not here — it is another
#: committee's remit, and a committee that weighed everything would
#: leave the Executive layer nothing to adjudicate between.
REMIT = frozenset(
    {
        Dimension.QUALITY,
        Dimension.VALUATION,
        Dimension.MOMENTUM,
        Dimension.RESEARCH,
    }
)


class InvestmentCommittee:
    """
    Reviews whether this security is an attractive investment.

    It used to review only the portfolio and the market, which are the
    same whichever security is being judged, so its opinion was
    identical under every symbol and told the Artificial CIO nothing
    about the case in front of it. Then it weighed the security's own
    verdict at 60% against that context — better, and still a score.

    It now states a position over the findings in its remit and shows
    them. The portfolio and the market have left this object entirely:
    they are the conditions a security would be bought into, they are
    weighed where conditions belong, and a committee that folded them
    into its own view was reporting the account's health as an opinion
    about a company.
    """

    def review(
        self,
        brain: Brain,
        symbol: str,
        findings: FindingLedger,
    ) -> CommitteeOpinion:

        company = brain.security_evidence(symbol)

        if company is None:
            return build(
                committee="Investment Committee",
                remit=REMIT,
                ledger=findings,
                abstain_because=(
                    f"No security-level evidence is available for {symbol}, so "
                    "the Investment Committee takes no position. That is an "
                    "abstention, not a neutral view of the company."
                ),
            )

        signals = company.signals

        return build(
            committee="Investment Committee",
            remit=REMIT,
            ledger=findings,
            # What this committee asks to have measured before it is
            # fully evidenced. Named individually so an unmeasured one
            # says which, rather than lowering a number nobody can
            # decompose.
            inputs=(
                Input(
                    name="business quality",
                    value=None if signals.quality.quality == "UNKNOWN" else 1,
                    absent_because=(
                        f"Business quality could not be read for {symbol}."
                    ),
                ),
                Input(
                    name="valuation",
                    value=None if signals.value.valuation == "UNKNOWN" else 1,
                    absent_because=(f"Valuation could not be read for {symbol}."),
                ),
            ),
            uncertainty=self._outside_knowledge(brain, symbol),
        )

    @staticmethod
    def _outside_knowledge(
        brain: Brain,
        symbol: str,
    ) -> tuple[Uncertainty, ...]:
        """Questions that will not be answered by looking harder.

        An asset with no company behind it has no business quality and
        no earnings to be priced against — ever. Reporting those as
        *missing* would send an investor back to wait for a measurement
        that is not coming, which is the same counterfeit as an
        estimated figure, told in the future tense.
        """

        asset_class = brain.asset_class_for(symbol)

        if asset_class is None or not asset_class.has_no_company:
            return ()

        return (
            Uncertainty(
                kind=UncertaintyKind.OUTSIDE_KNOWLEDGE,
                about=(
                    f"A {asset_class.noun} has no business quality and no "
                    "earnings to be valued against, so neither is a question "
                    "this committee can ever answer for it."
                ),
            ),
        )
