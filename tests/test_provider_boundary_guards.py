"""The seven failure modes this boundary exists to make impossible.

Each test names a defect the Provider Semantics Audit measured, and
asserts the *type* refuses it — not that today's code happens not to
do it. Where a guard could only be written by scanning source text it
is written against the domain object instead, because a string search
passes the day somebody renames a variable.

Every test here is a mutation test in the sense that matters: it
describes the wrong behaviour precisely enough that reintroducing it
turns this file red.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.market_snapshot import MarketQuote
from app.domain.provider_claim import ClaimAbsence, ProviderClaim, disagreeing
from app.domain.provider_fact import promote
from app.domain.provider_identity import (
    IdentityStanding,
    ProviderIdentityClaim,
    join_identity,
)
from app.domain.provider_translation import (
    DecisionRelevance,
    DomainRepresentation,
    ProviderTranslation,
    TranslationKind,
    TranslationWarrant,
)
from app.domain.provider_translations import TRANSLATIONS, governed

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)


def _claim(**overrides: object) -> ProviderClaim:
    fields: dict[str, object] = {
        "provider": "Yahoo Finance",
        "endpoint": "quoteSummary",
        "field": "dividendYield",
        "requested_at": NOW,
        "raw_value": 0.0517,
    }

    fields.update(overrides)

    return ProviderClaim(**fields)  # type: ignore[arg-type]


class TestIdentity:
    """Two providers sharing a symbol must not silently become one security."""

    def test_symbol_equality_alone_never_establishes_identity(self) -> None:
        identity = join_identity(
            "SPCX",
            (
                ProviderIdentityClaim(provider="eToro", symbol="SPCX"),
                ProviderIdentityClaim(provider="Yahoo Finance", symbol="SPCX"),
            ),
        )

        assert identity.standing is IdentityStanding.ASSUMED
        assert not identity.establishes_identity

    def test_conflicting_instrument_forms_are_unresolved(self) -> None:
        """The live SPCX shape: two providers, two kinds of instrument."""

        identity = join_identity(
            "SPCX",
            (
                ProviderIdentityClaim(
                    provider="eToro",
                    symbol="SPCX",
                    instrument_id="15618",
                    name="Space Exploration Technologies Corp",
                    taxonomy="5",
                ),
                ProviderIdentityClaim(
                    provider="Yahoo Finance",
                    symbol="SPCX",
                    name="SPAC and New Issue ETF",
                    taxonomy="ETF",
                ),
            ),
        )

        assert identity.standing is IdentityStanding.UNRESOLVED
        assert not identity.establishes_identity

    def test_both_accounts_are_retained_through_a_conflict(self) -> None:
        """A conflict resolved by dropping an account cannot be shown."""

        identity = join_identity(
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

        assert len(identity.claims) == 2
        assert set(identity.providers) == {"eToro", "Yahoo Finance"}
        assert any("Space Exploration" in account for account in identity.accounts)
        assert any("ETF" in account for account in identity.accounts)

    def test_differing_global_identifiers_are_unresolved(self) -> None:
        identity = join_identity(
            "ASML.AS",
            (
                ProviderIdentityClaim(
                    provider="eToro", symbol="ASML.AS", isin="NL0010273215"
                ),
                ProviderIdentityClaim(
                    provider="Yahoo Finance", symbol="ASML.AS", isin="ARDEUT320283"
                ),
            ),
        )

        assert identity.standing is IdentityStanding.UNRESOLVED

    def test_a_shared_global_identifier_establishes_identity(self) -> None:
        """The guard must not be a blanket refusal — proof it can pass."""

        identity = join_identity(
            "ASML.AS",
            (
                ProviderIdentityClaim(
                    provider="eToro", symbol="ASML.AS", isin="NL0010273215"
                ),
                ProviderIdentityClaim(
                    provider="Yahoo Finance", symbol="ASML.AS", isin="NL0010273215"
                ),
            ),
        )

        assert identity.standing is IdentityStanding.ESTABLISHED
        assert identity.establishes_identity

    def test_one_sided_form_evidence_is_not_agreement(self) -> None:
        """Silence is not assent — the reading that made SPCX a company."""

        identity = join_identity(
            "IB01.L",
            (
                ProviderIdentityClaim(
                    provider="eToro",
                    symbol="IB01.L",
                    name="iShares $ Treasury Bond 0-1yr UCITS ETF",
                ),
                ProviderIdentityClaim(
                    provider="Yahoo Finance", symbol="IB01.L", name="BlackRock ICS"
                ),
            ),
        )

        assert identity.standing is IdentityStanding.UNRESOLVED


class TestVocabulary:
    """A provider token must not become a domain enum without a warrant."""

    def test_every_governed_translation_declares_a_kind(self) -> None:
        for translation in TRANSLATIONS:
            assert translation.kinds

    def test_a_translation_without_a_declared_kind_is_refused(self) -> None:
        with pytest.raises(ValueError, match="which question it answers"):
            ProviderTranslation(
                provider="eToro",
                provider_field="assetTypeId",
                endpoint="/api/v1/watchlists",
                domain_concept="AssetClass",
                kinds=(),
                warrant=TranslationWarrant.ASSUMED,
                decision_relevance=DecisionRelevance.SELECTS_ANALYSIS,
            )

    def test_a_warrant_above_assumed_must_name_its_evidence(self) -> None:
        """A verified translation with nothing checked is an assumption."""

        with pytest.raises(ValueError, match="what was checked"):
            ProviderTranslation(
                provider="eToro",
                provider_field="assetTypeId",
                endpoint="/api/v1/watchlists",
                domain_concept="AssetClass",
                kinds=(TranslationKind.VOCABULARY,),
                warrant=TranslationWarrant.VERIFIED,
                decision_relevance=DecisionRelevance.SELECTS_ANALYSIS,
            )

    def test_a_declared_warrant_must_point_at_the_declaration(self) -> None:
        with pytest.raises(ValueError, match="name what the provider"):
            ProviderTranslation(
                provider="eToro",
                provider_field="assetTypeId",
                endpoint="/api/v1/watchlists",
                domain_concept="AssetClass",
                kinds=(TranslationKind.VOCABULARY,),
                warrant=TranslationWarrant.DECLARED,
                decision_relevance=DecisionRelevance.SELECTS_ANALYSIS,
                because="eToro publishes an instrument-types endpoint",
            )

    def test_the_etoro_asset_type_mapping_stands_at_assumed(self) -> None:
        """It matches the provider's truth and is still not warranted.

        The rule the brief states: a mapping that happens to be right
        is ASSUMED until something outside our own code establishes it.
        The broker publishes the declaration; nothing calls it.
        """

        translation = governed("AssetClass")

        assert translation is not None
        assert translation.warrant is TranslationWarrant.ASSUMED
        assert not translation.establishes_domain_fact


class TestUnit:
    """Incompatible representations must not collapse into one fact."""

    def test_two_endpoints_disagreeing_are_recognised_as_two_claims(self) -> None:
        summary = _claim(endpoint="quoteSummary", raw_value=0.0517)
        v7 = _claim(endpoint="v7/finance/quote", raw_value=5.17)

        assert disagreeing((summary, v7))

    def test_a_disagreement_promotes_to_unknown_whatever_the_registry(self) -> None:
        translation = ProviderTranslation(
            provider="Yahoo Finance",
            provider_field="dividendYield",
            endpoint="quoteSummary",
            domain_concept="test.yield",
            kinds=(TranslationKind.UNIT,),
            # Deliberately the strongest warrant available: a conflict
            # must override the registry, not be softened by it.
            warrant=TranslationWarrant.VERIFIED,
            decision_relevance=DecisionRelevance.GATES_A_DECISION,
            because="a checked translation, to prove the conflict wins",
        )

        fact = promote(
            concept="test.yield",
            translation=translation,
            claims=(
                _claim(endpoint="quoteSummary", raw_value=0.0517),
                _claim(endpoint="v7/finance/quote", raw_value=5.17),
            ),
            value=5.17,
        )

        assert fact.unresolved
        assert fact.warrant is TranslationWarrant.UNKNOWN
        assert not fact.establishes_domain_fact
        assert "disagree" in fact.stated

    def test_promotion_never_converts_a_value(self) -> None:
        """A domain invariant may reject a representation, never rescale it.

        5.17 cannot be a decimal ratio. The boundary says so and still
        serves 5.17, because "therefore Yahoo meant 0.0517" is a guess
        about the provider's intent and inferring it from magnitude is
        the defect, not the repair.
        """

        translation = ProviderTranslation(
            provider="Yahoo Finance",
            provider_field="dividendYield",
            endpoint="quoteSummary",
            domain_concept="test.yield",
            kinds=(TranslationKind.UNIT,),
            warrant=TranslationWarrant.ASSUMED,
            decision_relevance=DecisionRelevance.GATES_A_DECISION,
            representation=DomainRepresentation.DECIMAL_RATIO,
        )

        fact = promote(
            concept="test.yield",
            translation=translation,
            claims=(_claim(raw_value=5.17),),
            value=5.17,
        )

        assert fact.value == 5.17
        assert fact.representation_rejected
        assert fact.warrant is TranslationWarrant.UNKNOWN

    def test_the_endpoint_is_part_of_a_claims_identity(self) -> None:
        """Without it, two schemas' readings are one indistinguishable value."""

        summary = _claim(endpoint="quoteSummary")
        v7 = _claim(endpoint="v7/finance/quote")

        assert summary.key != v7.key


class TestSemantic:
    """One concept substituting for another must record the substitution."""

    def test_the_forward_eps_substitution_is_governed_and_unknown(self) -> None:
        translation = governed("ValuationSnapshot.eps (substituted)")

        assert translation is not None
        assert translation.provider_field == "forwardEps"
        assert translation.warrant is TranslationWarrant.UNKNOWN
        assert not translation.establishes_domain_fact

    def test_a_substituted_eps_does_not_borrow_the_realised_warrant(self) -> None:
        realised = governed("ValuationSnapshot.eps")
        substituted = governed("ValuationSnapshot.eps (substituted)")

        assert realised is not None
        assert substituted is not None
        assert realised.warrant is not substituted.warrant


class TestAbsence:
    """Missing data must not become an ordinary observed zero."""

    def test_a_claim_with_no_value_and_no_reason_is_refused(self) -> None:
        with pytest.raises(ValueError, match="no value and no"):
            ProviderClaim(
                provider="Yahoo Finance",
                endpoint="yf.download",
                field="Close",
                requested_at=NOW,
            )

    def test_a_claim_cannot_carry_both_a_value_and_an_absence(self) -> None:
        with pytest.raises(ValueError, match="one of them is not true"):
            ProviderClaim(
                provider="Yahoo Finance",
                endpoint="yf.download",
                field="Close",
                requested_at=NOW,
                raw_value=1.0,
                absence=ClaimAbsence.FIELD_ABSENT,
            )

    def test_no_absence_is_a_measurement(self) -> None:
        for absence in ClaimAbsence:
            assert not absence.is_measurement

    def test_a_manufactured_zero_is_distinguishable_from_an_observed_one(
        self,
    ) -> None:
        observed = MarketQuote(
            symbol="AAPL", name="Apple", price=1.0, change_percent=0.0
        )

        manufactured = MarketQuote(
            symbol="ARB",
            name="Arbitrum",
            price=0.0006,
            change_percent=0.0,
            change_absence=ClaimAbsence.INSUFFICIENT_HISTORY,
        )

        assert observed.change_percent == manufactured.change_percent
        assert observed.change_is_measured
        assert not manufactured.change_is_measured

    def test_a_substituted_fact_never_establishes_anything(self) -> None:
        translation = ProviderTranslation(
            provider="Yahoo Finance",
            provider_field="Close (pair)",
            endpoint="yf.download",
            domain_concept="test.change",
            kinds=(TranslationKind.UNIT,),
            warrant=TranslationWarrant.VERIFIED,
            decision_relevance=DecisionRelevance.GATES_A_DECISION,
            because="a checked translation, to prove substitution still wins",
        )

        fact = promote(
            concept="test.change",
            translation=translation,
            claims=(
                ProviderClaim.absent(
                    provider="Yahoo Finance",
                    endpoint="yf.download",
                    field="Close (pair)",
                    requested_at=NOW,
                    absence=ClaimAbsence.INSUFFICIENT_HISTORY,
                ),
            ),
            value=0.0,
            compatibility_substitution=ClaimAbsence.INSUFFICIENT_HISTORY,
        )

        assert fact.value == 0.0
        assert fact.substituted
        assert not fact.establishes_domain_fact
        assert "nothing was measured" in fact.stated


class TestTimestamp:
    """Request time must never become provider observation time."""

    def test_an_unsupplied_observation_time_stays_absent(self) -> None:
        claim = _claim()

        assert claim.acquisition.observed_at == NOW
        assert claim.observation is None

    def test_a_supplied_observation_time_is_kept_apart(self) -> None:
        stated = datetime(2026, 8, 14, 21, 0, tzinfo=UTC)

        claim = _claim(provider_observed_at=stated)

        observation = claim.observation

        assert observation is not None
        assert observation.observed_at == stated
        assert claim.acquisition.observed_at == NOW
        assert observation.observed_at != claim.acquisition.observed_at

    def test_a_fact_reports_no_observation_time_it_was_not_given(self) -> None:
        translation = governed("ValuationSnapshot.forward_pe")

        assert translation is not None

        fact = promote(
            concept="ValuationSnapshot.forward_pe",
            translation=translation,
            claims=(_claim(field="forwardPE", raw_value=8.54),),
            value=8.54,
        )

        assert fact.acquisition is not None
        assert fact.observation is None


class TestCurrency:
    """A hardcoded currency must not look like a declared one."""

    def test_an_assumed_currency_is_flagged_on_the_quote(self) -> None:
        quote = MarketQuote(
            symbol="BP.L",
            name="BP",
            price=517.2,
            change_percent=0.4,
            currency="USD",
            currency_is_assumed=True,
        )

        assert quote.currency == "USD"
        assert quote.currency_is_assumed

    def test_the_currency_translation_is_governed_and_unwarranted(self) -> None:
        translation = governed("MarketQuote.currency")

        assert translation is not None
        assert TranslationKind.VOCABULARY in translation.kinds
        assert not translation.establishes_domain_fact
