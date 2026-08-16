"""Direction is what the evidence says; authority is whether we may act.

`decision-authority@1`. The two gates are independent and neither is
expressible as the other: relative coverage protects against a signal
being deleted, absolute breadth protects against an expected set so
small that one signal is "full" coverage by construction.
"""

from __future__ import annotations

import itertools

import pytest

from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.decision_participation import (
    AuthorityGap,
    SignalParticipation,
)
from app.domain.finding import Finding
from app.domain.momentum_signal import MomentumSignal
from app.domain.quality_signal import QualitySignal
from app.domain.value_signal import ValueSignal
from app.services.company_committee_service import CompanyCommitteeService

DECISIVENESS = {"HOLD": 0, "BUY": 1, "SELL": 1}

VALUES = ("CHEAP", "FAIR", "EXPENSIVE", "UNKNOWN")
QUALITIES = ("HIGH", "MEDIUM", "LOW", "UNKNOWN")
TRENDS = ("BULLISH", "NEUTRAL", "BEARISH", "UNKNOWN")


def _evaluate(
    value: str = "UNKNOWN",
    quality: str = "UNKNOWN",
    momentum: str = "UNKNOWN",
    *,
    value_applicable: bool = True,
    quality_applicable: bool = True,
    momentum_applicable: bool = True,
) -> CompanyRecommendation:
    note = (Finding.neutral("reading"),)

    return CompanyCommitteeService().evaluate(
        "TEST",
        CompanySignals(
            value=ValueSignal(
                valuation=value,
                confidence=50,
                evidence=note,
                applicable=value_applicable,
            ),
            quality=QualitySignal(
                quality=quality,
                confidence=50,
                evidence=note,
                applicable=quality_applicable,
            ),
            momentum=MomentumSignal(
                trend=momentum,
                strength="MODERATE",
                confidence=50,
                evidence=note,
                applicable=momentum_applicable,
            ),
        ),
    )


class TestParticipation:
    def test_a_genuine_neutral_participates(self) -> None:
        """A middle band is a reading, and counts fully towards coverage."""

        outcome = _evaluate("FAIR", "MEDIUM", "NEUTRAL")

        assert outcome.authority is not None
        assert outcome.authority.participating_count == 3
        assert outcome.authority.relative_coverage == 1.0
        assert outcome.authority.may_act

    def test_unknown_does_not_participate(self) -> None:
        outcome = _evaluate("CHEAP", "HIGH", "UNKNOWN")

        assert outcome.authority is not None
        assert outcome.authority.participating_count == 2

        momentum = next(s for s in outcome.authority.standings if s.name == "momentum")

        assert momentum.participation is SignalParticipation.EXPECTED_ABSENT
        assert momentum.direction is None

    def test_unknown_is_not_neutral(self) -> None:
        """The distinction the old kernel could not draw at all."""

        neutral = _evaluate("FAIR", "MEDIUM", "NEUTRAL")
        unknown = _evaluate("FAIR", "MEDIUM", "UNKNOWN")

        assert neutral.authority is not None and unknown.authority is not None
        assert neutral.authority.participating_count == 3
        assert unknown.authority.participating_count == 2
        assert neutral.authority.may_act
        assert not unknown.authority.may_act

    def test_not_applicable_leaves_the_expected_set(self) -> None:
        """It must not lower relative coverage."""

        outcome = _evaluate(
            "UNKNOWN",
            "UNKNOWN",
            "BULLISH",
            value_applicable=False,
            quality_applicable=False,
        )

        assert outcome.authority is not None
        assert outcome.authority.relative_coverage == 1.0
        assert len(outcome.authority.applicable) == 1

    def test_an_expected_absence_does_lower_coverage(self) -> None:
        outcome = _evaluate("CHEAP", "UNKNOWN", "BULLISH")

        assert outcome.authority is not None
        assert outcome.authority.relative_coverage < 1.0
        assert AuthorityGap.RELATIVE_COVERAGE in outcome.authority.gaps


class TestTheTwoGates:
    def test_a_fund_with_only_momentum_is_never_actionable(self) -> None:
        """#138's trap: full relative coverage over a one-signal set."""

        outcome = _evaluate(
            "UNKNOWN",
            "UNKNOWN",
            "BULLISH",
            value_applicable=False,
            quality_applicable=False,
        )

        assert outcome.authority is not None
        assert outcome.authority.relative_coverage == 1.0
        assert outcome.authority.gaps == (AuthorityGap.ABSOLUTE_BREADTH,)
        assert outcome.recommendation == "HOLD"

    def test_two_fully_covered_signals_are_eligible(self) -> None:
        """Breadth of two with nothing else applicable: normal evaluation."""

        outcome = _evaluate(
            "CHEAP",
            "UNKNOWN",
            "BULLISH",
            quality_applicable=False,
        )

        assert outcome.authority is not None
        assert outcome.authority.may_act
        assert outcome.direction == "BUY"
        assert outcome.recommendation == "BUY"

    def test_three_applicable_with_one_unknown_is_not_actionable(self) -> None:
        outcome = _evaluate("CHEAP", "UNKNOWN", "BULLISH")

        assert outcome.direction == "BUY"
        assert outcome.recommendation == "HOLD"
        assert outcome.lean_without_authority == "BUY"

    def test_the_gates_are_independent(self) -> None:
        """Neither is expressible as the other, and both can fail at once."""

        breadth_only = _evaluate(
            "UNKNOWN",
            "UNKNOWN",
            "BULLISH",
            value_applicable=False,
            quality_applicable=False,
        )
        coverage_only = _evaluate("CHEAP", "UNKNOWN", "BULLISH")
        both = _evaluate("UNKNOWN", "UNKNOWN", "BULLISH")

        assert breadth_only.authority is not None
        assert coverage_only.authority is not None
        assert both.authority is not None

        assert breadth_only.authority.gaps == (AuthorityGap.ABSOLUTE_BREADTH,)
        assert coverage_only.authority.gaps == (AuthorityGap.RELATIVE_COVERAGE,)
        assert set(both.authority.gaps) == {
            AuthorityGap.RELATIVE_COVERAGE,
            AuthorityGap.ABSOLUTE_BREADTH,
        }


class TestTheLeanSurvives:
    def test_a_withheld_direction_is_preserved_not_flattened(self) -> None:
        outcome = _evaluate("EXPENSIVE", "UNKNOWN", "BEARISH")

        assert outcome.direction == "SELL"
        assert outcome.recommendation == "HOLD"
        assert outcome.lean_without_authority == "SELL"

    def test_an_actionable_call_has_no_withheld_lean(self) -> None:
        outcome = _evaluate("CHEAP", "HIGH", "BULLISH")

        assert outcome.recommendation == "BUY"
        assert outcome.lean_without_authority is None

    def test_a_genuine_hold_is_not_a_withheld_lean(self) -> None:
        """Equivocation and withheld conviction must stay distinct."""

        outcome = _evaluate("FAIR", "MEDIUM", "NEUTRAL")

        assert outcome.direction == "HOLD"
        assert outcome.recommendation == "HOLD"
        assert outcome.lean_without_authority is None


class TestWeightsAndThresholdsAreUntouched:
    def test_survivor_weights_are_not_renormalised(self) -> None:
        """Two favourable survivors must not be amplified to certainty.

        Renormalising would score this `+1.00`; the original weights
        score it `+0.65`. #138 measured that renormalising is what makes
        forgetting look bullish.
        """

        outcome = _evaluate("CHEAP", "UNKNOWN", "BULLISH")

        assert outcome.confidence == round(50 + 0.65 * 50)

    def test_the_constants_are_unchanged(self) -> None:
        assert CompanyCommitteeService.VALUE_WEIGHT == 0.40
        assert CompanyCommitteeService.QUALITY_WEIGHT == 0.35
        assert CompanyCommitteeService.MOMENTUM_WEIGHT == 0.25
        assert CompanyCommitteeService.BUY_THRESHOLD == 0.50
        assert CompanyCommitteeService.SELL_THRESHOLD == -0.50


class TestIgnoranceNonPromotion:
    """The property: forgetting may never make the platform more decisive."""

    @staticmethod
    def _reading(value: str, quality: str, momentum: str) -> str:
        return _evaluate(value, quality, momentum).recommendation

    def test_no_single_deletion_increases_decisiveness(self) -> None:
        """Exhaustive over every reading and every established signal."""

        violations = []

        for value, quality, momentum in itertools.product(VALUES, QUALITIES, TRENDS):
            before = self._reading(value, quality, momentum)

            for index, band in enumerate((value, quality, momentum)):
                if band == "UNKNOWN":
                    continue

                deleted = [value, quality, momentum]
                deleted[index] = "UNKNOWN"

                after = self._reading(*deleted)

                if DECISIVENESS[after] > DECISIVENESS[before]:
                    violations.append((value, quality, momentum, index, before, after))

        assert violations == []

    @pytest.mark.parametrize(
        ("value", "quality", "momentum"),
        list(itertools.product(VALUES, QUALITIES, TRENDS)),
    )
    def test_no_deletion_flips_a_decisive_call_to_its_opposite(
        self, value: str, quality: str, momentum: str
    ) -> None:
        """BUY→SELL and SELL→BUY are forbidden outright."""

        before = self._reading(value, quality, momentum)

        for index, band in enumerate((value, quality, momentum)):
            if band == "UNKNOWN":
                continue

            deleted = [value, quality, momentum]
            deleted[index] = "UNKNOWN"

            after = self._reading(*deleted)

            assert not (before == "BUY" and after == "SELL")
            assert not (before == "SELL" and after == "BUY")

    def test_softening_remains_permitted(self) -> None:
        """The invariant forbids hardening, not evidence-responsiveness.

        A design that could never soften would be retaining a
        conclusion after its evidence — which #138 measured as the
        reason the invariant had to be stated over decisiveness rather
        than over positivity.
        """

        before = self._reading("CHEAP", "HIGH", "BULLISH")
        after = self._reading("UNKNOWN", "HIGH", "BULLISH")

        assert before == "BUY"
        assert after == "HOLD"
