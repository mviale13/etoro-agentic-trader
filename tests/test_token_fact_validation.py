"""A provider returning a value does not make that value a fact.

HYPE is the acceptance case throughout: Yahoo's stored reading priced
an $18bn token at $8,105, gave it 1.5bn circulating against a real
336.7m, and implied six years of history for a token that began trading
in 2024 — every figure apparently valid, every figure wrong. The gate
must reject them with their reasons retained, and must never let the
platform choose a plausible value over UNKNOWN.
"""

from datetime import UTC, datetime

from app.domain.provenance import Provenance
from app.domain.token_fact_validation import (
    GeneralistTokenClaims,
    NativeTokenClaims,
    judge,
)
from app.domain.token_facts import TokenFactStanding

READ = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)


def native(**overrides: object) -> NativeTokenClaims:
    """Hyperliquid as TokenInsight actually reported it, 2026-08-10."""

    values: dict[str, object] = {
        "symbol": "HYPE",
        "provider_id": "hyperliquid",
        "source": "TokenInsight",
        "read": Provenance(source="TokenInsight", observed_at=READ),
        "price": 54.23,
        "market_cap": 18_260_000_000.0,
        "circulating_supply": 336_685_219.0,
        "max_supply": 1_000_000_000.0,
        "fully_diluted_valuation": 54_230_000_000.0,
        "rank": 9.0,
        "spot_volume_24h": 11_780_956.0,
        "spot_volume_change_24h": -0.30,
        "price_change_24h": -0.0091,
    }

    values.update(overrides)

    return NativeTokenClaims(**values)  # type: ignore[arg-type]


def yahoo(**overrides: object) -> GeneralistTokenClaims:
    """HYPE as Yahoo's stored fundamentals actually held it."""

    values: dict[str, object] = {
        "source": "Yahoo Finance",
        "observed_at": READ,
        "market_cap": 8_105.0,
        "circulating_supply": 1_500_000_000.0,
        "inception": datetime(2020, 12, 29, tzinfo=UTC),
    }

    values.update(overrides)

    return GeneralistTokenClaims(**values)  # type: ignore[arg-type]


def standing_of(outcome, fact):
    held = outcome.fact(fact)
    assert held is not None, fact
    return held.standing


# ── the HYPE acceptance case ────────────────────────────────────────


def test_the_8105_dollar_market_cap_does_not_survive() -> None:
    """The defective claim is not canonical, and it does not disappear."""

    outcome = judge("HYPE", native(), yahoo())

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.value == 18_260_000_000.0
    assert market_cap.source == "TokenInsight"

    # The rejected reading is retained with its reason — the trust
    # ledger, not a silent replacement.
    rejected = [item for item in outcome.rejected if item.fact == "market_cap"]

    assert len(rejected) == 1
    assert rejected[0].source == "Yahoo Finance"
    assert rejected[0].stated == "$8,105"
    assert "conflicts with the corroborated market value" in rejected[0].because


def test_the_false_circulating_supply_is_rejected_too() -> None:
    outcome = judge("HYPE", native(), yahoo())

    circulating = outcome.fact("circulating_supply")

    assert circulating is not None
    assert circulating.standing is TokenFactStanding.ESTABLISHED
    assert circulating.value == 336_685_219.0

    rejected = [item for item in outcome.rejected if item.fact == "circulating_supply"]

    assert len(rejected) == 1
    assert rejected[0].stated == "1,500,000,000"


def test_the_six_year_history_never_becomes_an_age() -> None:
    """Unknown is preferable to an invented fact."""

    outcome = judge("HYPE", native(), yahoo())

    age = outcome.fact("project_age")

    assert age is not None
    assert age.standing is TokenFactStanding.ABSENT
    assert age.value is None
    assert age.because is not None
    assert "Unknown is the honest answer" in age.because

    # The date claim is in the ledger with the semantic reason.
    rejected = [item for item in outcome.rejected if item.fact == "project_age"]

    assert len(rejected) == 1
    assert rejected[0].stated == "2020-12-29"
    assert "never established" in rejected[0].because


def test_a_disagreeing_yahoo_forfeits_the_volume_gate() -> None:
    """A source shown wrong about the instrument keeps no sibling authority."""

    outcome = judge("HYPE", native(), yahoo())

    assert outcome.yahoo_market_cap_corroborated is False


def test_hypes_dilution_context_is_established_arithmetic() -> None:
    """FDV coheres with price × max, so the issuance story is measurable."""

    outcome = judge("HYPE", native(), yahoo())

    assert standing_of(outcome, "max_supply") is TokenFactStanding.ESTABLISHED
    assert (
        standing_of(outcome, "fully_diluted_valuation") is TokenFactStanding.ESTABLISHED
    )

    assert outcome.issued_share is not None
    assert round(outcome.issued_share, 3) == 0.337

    assert outcome.fdv_to_market_cap is not None
    assert round(outcome.fdv_to_market_cap, 1) == 3.0


# ── corroboration, the BTC shape ────────────────────────────────────


def test_two_agreeing_sources_corroborate_and_open_the_volume_gate() -> None:
    outcome = judge(
        "BTC",
        native(
            symbol="BTC",
            provider_id="bitcoin",
            price=65_158.68,
            market_cap=1_307_620_300_898.0,
            circulating_supply=20_068_225.0,
            max_supply=21_000_000.0,
            fully_diluted_valuation=1_368_332_360_679.0,
        ),
        yahoo(
            market_cap=1_308_328_460_288.0,
            circulating_supply=20_067_944.0,
            inception=None,
        ),
    )

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.because is not None
    assert "independently reports the same value" in market_cap.because

    assert outcome.yahoo_market_cap_corroborated is True
    assert outcome.rejected == ()


# ── single-source establishment, the TAO shape ──────────────────────


def test_a_native_only_reading_is_established_by_its_own_arithmetic() -> None:
    """Yahoo holds zeros for TAO — zeros are absence, never a claim."""

    outcome = judge(
        "TAO",
        native(
            symbol="TAO",
            provider_id="bittensor",
            price=208.0,
            market_cap=1_798_121_936.0,
            circulating_supply=8_644_817.0,
            max_supply=21_000_000.0,
            fully_diluted_valuation=4_368_000_000.0,
        ),
        None,
    )

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.because is not None
    assert "No second source reports one" in market_cap.because

    # Nothing corroborated Yahoo, because Yahoo claimed nothing.
    assert outcome.yahoo_market_cap_corroborated is False


# ── the integrity checks themselves ─────────────────────────────────


def test_an_incoherent_triad_rejects_all_three_figures() -> None:
    """Arithmetic cannot say which figure lied, so none survives."""

    outcome = judge(
        "HYPE",
        native(market_cap=2_000_000_000.0),  # price × circ says ~18.3bn
        None,
    )

    assert standing_of(outcome, "market_cap") is TokenFactStanding.ABSENT
    assert standing_of(outcome, "price") is TokenFactStanding.ABSENT
    assert standing_of(outcome, "circulating_supply") is TokenFactStanding.ABSENT

    rejected = {item.fact for item in outcome.rejected}

    assert {"market_cap", "price", "circulating_supply"} <= rejected

    reasons = {item.because for item in outcome.rejected if item.fact == "market_cap"}

    assert any("arithmetic inconsistency" in reason for reason in reasons)


def test_more_circulating_than_maximum_rejects_the_pair() -> None:
    outcome = judge(
        "HYPE",
        native(
            circulating_supply=1_200_000_000.0,
            market_cap=1_200_000_000.0 * 54.23,
            fully_diluted_valuation=None,
        ),
        None,
    )

    assert standing_of(outcome, "max_supply") is TokenFactStanding.ABSENT

    rejected = {item.fact for item in outcome.rejected}

    assert "max_supply" in rejected
    assert "circulating_supply" in rejected


def test_an_fdv_that_fails_its_own_arithmetic_is_rejected() -> None:
    outcome = judge(
        "HYPE",
        native(fully_diluted_valuation=9_000_000_000.0),  # price × max ≈ 54.2bn
        None,
    )

    fdv = outcome.fact("fully_diluted_valuation")

    assert fdv is not None
    assert fdv.standing is TokenFactStanding.ABSENT

    rejected = [
        item for item in outcome.rejected if item.fact == "fully_diluted_valuation"
    ]

    assert len(rejected) == 1
    assert "arithmetic inconsistency" in rejected[0].because


def test_identity_mismatch_rejects_the_whole_native_reading() -> None:
    """An answer about another token establishes nothing about this one."""

    outcome = judge("HYPE", native(symbol="SUPREME"), yahoo())

    # Nothing native survives; Yahoo's figures stand only as claims.
    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.CLAIMED
    assert market_cap.source == "Yahoo Finance"

    assert any("identity mismatch" in item.because for item in outcome.rejected)


def test_timing_differences_inside_the_tolerances_still_corroborate() -> None:
    """Two instants of a moving market are never exactly equal."""

    outcome = judge(
        "BTC",
        native(
            symbol="BTC",
            provider_id="bitcoin",
            price=65_158.68,
            market_cap=1_307_620_300_898.0,
            circulating_supply=20_068_225.0,
            max_supply=21_000_000.0,
            fully_diluted_valuation=1_368_332_360_679.0,
        ),
        yahoo(
            # 4% apart: a timing difference, not a conflict.
            market_cap=1_307_620_300_898.0 * 1.04,
            circulating_supply=None,
            inception=None,
        ),
    )

    assert outcome.yahoo_market_cap_corroborated is True
    assert outcome.rejected == ()


# ── claims that nothing can check stay claims ───────────────────────


def test_bare_figures_are_claims_and_never_facts() -> None:
    outcome = judge("HYPE", native(), None)

    for fact in ("rank", "spot_volume_24h", "spot_volume_change_24h"):
        held = outcome.fact(fact)

        assert held is not None, fact
        assert held.standing is TokenFactStanding.CLAIMED, fact

        # A claim is never served as an established value.
        assert held.established_value is None, fact


def test_spot_volume_keeps_its_narrow_meaning() -> None:
    """Tracked spot volume is not total volume, and says so."""

    outcome = judge("HYPE", native(), None)

    spot = outcome.fact("spot_volume_24h")

    assert spot is not None
    assert spot.because is not None
    assert "not mapped onto" in spot.because


def test_derived_arithmetic_requires_established_inputs() -> None:
    """A share of a claim would be a claim wearing arithmetic's authority."""

    outcome = judge(
        "HYPE",
        native(fully_diluted_valuation=None),  # max supply stays a claim
        None,
    )

    assert standing_of(outcome, "max_supply") is TokenFactStanding.CLAIMED
    assert outcome.issued_share is None


# ── nothing at all ──────────────────────────────────────────────────


def test_no_sources_at_all_is_all_absences_with_reasons() -> None:
    outcome = judge("HYPE", None, None)

    for fact in outcome.facts:
        assert fact.standing is TokenFactStanding.ABSENT, fact.fact
        assert fact.because, fact.fact

    assert outcome.rejected == ()
    assert outcome.yahoo_market_cap_corroborated is False
