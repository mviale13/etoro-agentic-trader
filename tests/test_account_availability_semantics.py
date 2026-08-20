"""Unavailable cash stays unavailable, and the portfolio clock is receipt time.

Two factual boundaries, both approved for repair by the owner's ruling on
PR #222.

**Cash.** `AccountSnapshot.cash_usd` was already optional and
`PortfolioService` destroyed the distinction, so an account whose cash
eToro did not state was rendered as an account measurably holding none —
and the Capital Action Envelope then told the investor the portfolio had
no room. Absence now survives to every consumer.

**The clock.** `last_sync` is the moment MOVRvest received a successful
account response. eToro states no account observation time at all, so
that receipt clock may gate operationally and may never be worded as the
broker's observation time, the account `asOf`, the source timestamp or
the underlying snapshot time.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.portfolio_service import PortfolioService
from tests.test_portfolio_service import build_account

MOMENT = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def analyzed(cash: float | None, *, equity: float = 100_000.0) -> PortfolioSnapshot:
    return PortfolioService().analyze(
        build_account(equity=equity, cash=cash, invested=60_000.0, positions=3)
    )


# ── control 1: cash absent ──────────────────────────────────────────


def test_1a_absent_cash_reaches_the_snapshot_as_absent() -> None:
    snapshot = analyzed(None)

    assert snapshot.available_cash_usd is None
    assert snapshot.available_cash_eur is None
    assert snapshot.allocation.cash is None
    assert snapshot.liquidity_pct is None

    # Said, not merely omitted.
    assert any("could not be read" in flag for flag in snapshot.risk_flags)

    # And nothing else was harmed: the measured half is intact.
    assert snapshot.total_value == 100_000.0
    assert snapshot.invested_usd == 60_000.0


def test_1b_no_cash_based_numeric_claim_is_emitted() -> None:
    """Every cash-dependent number refuses; none is answered with a zero."""

    from app.application.brain.reasoning.portfolio_analyst import PortfolioAnalyst
    from app.application.brain.reasoning.risk_analyst import RiskAnalyst

    snapshot = analyzed(None)

    assert PortfolioAnalyst()._liquidity_score(snapshot) is None
    assert RiskAnalyst()._liquidity_risk(snapshot) is None


def test_1c_the_capital_envelope_refuses_rather_than_reporting_zero_capacity(
    tmp_path,
) -> None:
    from app.domain.capital_envelope import (
        EnvelopeKind,
        PortfolioObservation,
        QualityAuthority,
        capacity_for,
        envelope_for,
        price_observation_for,
    )
    from tests.test_capital_action_envelope import policy, quote_for

    fresh = PortfolioObservation(fresh=True, as_of="eToro account response received")

    capacity = capacity_for(
        policy=policy(),
        total_value=100_000.0,
        cash_pct=None,
        current_weight_pct=0.0,
        portfolio=fresh,
        broker_answered=True,
    )

    assert capacity.capacity_pct is None, "no ceiling is computed from an absence"
    assert "cash allocation could not be read" in capacity.refused_because

    envelope = envelope_for(
        symbol="KO",
        course="open",
        policy=policy(),
        capacity=capacity,
        named_gaps=(),
        quality_authority=QualityAuthority.GROUNDED,
        hard_floor_passes=True,
        price=price_observation_for(
            symbol="KO", quote=quote_for("KO"), policy=policy(), now=MOMENT
        ),
        portfolio_as_of="eToro account response received at 2026-08-20 11:58 UTC",
        drawdown_depth_pct=2.0,
        is_equity=True,
    )

    assert envelope.kind is EnvelopeKind.REFUSED
    assert envelope.kind is not EnvelopeKind.ZERO_CAPACITY, (
        "the repaired defect: absent cash used to render as no room at all"
    )
    assert envelope.final_pct is None
    assert "could not be read" in envelope.stated
    assert "no additional capacity" not in envelope.stated
    assert "non-capital course remains unchanged" in envelope.stated


def test_1d_the_rest_of_the_cycle_still_completes_without_cash() -> None:
    """Missing cash costs the cash claims, never the whole pass."""

    from app.services.policy_analyzer import PolicyAnalyzer
    from app.services.signal_service import SignalService
    from tests.test_brain_context import make_policy

    snapshot = analyzed(None)

    analysis = PolicyAnalyzer().analyze(snapshot, make_policy())

    # Every non-cash allocation is still compared.
    by_asset = {item.asset: item for item in analysis.allocations}

    assert by_asset["stocks"].difference is not None
    assert by_asset["cash"].difference is None
    assert by_asset["cash"].current is None

    # An unmeasured difference is never credited as compliance.
    assert analysis.compliant is False

    # And the signal pass runs, emitting no cash signal.
    signals = SignalService().analyze(snapshot, None)

    assert all(not signal.type.startswith("cash") for signal in signals)


# ── control 2: cash measured at zero ────────────────────────────────


def test_2_a_measured_zero_stays_a_measured_zero() -> None:
    snapshot = analyzed(0.0)

    assert snapshot.available_cash_usd == 0.0
    assert snapshot.allocation.cash == 0.0
    assert snapshot.liquidity_pct == 0.0

    # Distinguishable from unavailable in both directions.
    absent = analyzed(None)

    assert absent.available_cash_usd is None
    assert snapshot.available_cash_usd is not None
    assert absent.allocation.cash is None
    assert snapshot.allocation.cash is not None

    # A measured zero is not an unreadable figure, and says so.
    assert not any("could not be read" in flag for flag in snapshot.risk_flags)


# ── control 3: positive measured cash is untouched ──────────────────


def test_3_positive_cash_behaves_exactly_as_before() -> None:
    snapshot = analyzed(25_000.0)

    assert snapshot.available_cash_usd == 25_000.0
    assert snapshot.allocation.cash == 25.0
    assert snapshot.liquidity_pct == 25.0
    assert snapshot.risk_flags == (
        "Invested assets are not yet classified by asset type",
    )


def test_3b_the_concentration_flag_still_fires_on_a_measured_high_reading() -> None:
    snapshot = analyzed(85_000.0)

    assert snapshot.allocation.cash == 85.0
    assert "Cash concentration" in snapshot.risk_flags


# ── control 4: a delta needs both readings ──────────────────────────


@pytest.mark.parametrize(
    ("current", "previous"),
    [(None, 20.0), (60.0, None), (None, None)],
    ids=["current-absent", "previous-absent", "both-absent"],
)
def test_4_either_cash_reading_absent_means_no_cash_delta(
    current: float | None, previous: float | None
) -> None:
    from app.services.signal_service import SignalService
    from tests.test_brain_context import make_portfolio

    base = make_portfolio()
    now = replace(base, allocation=replace(base.allocation, cash=current))
    before = replace(base, allocation=replace(base.allocation, cash=previous))

    signals = SignalService().analyze(now, before)

    assert not any(
        signal.type in ("cash_increase", "cash_deployed") for signal in signals
    ), "a movement claim needs both ends of the comparison"


def test_4b_two_measured_readings_still_produce_the_delta() -> None:
    from app.services.signal_service import SignalService
    from tests.test_brain_context import make_portfolio

    base = make_portfolio()
    now = replace(base, allocation=replace(base.allocation, cash=60.0))
    before = replace(base, allocation=replace(base.allocation, cash=20.0))

    signals = SignalService().analyze(now, before)

    assert any(signal.type == "cash_increase" for signal in signals)


# ── control 5: every consumer has an explicit None branch ───────────


def test_5_no_cash_consumer_formats_compares_or_computes_without_a_none_branch() -> (
    None
):
    """Behavioural, not a source scan: run each consumer with cash absent.

    A consumer missing its None branch raises `TypeError` on the format
    or the comparison. Asserting on behaviour rather than on source text
    is the repository's recorded lesson about literals.
    """

    from app.application.brain.brain_snapshot_service import BrainSnapshotService
    from app.application.brain.reasoning.behavior_analyst import BehaviorAnalyst
    from app.application.brain.reasoning.capacity_analyst import CapacityAnalyst
    from app.application.brain.reasoning.portfolio_analyst import PortfolioAnalyst
    from app.application.brain.reasoning.risk_analyst import RiskAnalyst
    from app.application.executive.portfolio_fit import PortfolioFit
    from app.brain import BrainBuilder
    from app.services.market_risk_service import MarketRiskService
    from app.services.morning_brief_service import MorningBriefService
    from app.services.policy_analyzer import PolicyAnalyzer
    from app.services.signal_service import SignalService
    from tests.test_brain_context import make_market, make_policy

    snapshot = analyzed(None)
    policy = make_policy()

    brain = BrainBuilder(
        portfolio=snapshot,
        market=make_market(),
        investment_policy=policy,
    ).build()

    # Each of these reads cash; none may raise, and none may claim a zero.
    PolicyAnalyzer().analyze(snapshot, policy)
    SignalService().analyze(snapshot, snapshot)
    MorningBriefService().build(snapshot)
    MarketRiskService().measure(make_market(), snapshot)
    PortfolioFit()._funding_room(snapshot, policy)

    capacity = CapacityAnalyst().assess(brain)

    assert capacity.cash_actual_pct is None
    assert capacity.funding_room_pct is None
    assert any("no cash figure" in note for note in capacity.unmeasured)

    behaviour = BehaviorAnalyst().assess(brain)

    assert any("could not be read" in bias for bias in behaviour.observed_biases)

    portfolio_view = PortfolioAnalyst().assess(brain)

    assert portfolio_view.liquidity_score is None
    assert portfolio_view.health_score is None, (
        "a score a quarter of which is unmeasured is unmeasured"
    )
    assert portfolio_view.health_level is None

    risk = RiskAnalyst().assess(brain)

    assert risk.liquidity_risk_score is None
    assert "Low cash buffer" not in risk.risk_factors

    sentence = BrainSnapshotService._summary(snapshot)

    assert "could not be read" in sentence
    assert "$0" not in sentence


def test_5b_investor_surfaces_render_unavailable_never_zero() -> None:
    from app.committee.risk import RiskCommittee
    from app.renderers.brief_language import health_label
    from app.services.morning_brief_service import MorningBriefService

    snapshot = analyzed(None)

    brief = MorningBriefService().build(snapshot)

    assert brief.cash_allocation is None
    assert "could not be read" in brief.summary
    assert "0%" not in brief.summary

    # A score nobody could compute gets a word that is not a band.
    assert health_label(None) == "Not measured"
    assert health_label(0.2) == "At risk", "the bands themselves are unchanged"

    assert RiskCommittee is not None


def test_5c_the_cash_committee_abstains_in_words_rather_than_voting_a_view() -> None:
    from app.committee.cash import CashCommittee
    from app.domain.committee_context import CommitteeContext
    from tests.test_brain_context import make_market, make_policy

    snapshot = analyzed(None)

    context = CommitteeContext(
        portfolio=snapshot,
        policy=make_policy(),
        intelligence=_intelligence(make_market()),
    )

    opinion = CashCommittee().evaluate(context)

    assert opinion.confidence == 0, "no view, and the confidence says so"
    assert "could not be read" in opinion.rationale
    assert "target" in opinion.rationale


def _intelligence(market):
    from app.domain.market_intelligence import MarketIntelligence

    return MarketIntelligence(
        market=market,
        sentiment=None,
        outlook="constructive",
        confidence=80,
        summary="Markets are constructive.",
    )


# ── control 6: a fresh receipt passes, and is named as a receipt ────


def test_6_a_fresh_response_passes_and_is_worded_as_receipt() -> None:
    from app.domain.capital_envelope import portfolio_observation_for
    from tests.test_capital_action_envelope import policy

    observed = portfolio_observation_for(
        last_sync=MOMENT - timedelta(minutes=3), policy=policy(), now=MOMENT
    )

    assert observed.fresh
    assert observed.as_of.startswith("eToro account response received at")
    assert "receipt time" in observed.as_of
    assert "eToro states no account observation time" in observed.as_of

    # The ruled prohibition, checked as words rather than intentions.
    lowered = observed.as_of.casefold()

    for forbidden in (
        "observed at",
        "observation time of",
        "as of",
        "asof",
        "snapshot time",
        "source timestamp",
        "underlying snapshot",
    ):
        assert forbidden not in lowered, forbidden


# ── control 7: every unusable clock refuses in its own words ────────


def test_7_stale_absent_naive_and_future_receipts_refuse_distinctly() -> None:
    from app.domain.capital_envelope import portfolio_observation_for
    from tests.test_capital_action_envelope import policy

    cases = {
        "stale": MOMENT - timedelta(minutes=40),
        "naive": datetime(2026, 8, 20, 11, 58),
        "future": MOMENT + timedelta(minutes=5),
        "absent": None,
    }

    reasons = {}

    for name, value in cases.items():
        observed = portfolio_observation_for(
            last_sync=value, policy=policy(), now=MOMENT
        )

        assert not observed.fresh, name
        assert observed.refused_because, name

        reasons[name] = observed.refused_because

    assert len(set(reasons.values())) == 4, "four causes, four sentences"
    assert "longer ago than" in reasons["stale"]
    assert "no timezone" in reasons["naive"]
    assert "in the future" in reasons["future"]
    assert "no eToro account response has been recorded" in reasons["absent"]


# ── control 8: measured inputs are byte-identical ───────────────────


def test_8_fully_measured_inputs_are_unchanged_end_to_end() -> None:
    """The repair is visible only where cash was absent."""

    from app.domain.capital_envelope import EnvelopeKind
    from tests.test_capital_action_envelope import capacity, envelope, policy

    live = policy()

    # The ruled policy values are untouched by this slice.
    assert live.starter_max_total_position_pct == 1.0
    assert live.standard_initial_position_pct == 3.0
    assert live.max_add_weight_change_pct == 2.0
    assert live.max_single_position_pct == 20.0
    assert live.cash_floor_pct == 40.0
    assert live.portfolio_max_age_minutes == 15.0

    # And the envelope arithmetic over measured inputs is unchanged.
    broad_open = envelope("open")

    assert broad_open.kind is EnvelopeKind.UPWARD_BOUNDED
    assert broad_open.final_pct == 3.0
    assert broad_open.evidence_ceiling == "standard_initial"

    limited_open = envelope("open", gaps=("no filing read",))

    assert limited_open.final_pct == 1.0
    assert limited_open.starter_capped is True

    assert envelope("add").final_pct == 2.0
    assert envelope("open", cap=capacity(cash=40.5)).final_pct == 0.5


def test_8b_a_measured_snapshot_produces_the_same_allocation_as_before() -> None:
    snapshot = analyzed(30_000.0)

    assert snapshot.allocation == Allocation(
        cash=30.0, stocks=0.0, etfs=0.0, crypto=0.0, unclassified=60.0
    )
    assert snapshot.liquidity_pct == 30.0
    assert snapshot.available_cash_usd == 30_000.0
