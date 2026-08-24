"""The owner's three amendments to PR #231, pinned.

The ruling of 2026-08-21 approved the slice subject to three
corrections, each of which is a statement this platform was about to
make and could not support:

2. **The judged crypto price stays**, and must identify the token, the
   crypto-native provider's id, the claimants that established the
   value, the observation time, and the rule that admitted it. Serving
   the pool's price while naming one vendor reports a corroborated
   figure as one source's number.

3. **The capital-envelope crypto refusal** must say that an established
   crypto-native price is available and that v1 does not size
   cryptocurrencies. *"No market quote for HYPE was acquired this
   cycle"* became false the moment a token was priced from the pool,
   and the absence of an admissible vendor series must never overwrite
   the presence of an established spot price.

4. **A conviction never states a count without its expectation.** *The
   mean of the 5 scores measured* is a claim that five families spoke;
   where four did, the reader has no way to tell.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.cio.artificial_cio import SCORE_FAMILIES, ArtificialCIO
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.capital_envelope import (
    EnvelopeKind,
    PortfolioCapacity,
    PriceObservation,
    envelope_for,
    price_observation_for,
    security_risk_ceiling_for,
)
from app.domain.capital_policy import CapitalPolicy, ReducePolicy
from app.domain.company_facts import CompanyFacts
from app.domain.provenance import Provenance
from app.domain.strategic_allocation import (
    AllocationBand,
    HardLimits,
    StrategicAllocation,
)
from app.domain.token_fact_validation import ESTABLISHMENT_RULE
from app.domain.token_facts import TokenFact, TokenFactStanding

MOMENT = datetime(2026, 8, 20, 14, 29, 38, tzinfo=UTC)

#: The active policy's hard limits — minimum cash and maximum crypto.
#: The strategy file states these once and every reader receives them;
#: they are not constants of the allocation module, which is precisely
#: the second authority this amendment removed.
OWNER_LIMITS = HardLimits(minimum_cash_pct=15.0, maximum_crypto_pct=40.0)

#: The owner's strategic allocation of 2026-08-24, as the tracked
#: strategy states it: four targets totalling 100%, each inside its own
#: operating range.
OWNER_ALLOCATION = StrategicAllocation(
    stocks=AllocationBand(
        asset="stocks", target_pct=35.0, minimum_pct=25.0, maximum_pct=45.0
    ),
    etfs=AllocationBand(
        asset="etfs", target_pct=15.0, minimum_pct=10.0, maximum_pct=25.0
    ),
    crypto=AllocationBand(
        asset="crypto", target_pct=25.0, minimum_pct=15.0, maximum_pct=40.0
    ),
    cash=AllocationBand(
        asset="cash", target_pct=25.0, minimum_pct=15.0, maximum_pct=45.0
    ),
    # The hard limits the active policy states — not a second copy of
    # them. These are what `minimum_cash_pct` and `maximum_crypto_pct`
    # say in the strategy document this suite loads.
    limits=OWNER_LIMITS,
)


# ── amendment 2: the judged price says who judged it ────────────────


def token_facts(**overrides) -> CompanyFacts:
    values = dict(
        instrument_id=1,
        symbol="HYPE",
        name="Hyperliquid",
        asset_type="crypto",
        exchange="",
        current_price=73.44,
        price_identity="hyperliquid",
        price_claimants=("TokenInsight", "CoinGecko"),
        price_rule=ESTABLISHMENT_RULE,
        price_reading=Provenance(
            source="TokenInsight",
            observed_at=MOMENT,
            # TokenInsight states no observation time — measured
            # 2026-08-21, see `test_token_facts_provider`. `MOMENT` is
            # the receipt time under the amendment below.
            observation_stated=False,
        ),
    )
    values.update(overrides)

    return CompanyFacts(**values)  # type: ignore[arg-type]


def test_a_judged_price_identifies_all_five_things_the_ruling_names() -> None:
    """One sentence, composed in the domain, carrying the whole ruling.

    Amended 2026-08-21. The ruling's fifth element is *when the figure
    was read*, and this test used to satisfy it with the literal string
    "observed 2026-08-20 14:29 UTC" — built from TokenInsight's
    `market_data.last_updated`, which was then measured not to advance
    with the price it accompanies. The element stands; what changed is
    that TokenInsight cannot supply it, so the sentence prints
    MOVRvest's receipt time and says that is what it is.
    """

    stated = token_facts().price_provenance

    assert stated is not None

    # The token, and the crypto-native provider's own identifier for it —
    # the thing a pair listing cannot supply.
    assert "HYPE (hyperliquid)" in stated

    # Both claimants. The deviation the owner approved is that the price
    # is the *pool's*, so naming only TokenInsight would report a
    # corroborated figure as one vendor's number.
    assert "TokenInsight and CoinGecko" in stated

    # When it was read, labelled as the clock it actually is — and the
    # rule that admitted it.
    assert "received 2026-08-20 14:29 UTC" in stated
    assert "TokenInsight states no observation time for it" in stated
    assert ESTABLISHMENT_RULE in stated

    # The word the amendment withdraws. A receipt time printed as an
    # observation is the whole defect, and it must not reappear by any
    # route — including a future source that happens to be named first.
    assert "observed 2026-08-20 14:29 UTC" not in stated


def test_a_source_that_states_an_observation_time_is_quoted_as_observing() -> None:
    """The amendment narrows the claim; it does not withdraw it everywhere.

    CoinGecko's `last_updated` *does* advance — measured minutes behind
    the fetch on the same day TokenInsight's stood 16.5 hours behind it.
    A source that states an observation time is still quoted as stating
    one, so the receipt wording marks a real difference between sources
    rather than becoming the platform's uniform hedge.
    """

    stated = token_facts(
        price_claimants=("CoinGecko",),
        price_reading=Provenance(source="CoinGecko", observed_at=MOMENT),
    ).price_provenance

    assert stated is not None
    assert "observed 2026-08-20 14:29 UTC" in stated
    assert "receipt time" not in stated


def test_a_vendor_quote_is_never_dressed_in_the_gate_s_sentence() -> None:
    """An equity's price was admitted by no rule, and says so by saying nothing.

    The sentence claims a corroboration. A security quoted under its own
    ticker at a venue had none performed, so it gets no sentence rather
    than a sentence with an empty middle.
    """

    equity = token_facts(
        symbol="AMD",
        name="AMD",
        asset_type="stock",
        price_identity=None,
        price_claimants=(),
        price_rule=None,
    )

    assert equity.price_provenance is None


def test_the_establishing_claimants_travel_from_the_gate_as_a_list() -> None:
    """Structurally, never parsed back out of the account sentence."""

    fact = TokenFact(
        fact="price",
        standing=TokenFactStanding.ESTABLISHED,
        value=73.44,
        source="TokenInsight",
        observed_at=MOMENT,
        because="independently corroborated by CoinGecko.",
        claimants=("TokenInsight", "CoinGecko"),
        rule=ESTABLISHMENT_RULE,
    )

    assert fact.claimants[0] == "TokenInsight", "the served figure's source first"
    assert fact.rule == ESTABLISHMENT_RULE


def test_a_standing_short_of_established_names_no_claimants_and_no_rule() -> None:
    """Nothing agreed, so nothing established it, so nothing admitted it."""

    conflicted = TokenFact(
        fact="price",
        standing=TokenFactStanding.CONFLICTED,
        value=None,
        because="two coherent claimants disagree materially.",
    )

    assert conflicted.claimants == ()
    assert conflicted.rule is None
    assert conflicted.established_value is None


# ── amendment 3: price availability is not sizing support ───────────


def policy() -> CapitalPolicy:
    return CapitalPolicy(
        starter_max_total_position_pct=1.0,
        standard_initial_position_pct=3.0,
        max_add_weight_change_pct=2.0,
        max_single_position_pct=20.0,
        # The owner's own limits, and the same pair `OWNER_ALLOCATION`
        # was validated against. Carrying the pre-ruling 65/40 here
        # while the allocation held 40/15 is exactly the two-authority
        # state `CapitalPolicy` now refuses — a policy cannot fund
        # against one hard limit while its plan was checked against
        # another.
        max_crypto_pct=40.0,
        target_cash_pct=25.0,
        minimum_cash_pct=15.0,
        price_max_age_minutes=15.0,
        portfolio_max_age_minutes=15.0,
        maximum_acceptable_drawdown_pct=20.0,
        reduce_policy=ReducePolicy.RESTORE_TO_POLICY_CAP,
        security_risk_high_max_total_pct=2.0,
        security_risk_severe_max_total_pct=1.0,
        security_risk_unmeasured_max_total_pct=1.0,
        allocation=OWNER_ALLOCATION,
        source="investor_strategy.json",
        version="testversion1",
    )


def crypto_envelope(*, established: bool, price: PriceObservation):
    return envelope_for(
        symbol="HYPE",
        course="open",
        policy=policy(),
        capacity=PortfolioCapacity(
            funding_room_pct=10.0,
            concentration_room_pct=20.0,
            capacity_pct=10.0,
            current_weight_pct=0.0,
        ),
        named_gaps=(),
        quality_authority=None,
        hard_floor_passes=True,
        price=price,
        portfolio_as_of="received at 2026-08-20 14:00 UTC",
        drawdown_depth_pct=None,
        is_equity=False,
        security_risk=security_risk_ceiling_for(
            policy=policy(),
            volatility_band=None,
            drawdown_band=None,
        ),
        crypto_price_established=established,
    )


def test_an_established_crypto_price_is_stated_beside_the_sizing_refusal() -> None:
    """The owner's substance: available price, no sizing, no magnitude."""

    envelope = crypto_envelope(
        established=True,
        # The vendor has nothing for this token — its `HYPE-USD` is
        # another token, so the listing is refused and no series exists.
        price=price_observation_for(
            symbol="HYPE",
            quote=None,
            policy=policy(),
            now=MOMENT,
        ),
    )

    assert envelope.kind is EnvelopeKind.REFUSED

    stated = envelope.stated

    assert "an established crypto-native price is available" in stated
    assert "does not size cryptocurrencies" in stated
    assert "price availability is not sizing support" in stated

    # No magnitude is produced, and none could be: a refusal carries no
    # figure at all, which its own constructor enforces.
    assert envelope.final_pct is None


def test_the_missing_vendor_series_never_overwrites_the_established_price() -> None:
    """Precedence, pinned.

    The vendor's refusal for HYPE words itself *"no market quote for
    HYPE was acquired this cycle"*. That sentence is false about a token
    the crypto-native gate priced, and the only thing keeping it out of
    the envelope is that the crypto branch is evaluated first.
    """

    vendor = price_observation_for(
        symbol="HYPE",
        quote=None,
        policy=policy(),
        now=MOMENT,
    )

    assert "no market quote for HYPE was acquired this cycle" in vendor.refused_because

    envelope = crypto_envelope(established=True, price=vendor)

    assert "no market quote" not in envelope.stated
    assert "was acquired this cycle" not in envelope.stated


def test_a_token_with_no_established_price_claims_none() -> None:
    """The refusal says less, not more, where the gate established nothing."""

    envelope = crypto_envelope(
        established=False,
        price=price_observation_for(
            symbol="HYPE",
            quote=None,
            policy=policy(),
            now=MOMENT,
        ),
    )

    assert envelope.kind is EnvelopeKind.REFUSED
    assert "an established crypto-native price is available" not in envelope.stated
    assert "crypto remains outside the equity capital envelope" in envelope.stated


def test_an_established_price_admits_nothing_into_sizing() -> None:
    """Both crypto refusals are refusals, and neither carries a figure.

    The ruling permits the *wording* to change and nothing else. An
    established price does not produce a ceiling, a magnitude, or a
    volatility, liquidity or executability reading — so the two
    envelopes differ in exactly one field.
    """

    price = price_observation_for(
        symbol="HYPE",
        quote=None,
        policy=policy(),
        now=MOMENT,
    )

    with_price = crypto_envelope(established=True, price=price)
    without = crypto_envelope(established=False, price=price)

    assert with_price.kind is without.kind is EnvelopeKind.REFUSED
    assert with_price.final_pct is None and without.final_pct is None
    assert with_price.binding_constraint == without.binding_constraint == ""

    differing = {
        field
        for field in with_price.__slots__
        if getattr(with_price, field) != getattr(without, field)
    }

    assert differing == {"because"}, "wording only, per the ruling"


# ── amendment 4: a count is stated against its expectation ──────────


def scored(**overrides) -> DecisionEvidence:
    values: dict[str, object] = {
        "symbol": "AMD",
        "quality_score": 62,
        "evidence_score": 60,
        "valuation_score": 25,
        "risk_score": 85,
        "portfolio_fit_score": 60,
        "strengths": ("Large-cap company.",),
    }
    values.update(overrides)

    return DecisionEvidence(**values)  # type: ignore[arg-type]


def test_five_is_printed_only_when_five_families_participated() -> None:
    decision = ArtificialCIO().decide(scored())

    assert decision.conviction_participating == 5
    assert decision.conviction_expected == 5
    assert "computed from 5 of 5 score families" in decision.conviction_basis


def test_a_missing_family_changes_the_count_and_is_named() -> None:
    """The owner's example: 4 of 5, and which one did not speak.

    Business quality is the family the #232 research found missing or
    proxied for 60 of 64 stored equities, so this is the ordinary case
    rather than the exotic one.
    """

    decision = ArtificialCIO().decide(scored(quality_score=None))

    assert decision.conviction_participating == 4
    assert decision.conviction_expected == 5
    assert decision.conviction_absent_families == ("business quality",)

    basis = decision.conviction_basis

    assert "computed from 4 of 5 score families" in basis
    assert "No business quality score participated" in basis
    assert "an absent score is missing, not poor" in basis
    assert "5 scores" not in basis


def test_every_absent_family_is_named_rather_than_counted() -> None:
    decision = ArtificialCIO().decide(
        scored(quality_score=None, valuation_score=None),
    )

    assert decision.conviction_absent_families == ("business quality", "valuation")
    assert (
        "No business quality or valuation score participated"
        in decision.conviction_basis
    )


def test_a_complete_reading_states_no_coverage_limit() -> None:
    """A sentence that always hedges teaches a reader to ignore the hedge."""

    decision = ArtificialCIO().decide(scored())

    assert "participated" not in decision.conviction_basis
    assert decision.conviction_absent_families == ()


def test_the_family_names_are_pinned_to_the_scores_they_stand_for() -> None:
    """Positional pairing, so an absence is never attributed to the wrong one."""

    assert SCORE_FAMILIES == (
        "business quality",
        "evidence",
        "valuation",
        "portfolio fit",
        "safety",
    )

    # Each family, absent alone, names itself and nothing else. Evidence
    # is not among them: `evidence_score` is required on the model, so
    # it cannot be absent and there is no case to pin.
    for family, field in (
        ("business quality", "quality_score"),
        ("valuation", "valuation_score"),
        ("portfolio fit", "portfolio_fit_score"),
        ("safety", "risk_score"),
    ):
        decision = ArtificialCIO().decide(scored(**{field: None}))

        assert decision.conviction_absent_families == (family,)


def test_the_arithmetic_is_untouched_by_the_wording() -> None:
    """#232's ruling reserves the conviction arithmetic for its own slice.

    An absent family is still omitted from the mean — from the numerator
    and the denominator alike — and the state cap still applies over the
    top. The correction is that the sentence now says how many spoke.
    """

    clean = dict(
        quality_score=80,
        evidence_score=80,
        valuation_score=80,
        risk_score=20,
        portfolio_fit_score=80,
    )

    for overrides, expected_scores in (
        (clean, (80, 80, 80, 80, 80)),
        ({**clean, "quality_score": None}, (80, 80, 80, 80)),
    ):
        decision = ArtificialCIO().decide(scored(**overrides))

        mean = round(sum(expected_scores) / len(expected_scores))
        cap = ArtificialCIO.CONVICTION_LIMITS[decision.state]

        assert decision.conviction == min(mean, cap)
        assert decision.conviction_participating == len(expected_scores)


def test_the_state_cap_is_never_reported_as_a_participation_count() -> None:
    """The REJECT cap is 40; five families still spoke for it.

    The route to REJECT has changed twice — the 2026-08-21 cutover
    removed the severity rejection and the 2026-08-24 ruling the
    company vote's veto, leaving the hard policy gate. #231's
    amendment is unaffected either way: it is about never printing a
    count without its expectation, whichever gate produced the state.
    """

    decision = ArtificialCIO().decide(scored(hard_reject=True))

    assert decision.state is DecisionState.REJECT
    assert decision.conviction == ArtificialCIO.CONVICTION_LIMITS[DecisionState.REJECT]
    assert decision.conviction_participating == 5
    assert "capped at 40 by the REJECT state" in decision.conviction_basis
