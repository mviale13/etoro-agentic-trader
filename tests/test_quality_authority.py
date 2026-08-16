"""A band earned over part of the question set describes the reading.

`quality-authority@1`. The existing LOW/MEDIUM/HIGH ruler is unchanged
and its thresholds are untouched; what changed is that it runs only
after every applicable factor has been read.

The states that exposed the defect are pinned here, and so are the six
securities the platform would otherwise have told an investor to sell.
"""

from __future__ import annotations

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.decision_participation import SignalParticipation
from app.domain.quality_coverage import (
    FactorStanding,
    QualityCoverage,
    QualityFactor,
)
from app.services.company_committee_service import CompanyCommitteeService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService
from tests.conftest import admissible_market_cap

LARGE = 50_000_000_000.0
SMALL = 2_000_000_000.0


def _quality(
    market_cap: float | None = None,
    eps: float | None = None,
    dividend_yield: float | None = None,
    *,
    admissible: bool = True,
):
    facts = CompanyFacts(
        instrument_id=1,
        symbol="TEST",
        name="Test Co",
        asset_type="stock",
        exchange="4",
        market_cap=market_cap,
        market_cap_magnitude=(
            admissible_market_cap(market_cap)
            if market_cap is not None and admissible
            else None
        ),
        eps=eps,
        dividend_yield=dividend_yield,
    )

    return QualitySignalService().build(facts, AssetClass.STOCK)


class TestTheStatesThatExposedTheDefect:
    def test_one_of_three_readable_and_passed_is_not_a_band(self) -> None:
        """`1/1` — Apple's shape. Passing everything readable is not LOW."""

        signal = _quality(dividend_yield=0.02)

        assert signal.quality == "UNKNOWN"
        assert (signal.earned, signal.available) == (1, 1)

    def test_one_of_three_readable_and_failed_is_also_not_a_band(self) -> None:
        """`0/1` — and it must stay distinguishable from the above."""

        signal = _quality(dividend_yield=0.0)

        assert signal.quality == "UNKNOWN"
        assert (signal.earned, signal.available) == (0, 1)

    def test_passing_and_failing_the_same_lone_factor_differ(self) -> None:
        """The conflation #140 measured: both were LOW, both voted −1."""

        passed = _quality(dividend_yield=0.02)
        failed = _quality(dividend_yield=0.0)

        assert passed.quality == failed.quality == "UNKNOWN"
        assert passed.earned != failed.earned

    def test_two_of_three_readable_is_not_a_band(self) -> None:
        """`2/2` with a third applicable factor unread."""

        signal = _quality(eps=4.0, dividend_yield=0.02)

        assert signal.quality == "UNKNOWN"
        assert (signal.earned, signal.available) == (2, 2)
        assert signal.basis is not None
        assert "company size could not be read" in signal.basis

    @pytest.mark.parametrize(
        ("market_cap", "eps", "dividend", "band"),
        [
            (LARGE, 4.0, 0.02, "HIGH"),
            (LARGE, 4.0, 0.0, "MEDIUM"),
            (SMALL, -1.0, 0.0, "LOW"),
        ],
    )
    def test_three_of_three_bands_exactly_as_before(
        self, market_cap: float, eps: float, dividend: float, band: str
    ) -> None:
        """The ruler is untouched: full coverage, original semantics."""

        signal = _quality(market_cap, eps, dividend)

        assert signal.quality == band
        assert signal.available == 3

    def test_the_ruler_constants_are_unchanged(self) -> None:
        assert QualitySignalService.BANDS == (("HIGH", 3), ("MEDIUM", 2), ("LOW", 0))
        assert QualitySignalService.FACTORS == 3


class TestAbstentionIsNotABand:
    def test_it_is_not_low(self) -> None:
        assert _quality(dividend_yield=0.02).quality != "LOW"

    def test_it_carries_no_score_and_no_synthetic_band(self) -> None:
        signal = _quality(dividend_yield=0.02)

        assert signal.quality == "UNKNOWN"
        assert signal.confidence == 20

    def test_the_measured_half_survives_the_abstention(self) -> None:
        """Performance is still reported; only the band is withheld."""

        signal = _quality(eps=4.0, dividend_yield=0.02)

        assert signal.earned == 2
        assert signal.available == 2
        assert len(signal.contributions) == 2

    def test_the_reason_names_the_missing_factor(self) -> None:
        signal = _quality(market_cap=LARGE, eps=4.0)

        assert signal.basis is not None
        assert "dividend could not be read" in signal.basis


class TestApplicabilitySupportsASmallerSet:
    """A genuinely two-factor assessment is authorised at 2/2."""

    def test_a_two_factor_applicable_set_is_complete_at_two(self) -> None:
        coverage = QualityCoverage(
            standings=(
                FactorStanding(
                    factor=QualityFactor.MARKET_SIGNIFICANCE,
                    participation=SignalParticipation.NOT_APPLICABLE,
                ),
                FactorStanding(
                    factor=QualityFactor.EARNINGS,
                    participation=SignalParticipation.PARTICIPATING,
                    points=1,
                ),
                FactorStanding(
                    factor=QualityFactor.DIVIDEND,
                    participation=SignalParticipation.PARTICIPATING,
                    points=1,
                ),
            )
        )

        assert coverage.expected == 2
        assert coverage.available == 2
        assert coverage.may_band
        assert coverage.missing == ()

    def test_an_inapplicable_factor_does_not_count_as_missing(self) -> None:
        coverage = QualityCoverage(
            standings=(
                FactorStanding(
                    factor=QualityFactor.MARKET_SIGNIFICANCE,
                    participation=SignalParticipation.NOT_APPLICABLE,
                ),
                FactorStanding(
                    factor=QualityFactor.EARNINGS,
                    participation=SignalParticipation.EXPECTED_ABSENT,
                ),
                FactorStanding(
                    factor=QualityFactor.DIVIDEND,
                    participation=SignalParticipation.PARTICIPATING,
                    points=1,
                ),
            )
        )

        assert coverage.expected == 2
        assert not coverage.may_band
        assert coverage.missing == (QualityFactor.EARNINGS,)


class TestIntraQualityDeletion:
    """Deleting a factor may withdraw authority, never move direction."""

    BANDS = {"LOW": -1, "MEDIUM": 0, "HIGH": 1, "UNKNOWN": None}

    def test_deleting_any_established_factor_only_withdraws_authority(
        self,
    ) -> None:
        full = [
            (LARGE, 4.0, 0.02),
            (LARGE, 4.0, 0.0),
            (SMALL, 4.0, 0.0),
            (SMALL, -1.0, 0.0),
            (SMALL, -1.0, 0.02),
            (LARGE, -1.0, 0.02),
        ]

        for cap, eps, dividend in full:
            before = _quality(cap, eps, dividend)

            assert before.available == 3

            for deleted in range(3):
                factors: list[float | None] = [cap, eps, dividend]
                factors[deleted] = None

                after = _quality(*factors)

                assert after.quality == "UNKNOWN", (
                    f"{(cap, eps, dividend)} deleting {deleted} produced "
                    f"{after.quality}, a band over a partial question set"
                )

                assert self.BANDS[after.quality] is None

    def test_an_inadmissible_magnitude_withdraws_authority_too(self) -> None:
        """The live path: the size factor is applicable and unreadable."""

        before = _quality(LARGE, 4.0, 0.02)
        after = _quality(LARGE, 4.0, 0.02, admissible=False)

        assert before.quality == "HIGH"
        assert after.quality == "UNKNOWN"


class TestTheSixBlockingSpecimens:
    """None may become SELL because incomplete Quality became LOW."""

    SPECIMENS = (
        ("AAPL", 32.94, 4_572_794_322_944.0, None, 0.34),
        ("GOOG", 23.99, 4_322_915_254_272.0, None, 0.25),
        ("PG", 19.69, 339_486_441_472.0, None, 2.99),
        ("PLTR", 74.79, 413_350_068_224.0, 1.17, None),
        ("SBUX", 33.95, 120_361_205_760.0, None, 2.36),
        ("TSLA", 148.06, 1_297_742_299_136.0, 1.08, None),
    )

    @staticmethod
    def _recommendation(
        symbol: str, pe: float, cap: float, eps: float | None, div: float | None
    ) -> tuple[str, str]:
        facts = CompanyFacts(
            instrument_id=1,
            symbol=symbol,
            name=symbol,
            asset_type="stock",
            exchange="4",
            forward_pe=pe,
            # The live state: the magnitude is held and inadmissible.
            market_cap=cap,
            eps=eps,
            dividend_yield=div,
            daily_change_pct=-1.0,
        )

        quality = QualitySignalService().build(facts, AssetClass.STOCK)

        signals = CompanySignals(
            value=ValueSignalService().build(facts, AssetClass.STOCK),
            quality=quality,
            momentum=MomentumSignalService().build(facts),
            risk=RiskSignalService().build(facts),
        )

        outcome = CompanyCommitteeService().evaluate(symbol, signals)

        return quality.quality, outcome.recommendation

    @pytest.mark.parametrize(
        ("symbol", "pe", "cap", "eps", "div"),
        SPECIMENS,
        ids=[specimen[0] for specimen in SPECIMENS],
    )
    def test_none_becomes_sell_from_incomplete_quality(
        self,
        symbol: str,
        pe: float,
        cap: float,
        eps: float | None,
        div: float | None,
    ) -> None:
        band, recommendation = self._recommendation(symbol, pe, cap, eps, div)

        assert band == "UNKNOWN", (
            f"{symbol}: quality banded {band} on a partial question set"
        )

        assert recommendation != "SELL", (
            f"{symbol}: incomplete quality produced a {recommendation}"
        )
