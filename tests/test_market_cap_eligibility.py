"""A magnitude may be compared with a threshold only if it means something.

`market-cap-input-eligibility@1`. Momentum could admit an ASSUMED
translation because its output is a ratio, invariant under rescaling.
An absolute threshold comparison has no such protection, and these
tests pin both the bands that did not move and the gate that is new.
"""

from __future__ import annotations

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_translation import TranslationWarrant
from app.services.company_committee_service import CompanyCommitteeService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import (
    ELIGIBLE_MARKET_CAP_WARRANTS,
    QualitySignalService,
)
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService
from tests.conftest import admissible_market_cap

ABOVE = 50_000_000_000.0
BELOW = 2_000_000_000.0


def _facts(**overrides: object) -> CompanyFacts:
    base: dict[str, object] = {
        "instrument_id": 1,
        "symbol": "TEST",
        "name": "Test Co",
        "asset_type": "stock",
        "exchange": "4",
    }

    base.update(overrides)

    return CompanyFacts(**base)  # type: ignore[arg-type]


def _statements(signal: object) -> tuple[str, ...]:
    return tuple(finding.statement for finding in signal.evidence)  # type: ignore[attr-defined]


class TestTheBandsDidNotMove:
    """An admissible magnitude scores exactly as it always did."""

    def test_clearly_above_the_line_still_earns_the_point(self) -> None:
        signal = QualitySignalService().build(
            _facts(
                market_cap=ABOVE,
                market_cap_magnitude=admissible_market_cap(ABOVE),
                eps=4.0,
                dividend_yield=0.02,
            )
        )

        assert "Large-cap company." in _statements(signal)
        assert signal.earned == 3
        assert signal.available == 3
        assert signal.quality == "HIGH"

    def test_below_the_line_still_earns_no_point_and_is_still_counted(self) -> None:
        signal = QualitySignalService().build(
            _facts(
                market_cap=BELOW,
                market_cap_magnitude=admissible_market_cap(BELOW),
                eps=4.0,
                dividend_yield=0.02,
            )
        )

        assert "Small or mid-cap company." in _statements(signal)
        assert signal.earned == 2
        assert signal.available == 3

    @pytest.mark.parametrize(
        ("amount", "expected"),
        [
            (10_000_000_000.0, "Large-cap company."),
            (9_999_999_999.0, "Small or mid-cap company."),
        ],
    )
    def test_the_threshold_boundary_is_exactly_where_it_was(
        self, amount: float, expected: str
    ) -> None:
        signal = QualitySignalService().build(
            _facts(
                market_cap=amount,
                market_cap_magnitude=admissible_market_cap(amount),
            )
        )

        assert expected in _statements(signal)

    def test_the_threshold_constant_is_untouched(self) -> None:
        assert QualitySignalService.LARGE_CAP_THRESHOLD == 10_000_000_000


class TestThreeStatesNotTwo:
    """Not scorable is not zero, not small, and not neutral."""

    def test_an_inadmissible_magnitude_is_not_scored_at_all(self) -> None:
        signal = QualitySignalService().build(
            _facts(market_cap=ABOVE, eps=4.0, dividend_yield=0.02)
        )

        assert "Large-cap company." not in _statements(signal)
        assert "Small or mid-cap company." not in _statements(signal)
        assert signal.available == 2

    def test_a_numerically_huge_but_unjustified_magnitude_never_earns_a_point(
        self,
    ) -> None:
        """SPCX's shape: $1.75T that may not describe this instrument."""

        signal = QualitySignalService().build(
            _facts(market_cap=1_753_616_089_088.0, eps=4.0, dividend_yield=0.02)
        )

        assert "Large-cap company." not in _statements(signal)
        assert signal.earned == 2

    def test_a_sound_semantic_warrant_with_an_unresolved_unit_is_refused(self) -> None:
        """Right meaning, unknown denomination — still not comparable."""

        magnitude = MarketCapMagnitude.measured(
            ABOVE,
            warrant=TranslationWarrant.VERIFIED,
            currency=None,
            currency_is_assumed=True,
        )

        assert not magnitude.admissible_for_threshold(ELIGIBLE_MARKET_CAP_WARRANTS)

        signal = QualitySignalService().build(
            _facts(market_cap=ABOVE, market_cap_magnitude=magnitude, eps=4.0)
        )

        assert "Large-cap company." not in _statements(signal)

    def test_an_assumed_currency_is_not_an_established_one(self) -> None:
        magnitude = MarketCapMagnitude.measured(
            ABOVE,
            warrant=TranslationWarrant.VERIFIED,
            currency="USD",
            currency_is_assumed=True,
        )

        assert not magnitude.denomination_established
        assert not magnitude.admissible_for_threshold(ELIGIBLE_MARKET_CAP_WARRANTS)

    def test_the_refusal_names_the_crossing_not_the_company(self) -> None:
        magnitude = MarketCapMagnitude.measured(
            ABOVE, warrant=TranslationWarrant.ASSUMED
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS)

        assert "cannot be compared" in refusal
        assert "small" not in refusal.lower()

    def test_an_absent_magnitude_is_still_absent(self) -> None:
        magnitude = MarketCapMagnitude.unmeasured(
            ClaimAbsence.PROVIDER_UNAVAILABLE,
            warrant=TranslationWarrant.VERIFIED,
        )

        assert not magnitude.admissible_for_threshold(ELIGIBLE_MARKET_CAP_WARRANTS)
        assert "unavailable" in magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS)


class TestEligibilityIsMembership:
    def test_the_membership_is_enumerated_and_excludes_assumed(self) -> None:
        assert ELIGIBLE_MARKET_CAP_WARRANTS == frozenset(
            {TranslationWarrant.VERIFIED, TranslationWarrant.VALIDATED}
        )

        assert TranslationWarrant.ASSUMED not in ELIGIBLE_MARKET_CAP_WARRANTS
        assert TranslationWarrant.DECLARED not in ELIGIBLE_MARKET_CAP_WARRANTS
        assert TranslationWarrant.UNKNOWN not in ELIGIBLE_MARKET_CAP_WARRANTS

    @pytest.mark.parametrize(
        "warrant",
        [TranslationWarrant.VERIFIED, TranslationWarrant.VALIDATED],
    )
    def test_every_admitted_warrant_scores(self, warrant: TranslationWarrant) -> None:
        magnitude = MarketCapMagnitude.measured(
            ABOVE, warrant=warrant, currency="USD", currency_is_assumed=False
        )

        signal = QualitySignalService().build(
            _facts(market_cap=ABOVE, market_cap_magnitude=magnitude)
        )

        assert "Large-cap company." in _statements(signal)

    def test_eligibility_is_not_representable_as_a_band_change(self) -> None:
        """Two rules, two fingerprints — the bands cannot absorb this.

        The membership lives on the eligibility rule and the threshold
        on the quality rule. A reviewer reading `provider-quality@1`
        sees an unchanged ruler, which is the truth.
        """

        from app.domain.decision_rules import (
            MARKET_CAP_INPUT_ELIGIBILITY,
            PROVIDER_QUALITY,
        )

        assert MARKET_CAP_INPUT_ELIGIBILITY.key != PROVIDER_QUALITY.key
        assert PROVIDER_QUALITY.version == 1
        assert MARKET_CAP_INPUT_ELIGIBILITY.version == 1


class TestTheDecisionRegression:
    """An inadmissible magnitude cannot carry a case over a boundary."""

    @staticmethod
    def _recommendation(facts: CompanyFacts) -> str:
        signals = CompanySignals(
            value=ValueSignalService().build(facts, AssetClass.STOCK),
            quality=QualitySignalService().build(facts, AssetClass.STOCK),
            momentum=MomentumSignalService().build(facts),
            risk=RiskSignalService().build(facts),
        )

        return CompanyCommitteeService().evaluate("TEST", signals).recommendation

    def test_the_point_that_carries_a_case_must_be_earned(self) -> None:
        """The causal pin, with the surrounding inputs manufactured.

        When this pin was written the inadmissible case produced a
        SELL, and that SELL was itself the defect `quality-authority@1`
        later removed: an incomplete question set was banding LOW and
        voting adverse. The pin now asserts the stronger property it
        was always reaching for — **an inadmissible magnitude cannot
        carry a case in either direction**. Admissible, the company is
        judged and holds; inadmissible, Quality withholds its band, the
        vote loses coverage, and nothing is issued.
        """

        shared: dict[str, object] = {
            "forward_pe": 40.0,
            "eps": 4.0,
            "dividend_yield": 0.02,
            "daily_change_pct": -1.0,
        }

        admissible = self._recommendation(
            _facts(
                market_cap=ABOVE,
                market_cap_magnitude=admissible_market_cap(ABOVE),
                **shared,
            )
        )

        inadmissible = self._recommendation(_facts(market_cap=ABOVE, **shared))

        assert admissible == "HOLD"
        assert inadmissible == "HOLD"

    def test_an_unjustified_magnitude_cannot_reach_the_recommendation_gate(
        self,
    ) -> None:
        """The same case stated as the platform's own claim.

        With the size point withdrawn the company can no longer reach
        HIGH quality, which is the band the recommendation gate reads.
        """

        facts = _facts(
            market_cap=1_753_616_089_088.0,
            eps=4.0,
            dividend_yield=0.02,
            forward_pe=12.0,
        )

        quality = QualitySignalService().build(facts, AssetClass.STOCK)

        assert quality.quality != "HIGH"
        assert quality.available == 2
