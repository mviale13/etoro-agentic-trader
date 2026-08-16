"""Monetary values compare only when both sides say what they are in.

`monetary-comparison@1`, and the establishment rule behind it. BP.L is
the standing negative specimen: one instrument whose price ticks in
pence, whose statements are in dollars, and whose market cap is in
pounds — so every inheritance rule picks a wrong answer for a security
the platform already holds.
"""

from __future__ import annotations

import pytest

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.monetary import (
    DenominationBasis,
    MarketCapDenomination,
    MonetaryAmount,
    corroborate_denomination,
)
from app.domain.provider_translation import TranslationWarrant
from app.providers.value_provider import ValueProvider
from app.services.company_facts_service import CompanyFactsService
from app.services.quality_signal_service import (
    ELIGIBLE_MARKET_CAP_WARRANTS,
    QualitySignalService,
)

USD_THRESHOLD = QualitySignalService.LARGE_CAP

#: BP.L as the live probe measured it (#142): quote GBp, statements
#: USD, and cap / (price × shares) = exactly 0.010.
BP_L = {
    "marketCap": 80_798_785_536.0,
    "regularMarketPrice": 522.90,
    "sharesOutstanding": 15_452_053_728.0,
    "currency": "GBp",
    "financialCurrency": "USD",
}

#: DIDIY as measured: an ADR whose cap does not reconcile with the
#: listed share count (ratio 1.072).
DIDIY = {
    "marketCap": 18_030_065_664.0,
    "regularMarketPrice": 4.00,
    "sharesOutstanding": 4_202_830_472.0,
    "currency": "USD",
    "financialCurrency": "CNY",
}


def _magnitude(
    amount: float,
    currency: str | None,
    *,
    established: bool = True,
) -> MarketCapMagnitude:
    return MarketCapMagnitude.measured(
        amount,
        warrant=TranslationWarrant.VALIDATED,
        currency=currency,
        currency_is_assumed=not established,
    )


class TestTheThresholdDeclaresItself:
    def test_the_threshold_is_usd_ten_billion(self) -> None:
        assert USD_THRESHOLD.currency == "USD"
        assert USD_THRESHOLD.amount == 10_000_000_000.0

    def test_the_amount_cannot_drift_from_the_fingerprinted_constant(self) -> None:
        assert USD_THRESHOLD.amount == float(QualitySignalService.LARGE_CAP_THRESHOLD)

    def test_the_declaration_is_visible_in_output(self) -> None:
        """Test 10: the policy can never become implicit again."""

        assert "USD" in USD_THRESHOLD.stated
        assert "USD" in repr(USD_THRESHOLD)

    def test_an_unlabelled_amount_cannot_be_constructed(self) -> None:
        with pytest.raises(ValueError, match="must say what currency"):
            MonetaryAmount(amount=10_000_000_000.0, currency=" ")


class TestComparison:
    def test_usd_above_the_usd_threshold_is_comparable(self) -> None:
        """Test 1."""

        magnitude = _magnitude(12_000_000_000.0, "USD")

        assert magnitude.comparable_with(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)

    def test_usd_below_the_usd_threshold_is_comparable(self) -> None:
        """Test 2: below the line is still a comparison."""

        magnitude = _magnitude(8_000_000_000.0, "USD")

        assert magnitude.comparable_with(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)

    def test_chf_against_usd_is_refused_pending_conversion(self) -> None:
        """Test 3: Nestlé's shape — established, and not comparable."""

        magnitude = _magnitude(208_375_545_856.0, "CHF")

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS, USD_THRESHOLD)

        assert "established in CHF" in refusal
        assert "pending an authorised currency conversion" in refusal

    def test_gbp_against_usd_is_refused_pending_conversion(self) -> None:
        """Test 4."""

        magnitude = _magnitude(80_798_785_536.0, "GBP")

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

    def test_a_bare_magnitude_is_refused_for_absent_denomination(self) -> None:
        """Test 5: 208bn of nothing in particular compares with nothing."""

        magnitude = _magnitude(208_375_545_856.0, None, established=False)

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS, USD_THRESHOLD)

        assert "currency is not established" in refusal
        assert "conversion" not in refusal


class TestEstablishmentWithoutInheritance:
    def test_a_reconciling_usd_cap_is_established_usd(self) -> None:
        """The 29-case shape: identity holds in the quote unit."""

        outcome = corroborate_denomination(
            4_464_797_286_400.0,
            305.93,
            (14_594_180_000.0,),
            "USD",
        )

        assert outcome.basis is DenominationBasis.CORROBORATED
        assert outcome.currency == "USD"
        assert "by arithmetic" in outcome.because

    def test_a_reconciling_chf_cap_is_established_chf_not_usd(self) -> None:
        """Nestlé: the establishment says CHF; the comparison then refuses."""

        outcome = corroborate_denomination(
            208_375_545_856.0,
            81.01,
            (2_572_220_000.0,),
            "CHF",
        )

        assert outcome.basis is DenominationBasis.CORROBORATED
        assert outcome.currency == "CHF"

    def test_bp_l_is_established_gbp_by_arithmetic(self) -> None:
        """Tests 6 and 7: neither the quote nor the statement currency.

        The direct identity fails at ratio 0.010, so GBp is refused;
        the minor-unit identity holds exactly, so the cap is GBP — and
        nothing anywhere consulted `financialCurrency`, so USD had no
        path in.
        """

        outcome = corroborate_denomination(
            BP_L["marketCap"],
            BP_L["regularMarketPrice"],
            (BP_L["sharesOutstanding"],),
            BP_L["currency"],
        )

        assert outcome.currency == "GBP"
        assert outcome.currency != "GBp"
        assert outcome.currency != "USD"
        assert outcome.basis is DenominationBasis.MINOR_UNIT

    def test_bp_l_through_the_live_adapter_is_gbp(self) -> None:
        """The same facts through `from_info`, not just the function."""

        snapshot = ValueProvider.from_info(dict(BP_L))

        assert snapshot.market_cap_denomination is not None
        assert snapshot.market_cap_denomination.currency == "GBP"

    def test_bp_l_is_refused_against_the_usd_threshold(self) -> None:
        snapshot = ValueProvider.from_info(dict(BP_L))

        magnitude = CompanyFactsService._market_cap_magnitude(
            snapshot.market_cap, snapshot.market_cap_denomination
        )

        assert magnitude is not None
        assert magnitude.currency == "GBP"
        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

    def test_an_adr_reconciliation_failure_is_not_currency_unknown(self) -> None:
        """Test 8: a structural failure routes to a different boundary."""

        outcome = corroborate_denomination(
            DIDIY["marketCap"],
            DIDIY["regularMarketPrice"],
            (DIDIY["sharesOutstanding"],),
            DIDIY["currency"],
        )

        assert outcome.basis is DenominationBasis.UNRECONCILED
        assert outcome.currency is None
        assert "not a currency doubt" in outcome.because

    def test_missing_inputs_are_insufficient_not_unreconciled(self) -> None:
        outcome = corroborate_denomination(1_000_000.0, None, (), "USD")

        assert outcome.basis is DenominationBasis.INSUFFICIENT
        assert outcome.currency is None

    def test_a_non_establishing_basis_cannot_carry_a_currency(self) -> None:
        """The type refuses an inherited denomination wearing a basis."""

        with pytest.raises(ValueError, match="inherited denomination"):
            MarketCapDenomination(
                currency="USD",
                basis=DenominationBasis.UNRECONCILED,
                because="smuggled",
            )


class TestQualityConsumesTheBoundary:
    def _signal(self, denomination: MarketCapDenomination | None):
        magnitude = CompanyFactsService._market_cap_magnitude(
            50_000_000_000.0, denomination
        )

        facts = CompanyFacts(
            instrument_id=1,
            symbol="TEST",
            name="Test Co",
            asset_type="stock",
            exchange="4",
            market_cap=50_000_000_000.0,
            market_cap_magnitude=magnitude,
            eps=4.0,
            dividend_yield=0.02,
        )

        return QualitySignalService().build(facts, AssetClass.STOCK)

    def test_an_established_usd_cap_restores_the_size_factor(self) -> None:
        signal = self._signal(
            MarketCapDenomination(
                currency="USD",
                basis=DenominationBasis.CORROBORATED,
                because="corroborated in test",
            )
        )

        assert signal.quality == "HIGH"
        assert signal.available == 3

    def test_a_chf_cap_leaves_the_size_factor_unreadable(self) -> None:
        """Nestlé end to end: established, refused, quality abstains."""

        signal = self._signal(
            MarketCapDenomination(
                currency="CHF",
                basis=DenominationBasis.CORROBORATED,
                because="corroborated in test",
            )
        )

        assert signal.quality == "UNKNOWN"
        assert signal.available == 2

    def test_removing_denomination_withdraws_authority_not_direction(self) -> None:
        """Test 9: the band disappears; it never becomes a different band."""

        with_denomination = self._signal(
            MarketCapDenomination(
                currency="USD",
                basis=DenominationBasis.CORROBORATED,
                because="corroborated in test",
            )
        )

        without = self._signal(None)

        assert with_denomination.quality == "HIGH"
        assert without.quality == "UNKNOWN"
        assert without.quality not in ("LOW", "MEDIUM")
        # The measured half survives: the other two factors still read.
        assert without.earned == 2
        assert without.available == 2
