"""A pool of claims, judged — agreement inside one provider is not corroboration.

The S1 acceptance cases live here. ARB is the staleness case: a vendor
whose market value reproduces its own frozen circulating supply passes
every intra-source check and is still wrong by 4×. HYPE is the
methodology case: two coherent vendors 33–51% apart on what counts as
circulating. Under the pool, the first cannot establish alone and the
second is an honest conflict — and Yahoo's $8,105 still lands in the
ledger on the way.
"""

from datetime import UTC, datetime

from app.domain.provenance import Provenance
from app.domain.token_fact_validation import (
    TokenClaimSet,
    judge,
)
from app.domain.token_facts import TokenFactStanding

READ = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)


def claim_set(source: str, **overrides: object) -> TokenClaimSet:
    values: dict[str, object] = {
        "source": source,
        "read": Provenance(source=source, observed_at=READ),
    }

    values.update(overrides)

    return TokenClaimSet(**values)  # type: ignore[arg-type]


def tokeninsight(**overrides: object) -> TokenClaimSet:
    """Hyperliquid as TokenInsight reported it — internally coherent."""

    values: dict[str, object] = {
        "symbol_echo": "HYPE",
        "provider_id": "hyperliquid",
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

    return claim_set("TokenInsight", **values)


def coingecko(**overrides: object) -> TokenClaimSet:
    """Hyperliquid as CoinGecko reported it — also coherent, 33% away."""

    values: dict[str, object] = {
        "symbol_echo": "HYPE",
        "provider_id": "hyperliquid",
        "price": 54.63,
        "market_cap": 12_150_000_000.0,
        "circulating_supply": 222_445_714.0,
        "total_supply": 955_307_079.0,
        "max_supply": 1_000_000_000.0,
        "fully_diluted_valuation": 54_630_000_000.0,
        "rank": 10.0,
        "market_volume_24h": 163_000_000.0,
    }

    values.update(overrides)

    return claim_set("CoinGecko", **values)


def yahoo(**overrides: object) -> TokenClaimSet:
    """HYPE as Yahoo's stored fundamentals held it — the defective row."""

    values: dict[str, object] = {
        "market_cap": 8_105.0,
        "circulating_supply": 1_500_000_000.0,
        "inception": datetime(2020, 12, 29, tzinfo=UTC),
    }

    values.update(overrides)

    return claim_set("Yahoo Finance", **values)


def standing_of(outcome, fact):
    held = outcome.fact(fact)
    assert held is not None, fact
    return held.standing


# ── acceptance 1: N claims, not two slots ───────────────────────────


def test_the_pool_accepts_any_number_of_claim_sets() -> None:
    for sets in ([], [tokeninsight()], [tokeninsight(), coingecko(), yahoo()]):
        outcome = judge("HYPE", sets)

        assert outcome.symbol == "HYPE"
        assert len(outcome.facts) > 0


# ── acceptance 4: ARB — staleness cannot establish alone ────────────


def test_a_coherent_stale_vendor_cannot_establish_by_itself() -> None:
    """Agreement inside one provider is not corroboration.

    TokenInsight's ARB row reproduces its own arithmetic exactly —
    price × the 2023 launch float — and under the pool that earns a
    claim, never a fact.
    """

    stale = claim_set(
        "TokenInsight",
        symbol_echo="ARB",
        provider_id="arbitrum",
        price=0.08,
        market_cap=102_000_000.0,
        circulating_supply=1_275_000_000.0,
        max_supply=10_000_000_000.0,
        fully_diluted_valuation=800_000_000.0,
    )

    outcome = judge("ARB", [stale])

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.CLAIMED
    assert market_cap.because is not None
    assert "not corroboration" in market_cap.because

    # A claim never reaches consumers as an established value.
    assert outcome.established_value("market_cap") is None


def test_a_second_credible_claimant_exposes_the_staleness() -> None:
    """ARB with both vendors: the market value is an honest conflict."""

    stale = claim_set(
        "TokenInsight",
        symbol_echo="ARB",
        provider_id="arbitrum",
        price=0.0799,
        market_cap=101_973_146.0,
        circulating_supply=1_275_000_000.0,
        max_supply=10_000_000_000.0,
        fully_diluted_valuation=799_000_000.0,
    )

    live = claim_set(
        "CoinGecko",
        symbol_echo="ARB",
        provider_id="arbitrum",
        price=0.0801,
        market_cap=530_000_000.0,
        circulating_supply=6_614_056_381.0,
        max_supply=10_000_000_000.0,
        fully_diluted_valuation=801_000_000.0,
    )

    outcome = judge("ARB", [stale, live])

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.CONFLICTED
    assert market_cap.value is None
    assert market_cap.because is not None
    assert "TokenInsight" in market_cap.because
    assert "CoinGecko" in market_cap.because

    assert standing_of(outcome, "circulating_supply") is (TokenFactStanding.CONFLICTED)

    # The figures the vendors AGREE on still establish: the price is
    # real; the supply is the dispute; the market value inherits it.
    assert standing_of(outcome, "price") is TokenFactStanding.ESTABLISHED
    assert standing_of(outcome, "max_supply") is TokenFactStanding.ESTABLISHED


# ── acceptance 5: HYPE — methodology conflict, no winner ────────────


def test_hype_circulating_methodology_is_an_honest_conflict() -> None:
    outcome = judge("HYPE", [tokeninsight(), coingecko()])

    for fact in ("market_cap", "circulating_supply"):
        held = outcome.fact(fact)

        assert held is not None, fact
        assert held.standing is TokenFactStanding.CONFLICTED, fact

        # No value served, no average, both claims named with times.
        assert held.value is None
        assert held.because is not None
        assert "TokenInsight" in held.because
        assert "CoinGecko" in held.because
        assert "count the concept differently" in held.because

    # What they agree on is established: the cap, and FDV within
    # tolerance. The dilution *ratio* stays uncomputable — it needs an
    # established market value.
    assert standing_of(outcome, "max_supply") is TokenFactStanding.ESTABLISHED
    assert (
        standing_of(outcome, "fully_diluted_valuation") is TokenFactStanding.ESTABLISHED
    )
    assert outcome.fdv_to_market_cap is None
    assert outcome.issued_share is None


def test_the_8105_reading_is_still_rejected_on_the_way() -> None:
    """Acceptance 8: the trust ledger survives the pool.

    Yahoo's figure is not a third methodology — it is six orders from
    both coherent claimants with no arithmetic of its own, and it is
    rejected before conflict is even asked. The genuine two-way
    methodology conflict remains.
    """

    outcome = judge("HYPE", [tokeninsight(), coingecko(), yahoo()])

    rejected = [item for item in outcome.rejected if item.fact == "market_cap"]

    assert len(rejected) == 1
    assert rejected[0].source == "Yahoo Finance"
    assert rejected[0].stated == "$8,105"
    assert "no arithmetic of its own" in rejected[0].because

    assert standing_of(outcome, "market_cap") is TokenFactStanding.CONFLICTED


def test_the_inception_field_is_rejected_from_any_set() -> None:
    outcome = judge("HYPE", [tokeninsight(), coingecko(), yahoo()])

    age = outcome.fact("project_age")

    assert age is not None
    assert age.standing is TokenFactStanding.ABSENT

    rejected = [item for item in outcome.rejected if item.fact == "project_age"]

    assert len(rejected) == 1
    assert rejected[0].stated == "2020-12-29"


# ── acceptance 6: majors establish across the pool ──────────────────


def bitcoin_sets() -> list[TokenClaimSet]:
    return [
        claim_set(
            "TokenInsight",
            symbol_echo="BTC",
            provider_id="bitcoin",
            price=65_158.68,
            market_cap=1_307_620_300_898.0,
            circulating_supply=20_068_225.0,
            max_supply=21_000_000.0,
            fully_diluted_valuation=1_368_332_360_679.0,
            rank=1.0,
            spot_volume_24h=3_657_142_498.0,
        ),
        claim_set(
            "CoinGecko",
            symbol_echo="BTC",
            provider_id="bitcoin",
            price=65_288.0,
            market_cap=1_310_220_000_000.0,
            circulating_supply=20_068_243.0,
            total_supply=20_068_243.0,
            max_supply=21_000_000.0,
            fully_diluted_valuation=1_371_048_000_000.0,
            rank=1.0,
            market_volume_24h=14_200_000_000.0,
        ),
        claim_set(
            "Yahoo Finance",
            market_cap=1_308_328_460_288.0,
            circulating_supply=20_067_944.0,
        ),
    ]


def test_agreeing_majors_establish_with_the_corroborators_named() -> None:
    outcome = judge("BTC", bitcoin_sets())

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.because is not None
    assert "CoinGecko" in market_cap.because
    assert "Yahoo Finance" in market_cap.because

    # The printed figure is the crypto-native claimant's — a stated
    # display choice inside the agreement corridor, not an authority.
    assert market_cap.value == 1_307_620_300_898.0
    assert market_cap.source == "TokenInsight"

    for fact in ("price", "circulating_supply", "max_supply"):
        assert standing_of(outcome, fact) is TokenFactStanding.ESTABLISHED, fact

    assert outcome.rejected == ()
    assert outcome.yahoo_market_cap_corroborated is True


def test_a_conflicted_market_value_closes_the_volume_gate() -> None:
    outcome = judge("HYPE", [tokeninsight(), coingecko(), yahoo()])

    assert outcome.yahoo_market_cap_corroborated is False


# ── acceptance 12: a third fake provider joins without validator changes ──


def test_a_fake_third_provider_joins_the_pool_unchanged() -> None:
    """A new claimant is a new TokenClaimSet, and nothing else.

    The validator has no provider names in its establishment rules:
    three agreeing sources establish exactly as two do, with the
    newcomer named among the corroborators.
    """

    fake = claim_set(
        "FakeLlama",
        symbol_echo="BTC",
        price=65_200.0,
        market_cap=1_308_500_000_000.0,
        circulating_supply=20_068_100.0,
    )

    outcome = judge("BTC", [*bitcoin_sets(), fake])

    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.ESTABLISHED
    assert market_cap.because is not None
    assert "FakeLlama" in market_cap.because


def test_a_fake_provider_can_also_be_the_dissenter() -> None:
    """And when it materially disagrees, the fact conflicts — no
    precedence, hidden or otherwise, resolves it."""

    dissenter = claim_set(
        "FakeLlama",
        symbol_echo="BTC",
        price=52_000.0,
        market_cap=1_043_500_000_000.0,
        circulating_supply=20_067_000.0,
    )

    outcome = judge("BTC", [*bitcoin_sets(), dissenter])

    assert standing_of(outcome, "market_cap") is TokenFactStanding.CONFLICTED


# ── the intra-set rules still hold ──────────────────────────────────


def test_an_incoherent_triad_still_rejects_all_three_figures() -> None:
    outcome = judge(
        "HYPE",
        [tokeninsight(market_cap=2_000_000_000.0)],
    )

    for fact in ("market_cap", "price", "circulating_supply"):
        assert standing_of(outcome, fact) is TokenFactStanding.ABSENT, fact

    rejected = {item.fact for item in outcome.rejected}

    assert {"market_cap", "price", "circulating_supply"} <= rejected


def test_supply_chain_order_is_checked_within_a_set() -> None:
    """circulating ≤ total ≤ maximum, inside one source's own claims."""

    outcome = judge(
        "HYPE",
        [
            coingecko(
                total_supply=100_000_000.0,  # below its own circulating
                fully_diluted_valuation=None,
            )
        ],
    )

    rejected = {item.fact for item in outcome.rejected}

    assert "circulating_supply" in rejected
    assert "total_supply" in rejected


def test_identity_mismatch_rejects_the_whole_set() -> None:
    outcome = judge(
        "HYPE",
        [tokeninsight(symbol_echo="SUPREME"), coingecko()],
    )

    # Only CoinGecko's claims remain — single source, so claims only.
    market_cap = outcome.fact("market_cap")

    assert market_cap is not None
    assert market_cap.standing is TokenFactStanding.CLAIMED
    assert market_cap.source == "CoinGecko"

    assert any("identity mismatch" in item.because for item in outcome.rejected)


def test_timing_differences_inside_tolerance_still_corroborate() -> None:
    sets = bitcoin_sets()

    nudged = claim_set(
        "CoinGecko",
        symbol_echo="BTC",
        price=sets[0].price * 1.04 if sets[0].price else None,
        market_cap=(sets[0].market_cap or 0) * 1.04,
        circulating_supply=sets[0].circulating_supply,
        max_supply=21_000_000.0,
        fully_diluted_valuation=(sets[0].fully_diluted_valuation or 0) * 1.04,
    )

    outcome = judge("BTC", [sets[0], nudged])

    assert standing_of(outcome, "market_cap") is TokenFactStanding.ESTABLISHED


# ── vendor-scoped figures never pool ────────────────────────────────


def test_scoped_figures_stay_claims_even_when_vendors_agree() -> None:
    """Two vendors both ranking BTC #1 is a coincidence of universes."""

    outcome = judge("BTC", bitcoin_sets())

    rank = outcome.fact("rank")

    assert rank is not None
    assert rank.standing is TokenFactStanding.CLAIMED
    assert rank.because is not None
    assert "never pooled" in rank.because

    spot = outcome.fact("spot_volume_24h")
    market_volume = outcome.fact("market_volume_24h")

    assert spot is not None and spot.standing is TokenFactStanding.CLAIMED
    assert spot.source == "TokenInsight"

    assert market_volume is not None
    assert market_volume.standing is TokenFactStanding.CLAIMED
    assert market_volume.source == "CoinGecko"
    assert market_volume.because is not None
    assert "vendor-defined universe" in market_volume.because


# ── derived arithmetic still demands established inputs ─────────────


def test_derived_ratios_require_established_inputs() -> None:
    outcome = judge("HYPE", [tokeninsight(), coingecko()])

    # Conflicted circulating and market value → no issued share, no
    # dilution ratio. A ratio over a conflict would be a conflict
    # wearing arithmetic's authority.
    assert outcome.issued_share is None
    assert outcome.fdv_to_market_cap is None

    corroborated = judge("BTC", bitcoin_sets())

    assert corroborated.issued_share is not None
    assert round(corroborated.issued_share, 3) == 0.956


# ── nothing at all ──────────────────────────────────────────────────


def test_no_sources_at_all_is_all_absences_with_reasons() -> None:
    outcome = judge("HYPE", [])

    for fact in outcome.facts:
        assert fact.standing is TokenFactStanding.ABSENT, fact.fact
        assert fact.because, fact.fact

    assert outcome.rejected == ()
    assert outcome.yahoo_market_cap_corroborated is False
