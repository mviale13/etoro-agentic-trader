"""An amount crosses a currency only through evidenced translation.

`fx-translation@1`, C6. Nestlé is the positive specimen — CHF 208bn,
established by arithmetic in #142's measurement, authorised into USD
and finally comparable with the USD 10bn threshold. BP.L proves the
POUNDS figure is what gets translated: never the pence quote, never
the statement dollars. And every earlier crossing keeps its refusal:
FX rescues nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.exchange_rate import ExchangeRate
from app.domain.market_magnitude import MarketCapMagnitude
from app.domain.monetary import (
    MonetaryAmount,
)
from app.domain.monetary_translation import (
    TRANSLATABLE_TO_USD,
    MonetaryTranslation,
)
from app.domain.provenance import Provenance
from app.domain.provider_translation import TranslationWarrant
from app.services.quality_signal_service import (
    ELIGIBLE_MARKET_CAP_WARRANTS,
    QualitySignalService,
)
from tests.conftest import assumed_identity

USD_THRESHOLD = QualitySignalService.LARGE_CAP

#: One acquisition day, shared by the figure and the rate — the
#: temporal rule's happy case.
DAY = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)

#: Nestlé as the live probe measured it: cap 208,375,545,856 in CHF,
#: established CORROBORATED by the price × shares identity.
NESTLE_CAP = 208_375_545_856.0

#: BP.L's market cap in POUNDS — the figure the minor-unit identity
#: established, one hundredth of what the pence quote would suggest.
BP_L_CAP_GBP = 80_798_785_536.0


def _rate(
    base: str,
    quote: str,
    value: float,
    observed_at: datetime = DAY,
    source: str = "Yahoo Finance",
) -> ExchangeRate:
    return ExchangeRate(
        base=base,
        quote=quote,
        rate=value,
        reading=Provenance(source=source, observed_at=observed_at),
    )


def _translation(
    amount: float = NESTLE_CAP,
    currency: str = "CHF",
    rate: ExchangeRate | None = None,
    observed_at: datetime = DAY,
) -> MonetaryTranslation:
    return MonetaryTranslation(
        original=MonetaryAmount(amount=amount, currency=currency),
        rate=rate if rate is not None else _rate("CHF", "USD", 1.2402),
        subject_observed_at=observed_at,
    )


class TestDirectionIsPartOfTheRate:
    def test_an_inverted_pair_cannot_construct_a_translation(self) -> None:
        """The inverted-rate bug is a raise, not a plausible number.

        A USD→CHF rate handed to a CHF amount would divide where it
        should multiply — numerically believable, wrong by the square
        of the rate. It cannot be constructed.
        """

        with pytest.raises(ValueError, match="inverted or mismatched"):
            _translation(rate=_rate("USD", "CHF", 0.8063))

    def test_a_mismatched_pair_cannot_construct_one_either(self) -> None:
        with pytest.raises(ValueError, match="inverted or mismatched"):
            _translation(rate=_rate("EUR", "USD", 1.17))

    def test_a_non_positive_rate_is_not_a_measurement(self) -> None:
        with pytest.raises(ValueError, match="not a measurement"):
            _translation(rate=_rate("CHF", "USD", 0.0))

    def test_the_derivation_is_the_exact_product(self) -> None:
        """Pinned to the digit, so an inversion that survived the type
        guard (a mislabeled feed) would still fail loudly here."""

        translation = _translation(rate=_rate("CHF", "USD", 1.2402))

        derived = translation.translated

        assert derived is not None
        assert derived.amount == NESTLE_CAP * 1.2402
        assert derived.amount == pytest.approx(258_427_351_970.6, abs=1.0)
        assert derived.currency == "USD"

    def test_the_original_is_never_altered(self) -> None:
        translation = _translation()

        assert translation.original.amount == NESTLE_CAP
        assert translation.original.currency == "CHF"


class TestTimeIsPartOfTheEvidence:
    def test_a_same_day_rate_authorises(self) -> None:
        translation = _translation(
            rate=_rate("CHF", "USD", 1.2402, observed_at=DAY.replace(hour=18)),
            observed_at=DAY,
        )

        assert translation.temporally_compatible
        assert translation.authorised
        assert translation.translated is not None

    def test_a_rate_from_another_day_is_refused_not_applied(self) -> None:
        """'Latest FX' is never silently used for an older observation."""

        stale_day = datetime(2026, 8, 11, tzinfo=UTC)

        translation = _translation(
            rate=_rate("CHF", "USD", 1.2402, observed_at=stale_day),
            observed_at=DAY,
        )

        assert not translation.authorised
        assert translation.translated is None
        assert "different day" in translation.stated
        assert "refused" in translation.stated

    def test_the_refusal_works_in_both_directions(self) -> None:
        """An older figure with a fresh rate refuses identically."""

        translation = _translation(
            rate=_rate("CHF", "USD", 1.2402, observed_at=DAY),
            observed_at=datetime(2026, 8, 9, tzinfo=UTC),
        )

        assert not translation.authorised
        assert translation.translated is None

    def test_the_derivation_is_inspectable_without_recomputation(self) -> None:
        """C6's readable form: original × [rate, source, date] = derived."""

        stated = _translation(rate=_rate("CHF", "USD", 1.2402)).stated

        assert "CHF 208,375,545,856" in stated
        assert "CHF→USD 1.2402" in stated
        assert "Yahoo Finance" in stated
        assert "2026-08-16" in stated
        assert "= USD" in stated


class TestTheComparisonRoute:
    def _magnitude(
        self,
        translation: MonetaryTranslation | None,
        amount: float = NESTLE_CAP,
        currency: str = "CHF",
    ) -> MarketCapMagnitude:
        return MarketCapMagnitude.measured(
            amount,
            warrant=TranslationWarrant.VALIDATED,
            currency=currency,
            currency_is_assumed=False,
            identity=assumed_identity(),
            translation=translation,
        )

    def test_chf_with_an_authorised_translation_is_comparable(self) -> None:
        """Nestlé, finally: established CHF, evidenced into USD, compared."""

        magnitude = self._magnitude(_translation())

        assert magnitude.comparable_with(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)
        assert (
            magnitude.comparable_amount(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)
            == NESTLE_CAP * 1.2402
        )

    def test_the_compared_amount_is_the_translated_one_never_the_raw(self) -> None:
        """A DKK cap above the threshold's bare number, below it in USD.

        DKK 50bn reads numerically above 10bn; at 0.157 dollars per
        krone it is USD 7.85bn — below. If the raw amount ever leaked
        into the comparison this test flips, which is exactly the
        wrong-by-a-factor comparison the boundary exists to refuse.
        """

        magnitude = self._magnitude(
            _translation(
                amount=50_000_000_000.0,
                currency="DKK",
                rate=_rate("DKK", "USD", 0.157),
            ),
            amount=50_000_000_000.0,
            currency="DKK",
        )

        amount = magnitude.comparable_amount(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

        assert amount == 50_000_000_000.0 * 0.157
        assert amount is not None
        assert amount < QualitySignalService.LARGE_CAP_THRESHOLD

    def test_same_currency_usd_never_involves_fx(self) -> None:
        magnitude = self._magnitude(None, amount=50_000_000_000.0, currency="USD")

        assert magnitude.comparable_with(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)
        assert (
            magnitude.comparable_amount(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)
            == 50_000_000_000.0
        )

    def test_a_missing_rate_is_never_one_to_one(self) -> None:
        magnitude = self._magnitude(None)

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )
        assert (
            magnitude.comparable_amount(USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS)
            is None
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS, USD_THRESHOLD)

        assert "CHF→USD" in refusal
        assert "never assumed" in refusal

    def test_a_stale_rate_is_refused_with_its_evidence_named(self) -> None:
        magnitude = self._magnitude(
            _translation(
                rate=_rate(
                    "CHF", "USD", 1.2402, observed_at=datetime(2026, 8, 11, tzinfo=UTC)
                )
            )
        )

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS, USD_THRESHOLD)

        assert "different day" in refusal

    def test_a_translation_into_the_wrong_currency_does_not_compare(self) -> None:
        magnitude = self._magnitude(_translation(rate=_rate("CHF", "EUR", 0.936)))

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

    def test_a_translation_of_a_different_figure_cannot_be_attached(self) -> None:
        """The magnitude refuses a derived claim about another number."""

        with pytest.raises(ValueError, match="exactly this magnitude"):
            self._magnitude(_translation(amount=1_000_000.0))

    def test_a_translation_cannot_ride_on_an_unestablished_currency(self) -> None:
        with pytest.raises(ValueError, match="exactly this magnitude"):
            MarketCapMagnitude.measured(
                NESTLE_CAP,
                warrant=TranslationWarrant.VALIDATED,
                currency=None,
                currency_is_assumed=True,
                identity=assumed_identity(),
                translation=_translation(),
            )


class TestFxRescuesNothing:
    """The three earlier crossings keep their refusals, translation or not."""

    def test_an_unresolved_identity_refuses_before_fx_is_looked_at(self) -> None:
        from app.domain.provider_identity import (
            ProviderIdentityClaim,
            join_identity,
        )

        disputed = join_identity(
            "SPCX",
            (
                ProviderIdentityClaim(
                    provider="eToro",
                    symbol="SPCX",
                    name="Space Exploration Technologies Corp",
                ),
                ProviderIdentityClaim(
                    provider="Yahoo Finance",
                    symbol="SPCX",
                    name="SPAC and New Issue ETF",
                ),
            ),
        )

        magnitude = MarketCapMagnitude.measured(
            NESTLE_CAP,
            warrant=TranslationWarrant.VALIDATED,
            currency="CHF",
            currency_is_assumed=False,
            identity=disputed,
            translation=_translation(),
        )

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )

        refusal = magnitude.refusal(ELIGIBLE_MARKET_CAP_WARRANTS, USD_THRESHOLD)

        assert "identity" in refusal
        assert "translation" not in refusal

    def test_an_ineligible_warrant_refuses_translation_or_not(self) -> None:
        magnitude = MarketCapMagnitude.measured(
            NESTLE_CAP,
            warrant=TranslationWarrant.ASSUMED,
            currency="CHF",
            currency_is_assumed=False,
            identity=assumed_identity(),
            translation=_translation(),
        )

        assert not magnitude.comparable_with(
            USD_THRESHOLD, ELIGIBLE_MARKET_CAP_WARRANTS
        )


class TestQualityConsumesTheTranslation:
    def _facts(self, magnitude: MarketCapMagnitude):
        from app.domain.company_facts import CompanyFacts

        return CompanyFacts(
            instrument_id=1,
            symbol="NESN.SW",
            name="Nestle SA",
            asset_type="stock",
            exchange="4",
            market_cap=magnitude.amount,
            market_cap_magnitude=magnitude,
            eps=4.0,
            dividend_yield=0.02,
        )

    def _nestle(self, translation: MonetaryTranslation | None) -> MarketCapMagnitude:
        return MarketCapMagnitude.measured(
            NESTLE_CAP,
            warrant=TranslationWarrant.VALIDATED,
            currency="CHF",
            currency_is_assumed=False,
            identity=assumed_identity("NESN.SW"),
            translation=translation,
        )

    def test_nestle_finally_reads_three_of_three(self) -> None:
        """The chain C6 exists for: established CHF → authorised USD →
        size factor readable → quality banded over the full set."""

        signal = QualitySignalService().build(self._facts(self._nestle(_translation())))

        assert signal.available == 3
        assert signal.quality == "HIGH"

    def test_deleting_fx_authority_withdraws_and_never_reverses(self) -> None:
        """The translation deletion invariant.

        With the translation, Nestlé's size factor reads Large-cap.
        Without it, the factor is unread and the band is withheld —
        never a different band, and never the opposite finding.
        """

        with_fx = QualitySignalService().build(
            self._facts(self._nestle(_translation()))
        )
        without = QualitySignalService().build(self._facts(self._nestle(None)))

        statements_with = [f.statement for f in with_fx.evidence]
        statements_without = [f.statement for f in without.evidence]

        assert "Large-cap company." in statements_with
        assert "Large-cap company." not in statements_without
        assert "Small or mid-cap company." not in statements_without

        assert with_fx.quality == "HIGH"
        assert without.quality == "UNKNOWN"
        assert without.available == 2

    def test_a_stale_rate_withdraws_exactly_like_no_rate(self) -> None:
        stale = _translation(
            rate=_rate(
                "CHF", "USD", 1.2402, observed_at=datetime(2026, 8, 11, tzinfo=UTC)
            )
        )

        signal = QualitySignalService().build(self._facts(self._nestle(stale)))

        assert signal.quality == "UNKNOWN"
        assert signal.available == 2


class TestTheTranslatableSet:
    def test_the_membership_is_the_measured_four(self) -> None:
        assert TRANSLATABLE_TO_USD == ("CHF", "DKK", "EUR", "GBP")

    def test_bp_l_translates_the_pounds_figure(self) -> None:
        """Never GBp, never the statement dollars.

        The GBP figure times the GBP→USD rate — the pence figure would
        be one hundred times larger, and the statement currency has no
        path in because nothing here reads `financialCurrency` at all.
        """

        translation = MonetaryTranslation(
            original=MonetaryAmount(amount=BP_L_CAP_GBP, currency="GBP"),
            rate=_rate("GBP", "USD", 1.2716),
            subject_observed_at=DAY,
        )

        derived = translation.translated

        assert derived is not None
        assert derived.amount == BP_L_CAP_GBP * 1.2716
        assert derived.amount == pytest.approx(102_743_739_648.0, rel=1e-6)

    def test_a_pence_labelled_rate_cannot_touch_a_pounds_figure(self) -> None:
        """GBp is not GBP, and the type refuses the pair."""

        with pytest.raises(ValueError, match="inverted or mismatched"):
            MonetaryTranslation(
                original=MonetaryAmount(amount=BP_L_CAP_GBP, currency="GBP"),
                rate=_rate("GBp", "USD", 0.012716),
                subject_observed_at=DAY,
            )
