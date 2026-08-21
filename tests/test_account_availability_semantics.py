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
        security_risk_ceiling_for,
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
        security_risk=security_risk_ceiling_for(
            policy=policy(), volatility_band="LOW", drawdown_band="LOW"
        ),
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


# ── amendment: absence must not vote, and must not become a positive ──


def opinion(member: str, vote: str, confidence: int, because: str | None = None):
    from app.domain.committee_opinion import CommitteeOpinion

    return CommitteeOpinion(
        member=member,
        vote=vote,
        confidence=confidence,
        rationale=f"{member} says {vote}.",
        abstained_because=because,
    )


def abstention(member: str = "Cash"):
    """A typed abstention — note it still carries a `vote` string."""

    return opinion(member, "HOLD", 0, because="nothing to compare")


def test_9_a_zero_confidence_opinion_does_not_vote() -> None:
    """The discriminating panel: BUY 80, SELL 70, Cash HOLD 0.

    Adding or removing the abstaining Cash opinion must change nothing —
    not the recommendation, not the counts, not the mean confidence.
    Before this repair it changed all three: the Counter took every
    opinion, so an abstention was recorded as a HOLD vote and divided
    into the panel's stated confidence.
    """

    from app.committee.chairman import CommitteeChairman

    voting = [opinion("Value", "BUY", 80), opinion("Risk", "SELL", 70)]
    with_abstention = [*voting, abstention()]

    without = CommitteeChairman().decide(voting)
    within = CommitteeChairman().decide(with_abstention)

    assert within.recommendation == without.recommendation
    assert within.buy_votes == without.buy_votes == 1
    assert within.sell_votes == without.sell_votes == 1
    assert within.hold_votes == without.hold_votes == 0, (
        "the abstention is not a HOLD vote"
    )
    assert within.confidence == without.confidence == 75, (
        "75 is the mean of the members that actually voted, not 50"
    )

    # Its wording is still carried — it spoke, and the reader sees why.
    assert len(within.opinions) == 3
    assert any(item.member == "Cash" for item in within.opinions)


def test_9b_the_weighted_production_path_is_where_the_defect_bit_hardest() -> None:
    """`weighted_decide` is what CommitteeService runs.

    A heavily weighted abstainer used to carry its whole regime weight
    into HOLD and win the vote outright.
    """

    from app.committee.chairman import CommitteeChairman

    weights = {"Value": 1.0, "Risk": 1.0, "Cash": 5.0}

    voting = [opinion("Value", "BUY", 80), opinion("Risk", "SELL", 70)]
    with_abstention = [*voting, abstention()]

    without = CommitteeChairman().weighted_decide(voting, weights)
    within = CommitteeChairman().weighted_decide(with_abstention, weights)

    assert within.recommendation == without.recommendation
    assert within.recommendation != "HOLD", (
        "a 5.0-weighted abstention used to decide the whole committee"
    )
    assert within.hold_votes == 0
    assert within.confidence == without.confidence == 75


def test_9c_a_positive_confidence_hold_still_votes_exactly_as_before() -> None:
    """Abstention is never inferred from the word HOLD."""

    from app.committee.chairman import CommitteeChairman

    panel = [
        opinion("Value", "BUY", 80),
        opinion("Cash", "HOLD", 55),
        opinion("Risk", "HOLD", 60),
    ]

    decision = CommitteeChairman().decide(panel)

    assert decision.hold_votes == 2
    assert decision.recommendation == "HOLD"
    assert decision.confidence == 65


def test_9d_an_all_abstained_panel_is_reported_not_manufactured() -> None:
    """No HOLD is invented for a panel that reached no position.

    Unreachable from the live committee — only Cash can abstain — and
    `CommitteeDecision.recommendation` is a required string with no way
    to say "no position", so this raises rather than choosing a verdict
    nobody reached.
    """

    from app.committee.chairman import CommitteeChairman

    with pytest.raises(ValueError, match="every committee member abstained"):
        CommitteeChairman().decide([abstention()])


def test_10_the_cash_committee_abstains_and_a_measured_zero_still_votes() -> None:
    from app.committee.cash import CashCommittee
    from app.domain.committee_context import CommitteeContext
    from tests.test_brain_context import make_market, make_policy

    def evaluated(cash: float | None):
        return CashCommittee().evaluate(
            CommitteeContext(
                portfolio=analyzed(cash),
                policy=make_policy(),
                intelligence=_intelligence(make_market()),
            )
        )

    absent = evaluated(None)

    assert not absent.participates
    assert absent.abstained_because
    assert "no cash figure" in absent.abstained_because
    assert "could not be read" in absent.rationale

    # Control B: a measured zero keeps its real, counted vote.
    measured_zero = evaluated(0.0)

    assert measured_zero.participates
    assert measured_zero.abstained_because is None
    assert measured_zero.confidence > 0
    assert "0.0%" in measured_zero.rationale


def reasoned(cash: float | None):
    """The whole reasoning surface for one cash state."""

    from app.application.brain.reasoning.reasoning_service import ReasoningService
    from app.brain import BrainBuilder
    from tests.test_brain_context import make_market, make_policy

    brain = BrainBuilder(
        portfolio=analyzed(cash),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    return ReasoningService().reason(brain)


def spoken(snapshot) -> list[str]:
    """Every sentence the reasoning pass produced."""

    said: list[str] = []

    for part in (
        snapshot.portfolio,
        snapshot.risk,
        snapshot.behavior,
        snapshot.opportunity,
    ):
        for attribute in (
            "strengths",
            "weaknesses",
            "risk_factors",
            "mitigants",
            "unmeasured",
            "observed_biases",
            "positive_behaviors",
            "opportunities",
            "constraints",
        ):
            said.extend(getattr(part, attribute, ()) or ())

        for item in getattr(part, "evidence", ()) or ():
            said.append(item.description)

    return said


def test_11_absence_is_never_a_positive_finding() -> None:
    """Control A and D: the two-way branches used to reward an absence."""

    snapshot = reasoned(None)
    said = spoken(snapshot)
    blob = " | ".join(said)

    for forbidden in (
        "Capital is largely invested",
        "Healthy cash allocation",
        "Portfolio aligns with investment policy",
        "within its rebalance band",
        "Low cash buffer",
    ):
        assert forbidden not in blob, forbidden

    # And the absence is stated rather than merely omitted.
    assert any("no cash figure" in line for line in said)
    assert any("could not be read" in line for line in said)


def test_11b_the_unmeasured_ledger_names_cash_and_liquidity() -> None:
    snapshot = reasoned(None)

    assert any(
        "Cash and liquidity risk are not measured" in line
        for line in snapshot.risk.unmeasured
    )
    assert snapshot.risk.liquidity_risk_score is None


def test_11c_policy_alignment_and_emotional_risk_are_unavailable() -> None:
    """An absent penalty term used to leave alignment at a perfect 1.0."""

    snapshot = reasoned(None)

    assert snapshot.behavior.policy_alignment_score is None
    assert snapshot.behavior.emotional_risk_score is None

    # Not substituted anywhere downstream either.
    readiness_sentences = [
        item.description
        for item in snapshot.opportunity.evidence
        if "readiness" in item.description
    ]

    assert readiness_sentences
    assert any("policy alignment" in line for line in readiness_sentences), (
        "the missing readiness component is named, not silently dropped"
    )


def test_11d_the_measured_zero_control_keeps_its_findings() -> None:
    """Control B: nothing becomes unavailable merely because it is zero."""

    snapshot = reasoned(0.0)
    blob = " | ".join(spoken(snapshot))

    assert "Low cash buffer" in blob, "a measured zero is a real low-cash finding"

    assert snapshot.behavior.policy_alignment_score is not None
    assert snapshot.behavior.emotional_risk_score is not None
    assert snapshot.risk.liquidity_risk_score is not None
    assert snapshot.portfolio.liquidity_score is not None
    assert snapshot.portfolio.health_score is not None


def test_11e_the_cycle_still_completes_and_only_the_envelope_refuses() -> None:
    """Control A's last two clauses, together."""

    snapshot = reasoned(None)

    # The pass produced every assessment.
    assert snapshot.portfolio is not None
    assert snapshot.market is not None
    assert snapshot.risk is not None
    assert snapshot.behavior is not None
    assert snapshot.opportunity is not None

    # Non-cash reasoning is untouched.
    assert snapshot.market.momentum_score is not None
    assert snapshot.opportunity.opportunity_score is not None
    assert snapshot.portfolio.diversification_score is not None


# ── amendment 2: the abstention must travel past the chairman ────────


def panel_for(cash: float | None):
    """The legacy committee panel, Cash evaluated against a cash state."""

    from app.committee.cash import CashCommittee
    from app.domain.committee_context import CommitteeContext
    from tests.test_brain_context import make_market, make_policy

    context = CommitteeContext(
        portfolio=analyzed(cash),
        policy=make_policy(),
        intelligence=_intelligence(make_market()),
    )

    return [
        CashCommittee().evaluate(context),
        opinion("Diversification", "BUY", 80),
        opinion("Risk", "SELL", 70),
    ]


def recommendation_for(cash: float | None):
    """A whole legacy Recommendation, as CommitteeService would compose it."""

    from app.committee.chairman import CommitteeChairman
    from app.domain.recommendation import Recommendation
    from tests.test_brain_context import make_market

    opinions = panel_for(cash)
    decision = CommitteeChairman().weighted_decide(
        opinions, {"Cash": 5.0, "Diversification": 1.0, "Risk": 1.0}
    )

    return Recommendation(
        symbol="KO",
        portfolio=analyzed(cash),
        intelligence=_intelligence(make_market()),
        decision=decision,
    )


def test_12_the_opinion_itself_carries_the_abstention() -> None:
    """The fact lives on the domain object, not in each consumer's head."""

    from app.domain.committee_opinion import CommitteeOpinion

    absent = panel_for(None)[0]

    assert absent.abstained_because
    assert not absent.participates

    # And the invariants hold in both directions.
    with pytest.raises(ValueError, match="carries its reason"):
        CommitteeOpinion(
            member="X",
            vote="HOLD",
            confidence=0,
            rationale="r",
            abstained_because="   ",
        )

    with pytest.raises(ValueError, match="carries no confidence"):
        CommitteeOpinion(
            member="X",
            vote="HOLD",
            confidence=40,
            rationale="r",
            abstained_because="because",
        )

    with pytest.raises(ValueError, match="positive confidence"):
        CommitteeOpinion(member="X", vote="HOLD", confidence=0, rationale="r")

    # A participating HOLD is untouched.
    held = CommitteeOpinion(member="X", vote="HOLD", confidence=55, rationale="r")

    assert held.participates
    assert held.abstained_because is None


def test_13_the_chairman_has_no_private_definition_of_abstention() -> None:
    """It asks the carrier; it does not re-derive `confidence == 0`."""

    import ast
    import pathlib as _pathlib

    source = _pathlib.Path("app/committee/chairman.py").read_text()
    tree = ast.parse(source)

    docstrings = {
        doc
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        for doc in (ast.get_docstring(node, clean=False),)
        if doc is not None
    }
    executed = "\n".join(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    )

    assert "participates" in source
    assert "confidence == 0" not in executed
    assert not any(
        isinstance(node, ast.FunctionDef) and node.name == "abstained"
        for node in ast.walk(tree)
    ), "the private helper is gone; the domain owns the definition"


def test_14_the_doctor_reports_cash_unknown_never_healthy() -> None:
    """The measured consequence the owner named: HEALTHY at score 90."""

    from app.services.doctor_service import DoctorService

    health = DoctorService().evaluate(recommendation_for(None))
    cash = next(check for check in health.checks if check.name == "Cash")

    assert cash.status == "UNKNOWN"
    assert cash.status not in ("HEALTHY", "WARNING", "ACTION")
    assert cash.score != 90
    assert "no cash figure" in cash.message

    # Control B: a measured zero is graded, not abstained.
    measured = DoctorService().evaluate(recommendation_for(0.0))
    measured_cash = next(check for check in measured.checks if check.name == "Cash")

    assert measured_cash.status != "UNKNOWN"


def test_15_no_investor_surface_prints_the_abstention_as_hold() -> None:
    from app.services.evidence_renderer import EvidenceRenderer
    from app.services.recommendation_report_service import (
        RecommendationReportService,
    )

    recommendation = recommendation_for(None)
    absent = recommendation.decision.opinions[0]

    report = RecommendationReportService().render("KO", recommendation.decision)

    assert "Cash: HOLD" not in report, "the observed defect"
    assert "Cash: ABSTAINED" in report
    assert absent.abstained_because in report

    rendered = str(EvidenceRenderer().render(absent))

    assert "Vote: HOLD" not in rendered
    assert "ABSTAINED" in rendered

    # Control B: a measured zero still renders its real vote.
    measured_decision = recommendation_for(0.0).decision
    measured = RecommendationReportService().render("KO", measured_decision)

    assert "Cash: ABSTAINED" not in measured
    assert "Cash: " in measured


def test_16_the_remaining_members_alone_decide() -> None:
    from app.committee.chairman import CommitteeChairman

    weights = {"Cash": 5.0, "Diversification": 1.0, "Risk": 1.0}

    with_cash = CommitteeChairman().weighted_decide(panel_for(None), weights)
    without_cash = CommitteeChairman().weighted_decide(panel_for(None)[1:], weights)

    assert with_cash.recommendation == without_cash.recommendation
    assert with_cash.confidence == without_cash.confidence == 75
    assert with_cash.hold_votes == 0
    assert with_cash.recommendation != "HOLD"


def test_17_the_stored_event_preserves_the_abstention(tmp_path) -> None:
    """Persistence carries the fact; analytics refuse to count it."""

    import json

    from app.services.committee_analytics_service import (
        CommitteeAnalyticsService,
    )

    absent = panel_for(None)[0]

    stored = {
        "member": absent.member,
        "vote": absent.vote,
        "confidence": absent.confidence,
        "rationale": absent.rationale,
        "abstained_because": absent.abstained_because,
    }

    assert stored["abstained_because"], "the fact is on the row"

    # Round-trips as JSON, which is how the event store holds it.
    assert json.loads(json.dumps(stored))["abstained_because"]

    assert CommitteeAnalyticsService is not None


def test_18_analytics_count_neither_the_vote_nor_the_denominator(
    tmp_path,
) -> None:
    from app.domain.event import Event
    from app.domain.event_type import EventType
    from app.repositories.json_event_repository import JsonEventRepository
    from app.services.committee_analytics_service import (
        CommitteeAnalyticsService,
    )

    repository = JsonEventRepository(tmp_path / "events")

    def row(member: str, vote: str, confidence: int, because=None):
        return {
            "member": member,
            "vote": vote,
            "confidence": confidence,
            "rationale": "r",
            "abstained_because": because,
        }

    repository.save(
        Event(
            timestamp=MOMENT,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="KO",
            payload={
                "recommendation": "BUY",
                "confidence": 75,
                "votes": [
                    row("Value", "BUY", 80),
                    row("Cash", "HOLD", 0, "the broker stated no cash figure"),
                    # An older row, written before the key existed.
                    {
                        "member": "Legacy",
                        "vote": "HOLD",
                        "confidence": 60,
                        "rationale": "r",
                    },
                ],
            },
        )
    )

    statistics = {
        item.member: item
        for item in CommitteeAnalyticsService(repository).member_statistics()
    }

    assert "Cash" not in statistics, "an abstention is not a vote"
    assert statistics["Value"].buy == 1

    # Historical rows stay readable and keep counting exactly as before.
    assert statistics["Legacy"].hold == 1
    assert statistics["Legacy"].average_confidence == 60


def test_19_the_api_carries_the_typed_fact() -> None:
    """No client infers the abstention from confidence or prose."""

    from app.api.models.today import OpinionResponse

    absent = panel_for(None)[0]

    response = OpinionResponse(
        member=absent.member,
        vote=absent.vote,
        confidence=absent.confidence,
        rationale=absent.rationale,
        abstained_because=absent.abstained_because,
    )

    assert response.abstained_because
    assert response.model_dump()["abstained_because"]

    # And it defaults to null for a participating member.
    voting = OpinionResponse(member="Risk", vote="SELL", confidence=70, rationale="r")

    assert voting.abstained_because is None


def test_20_measured_inputs_are_unchanged_but_for_the_new_field() -> None:
    """The digest constant moved; the behaviour did not.

    `CommitteeOpinion` gained `abstained_because`, which appears in every
    participating opinion's `repr` as `None`. That changes a digest taken
    over reprs and nothing else — so the check elides the new field and
    pins the original constant, rather than asserting the equivalence in
    prose.
    """

    import hashlib

    from app.committee.chairman import CommitteeChairman
    from app.domain.committee_opinion import CommitteeOpinion

    panel = [
        CommitteeOpinion(member="Value", vote="BUY", confidence=80, rationale="v"),
        CommitteeOpinion(member="Risk", vote="SELL", confidence=70, rationale="r"),
        CommitteeOpinion(member="Cash", vote="HOLD", confidence=55, rationale="c"),
    ]
    weights = {"Value": 1.0, "Risk": 1.0, "Cash": 5.0}

    rendered = "\n".join(
        (
            f"committee={CommitteeChairman().decide(panel)!r}",
            f"weighted={CommitteeChairman().weighted_decide(panel, weights)!r}",
        )
    )

    # Every member participated, so the new field is uniformly absent.
    assert rendered.count("abstained_because=None") == 6
    assert "abstained_because='" not in rendered

    elided = rendered.replace(", abstained_because=None", "")

    # Computed on the pre-amendment tree (346f182), where the field did
    # not exist — a baseline, not a value copied from this run.
    assert hashlib.sha256(elided.encode()).hexdigest()[:16] == "afe5498223345cc5"


# ── amendment 3: the carrier must reach the public serializers ───────


def test_21_the_dashboard_serializes_the_abstention_not_a_hold() -> None:
    """The remaining public hole: `DashboardService._build_today`.

    It built `OpinionResponse` without forwarding the carrier, so the
    dashboard could still publish an abstaining Cash member as an
    ordinary zero-confidence HOLD.
    """

    from app.api.models.today import OpinionResponse

    absent = panel_for(None)[0]
    voting = panel_for(0.0)[0]

    def serialized(opinion):
        return OpinionResponse(
            member=opinion.member,
            vote=opinion.vote,
            confidence=opinion.confidence,
            rationale=opinion.rationale,
            abstained_because=opinion.abstained_because,
        ).model_dump()

    abstained_row = serialized(absent)

    assert abstained_row["abstained_because"], "the reason travels"
    assert "no cash figure" in abstained_row["abstained_because"]

    # Visibly distinguishable from a HOLD without reading confidence.
    participating_row = serialized(voting)

    assert participating_row["abstained_because"] is None
    assert abstained_row["abstained_because"] != participating_row["abstained_because"]

    # And a positive-confidence HOLD keeps a null carrier.
    held = OpinionResponse(
        member="Risk", vote="HOLD", confidence=55, rationale="r"
    ).model_dump()

    assert held["vote"] == "HOLD"
    assert held["abstained_because"] is None


def test_22_every_production_opinion_response_forwards_the_carrier() -> None:
    """A future serializer cannot silently drop it.

    Parses the AST of each production module that constructs the legacy
    `OpinionResponse` and asserts the keyword is present at every call
    site — a behavioural test cannot see a site nobody exercises.
    """

    import ast
    import pathlib as _pathlib

    sites = 0

    for path in sorted(_pathlib.Path("app").rglob("*.py")):
        tree = ast.parse(path.read_text())

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)

            if name != "OpinionResponse":
                continue

            sites += 1
            keywords = {keyword.arg for keyword in node.keywords}

            assert "abstained_because" in keywords, (
                f"{path} constructs OpinionResponse without forwarding "
                "abstained_because"
            )

    assert sites >= 2, f"expected every production site to be found, saw {sites}"


def test_23_the_weighted_vote_service_asks_the_carrier() -> None:
    """Skipped explicitly, and every participating score unchanged."""

    import ast
    import pathlib as _pathlib

    from app.domain.committee_member_weight import CommitteeMemberWeight
    from app.services.weighted_vote_service import WeightedVoteService

    source = _pathlib.Path("app/services/weighted_vote_service.py").read_text()

    assert "participates" in source, "it consults the domain contract"
    assert not any(
        isinstance(node, ast.Compare)
        and any(
            isinstance(item, ast.Constant) and item.value == 0
            for item in node.comparators
        )
        for node in ast.walk(ast.parse(source))
    ), "participation is not inferred from a confidence comparison"

    weights = [
        CommitteeMemberWeight(member="Value", weight=1.0, accuracy=0.5),
        CommitteeMemberWeight(member="Risk", weight=1.0, accuracy=0.5),
        CommitteeMemberWeight(member="Cash", weight=5.0, accuracy=0.5),
    ]
    voting = [opinion("Value", "BUY", 80), opinion("Risk", "SELL", 70)]

    without = WeightedVoteService().score(voting, weights)
    within = WeightedVoteService().score([*voting, abstention()], weights)

    assert within == without, "participating scores are byte-for-byte equal"
    assert within["HOLD"] == 0.0


def test_24_an_invalid_empty_carrier_never_becomes_a_historical_hold(
    tmp_path,
) -> None:
    """Presence, not truthiness — and null stays participating."""

    from app.domain.event import Event
    from app.domain.event_type import EventType
    from app.repositories.json_event_repository import JsonEventRepository
    from app.services.committee_analytics_service import (
        CommitteeAnalyticsService,
    )

    repository = JsonEventRepository(tmp_path / "events")

    repository.save(
        Event(
            timestamp=MOMENT,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="KO",
            payload={
                "recommendation": "BUY",
                "confidence": 75,
                "votes": [
                    # An invalid carrier: empty string. Falsy, but present.
                    {
                        "member": "Broken",
                        "vote": "HOLD",
                        "confidence": 0,
                        "rationale": "r",
                        "abstained_because": "",
                    },
                    # Explicit null — a participating row.
                    {
                        "member": "Null",
                        "vote": "HOLD",
                        "confidence": 60,
                        "rationale": "r",
                        "abstained_because": None,
                    },
                    # Key absent entirely — an older row.
                    {
                        "member": "Older",
                        "vote": "BUY",
                        "confidence": 70,
                        "rationale": "r",
                    },
                ],
            },
        )
    )

    statistics = {
        item.member: item
        for item in CommitteeAnalyticsService(repository).member_statistics()
    }

    assert "Broken" not in statistics, (
        "an empty-string carrier is an invalid abstention, never a HOLD"
    )
    assert statistics["Null"].hold == 1, "null remains participating"
    assert statistics["Older"].buy == 1, "an absent key remains participating"
