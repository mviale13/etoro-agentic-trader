"""The financial analysts, reading established facts instead of a provider.

The point of the whole statement acquisition, arriving where an investor
can see it: the same four questions — is this profitable, is it growing,
is the balance sheet sound, does it generate cash — answered from figures
this platform read out of the filing, checked against the cells they sit
in, and settled across repeated readings.

**The two routes never blend.** A filing-grade analyst reads
`FinancialUnderstanding` and nothing else; the provider-fed analysts in
this package read `CompanyFacts` and nothing else. Where a filing
establishes no figure, this route reports the gap in the filing's own
words — it never reaches for the provider's number to fill it. That is
the Yahoo boundary as a rule of construction rather than a preference:

> A secondary restatement of a readable primary source is inadmissible
> in any assessment's basis — the label does not launder the copy.

So this is not a replacement switch to be thrown. It is the second route,
which outgrows the first one authoritative case at a time, exactly as the
grounded playbook selector outgrew the industry one.

**The rule tables are not duplicated.** Scoring and verdicts stay in the
provider-fed analysts, which own them, and are delegated to from here.
What differs between the routes is only what feeds them and what an
absence says — which is the whole of the difference that matters.

One question is deliberately *unanswered* by this route: leverage. The
balance-sheet rule table scores debt-to-equity against thresholds at 0.30
and 0.60, and what a filer prints as a line of its balance sheet is
*total liabilities*, a larger and different quantity — JPMorgan's is
about 11. Scoring one against the other's thresholds would mark every
bank as catastrophically levered on a number nothing checked. So
`LIABILITIES_TO_EQUITY` is established, reported, and left unscored until
a rule table exists that is about it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.analysts.analyst import Analyst
from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.analysts.cash_flow_analyst import CashFlowAnalyst, money
from app.analysts.growth_analyst import GrowthAnalyst
from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.balance_sheet_opinion import BalanceSheetOpinion, BalanceSheetVerdict
from app.domain.cash_flow_opinion import CashFlowOpinion, CashFlowVerdict
from app.domain.company_facts import CompanyFacts
from app.domain.financial_understanding import (
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
    MeasureUnit,
)
from app.domain.growth_opinion import GrowthOpinion, GrowthVerdict
from app.domain.opinion import Opinion
from app.domain.profitability_opinion import ProfitabilityOpinion, ProfitabilityVerdict


def stated_value(established: EstablishedMeasure) -> str:
    """One measure's number, read the way its unit is read.

    A currency measure is stated at the scale its caption gives rather
    than rescaled into dollars. The filer printed "182,447" under "(in
    millions)", and turning that into "$182.4K" — which is what a
    dollar formatter does to it — would be this platform inventing a
    scale nobody wrote down.
    """

    if established.value is None:
        return "not established"

    if established.unit is MeasureUnit.FRACTION:
        return f"{established.value:.1%}"

    if established.unit is MeasureUnit.MULTIPLE:
        return f"{established.value:.2f}x"

    caption = established.basis[0].caption if established.basis else ""

    return f"{established.value:,.0f} {caption}".strip()


class FilingAnalyst[OpinionT: Opinion[Any]](Analyst[FinancialUnderstanding, OpinionT]):
    """One analyst's question, answered from established filing facts.

    Generic over the opinion rather than written four times, because
    what varies between the four is only which measures they read and
    which opinion they build. Everything that makes an answer an answer
    — the thresholds, the verdict bands — is delegated to the analyst
    that owns it, so there is exactly one rule table per question and
    this route cannot drift away from the other one.
    """

    def __init__(
        self,
        rules: Analyst[CompanyFacts, OpinionT],
        measures: tuple[FinancialMeasure, ...],
        unknown: Callable[[tuple[str, ...]], OpinionT],
    ) -> None:
        self._rules = rules
        self._measures = measures
        self._unknown = unknown

    @property
    def expected_observation_count(self) -> int:
        """Full confidence is every measure this analyst reads."""

        return len(self._measures)

    def observations(
        self,
        subject: FinancialUnderstanding,
    ) -> tuple[AnalystObservation, ...]:
        """Only what the filing established, each carrying its evidence."""

        observations = []

        for name in self._measures:
            established = subject.of(name)

            if established is None or not established.is_established:
                continue

            assert established.value is not None

            observations.append(
                AnalystObservation(
                    key=name.value,
                    label=established.label,
                    value=established.value,
                    stated=(
                        f"{established.label} is {stated_value(established)} — "
                        f"{established.stated}."
                    ),
                )
            )

        return tuple(observations)

    def score_observation(self, observation: AnalystObservation) -> int:
        """The owning analyst's threshold, applied to a filing-grade figure."""

        return self._rules.score_observation(observation)

    def uncertainty(self, subject: FinancialUnderstanding) -> tuple[str, ...]:
        """Every measure this analyst reads that the filing did not establish.

        In the filing's own words, and that is the difference this route
        exists to make. "Gross margin data is unavailable" says nothing
        an investor can act on; "the income statement prints no gross
        profit line" says which fact is missing and why, and whether it
        is a fact about the company or about the reading.
        """

        gaps = []

        for name in self._measures:
            established = subject.of(name)

            if established is None:
                gaps.append(f"{name.value} was not measured.")
            elif not established.is_established and established.absent_because:
                gaps.append(established.absent_because)

        return tuple(gaps)

    def build_opinion(
        self,
        *,
        score: int,
        confidence: float,
        evidence: tuple[str, ...],
        uncertainty: tuple[str, ...],
    ) -> OpinionT:
        return self._rules.build_opinion(
            score=score,
            confidence=confidence,
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def unknown_opinion(self, subject: FinancialUnderstanding) -> OpinionT:
        """Nothing established is an answer, and it says what is missing."""

        return self._unknown(self.uncertainty(subject))

    @staticmethod
    def format_evidence(observation: AnalystObservation) -> str:
        """The measure and the cells it was computed from, in one line."""

        if observation.stated:
            return observation.stated

        return f"{observation.label} is {money(observation.value)}."


def filing_profitability() -> FilingAnalyst[ProfitabilityOpinion]:
    """Margins, from the income statement's own lines."""

    return FilingAnalyst(
        rules=ProfitabilityAnalyst(),
        measures=(
            FinancialMeasure.GROSS_MARGIN,
            FinancialMeasure.OPERATING_MARGIN,
            FinancialMeasure.NET_MARGIN,
        ),
        unknown=lambda gaps: ProfitabilityOpinion(
            score=50,
            confidence=0.0,
            verdict=ProfitabilityVerdict.UNKNOWN,
            evidence=(),
            uncertainty=gaps,
        ),
    )


def filing_growth() -> FilingAnalyst[GrowthOpinion]:
    """Growth, measured along rows this platform had already read."""

    return FilingAnalyst(
        rules=GrowthAnalyst(),
        measures=(
            FinancialMeasure.REVENUE_GROWTH,
            FinancialMeasure.EARNINGS_GROWTH,
        ),
        unknown=lambda gaps: GrowthOpinion(
            score=50,
            confidence=0.0,
            verdict=GrowthVerdict.UNKNOWN,
            evidence=(),
            uncertainty=gaps,
        ),
    )


def filing_balance_sheet() -> FilingAnalyst[BalanceSheetOpinion]:
    """Liquidity only — see this module's docstring on leverage."""

    return FilingAnalyst(
        rules=BalanceSheetAnalyst(),
        measures=(FinancialMeasure.CURRENT_RATIO,),
        unknown=lambda gaps: BalanceSheetOpinion(
            score=50,
            confidence=0.0,
            verdict=BalanceSheetVerdict.UNKNOWN,
            evidence=(),
            uncertainty=gaps,
        ),
    )


def filing_cash_flow() -> FilingAnalyst[CashFlowOpinion]:
    """Cash generated and cash left after the plant was paid for."""

    return FilingAnalyst(
        rules=CashFlowAnalyst(),
        measures=(
            FinancialMeasure.OPERATING_CASH_FLOW,
            FinancialMeasure.FREE_CASH_FLOW,
        ),
        unknown=lambda gaps: CashFlowOpinion(
            score=50,
            confidence=0.0,
            verdict=CashFlowVerdict.UNKNOWN,
            evidence=(),
            uncertainty=gaps,
        ),
    )
