"""The entry-v1 rule table, proven on JPM — the reference implementation.

The quorate cases run against the committed JPM observations in
`data/knowledge/`, the same immutable fixture the CLI serves — no
model, no network, fully deterministic. They are reached through
`tests.reference_knowledge`, which declares that evidence explicitly
rather than letting a store default to a path literal.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.investment_decision import DecisionQuestion, DecisionVerdict
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.entry_question import (
    MARKET_NOT_CONSUMED,
    RULE_BELOW_QUORUM,
    RULE_NO_AUTHORITATIVE_PLAYBOOK,
    RULE_NO_CASE,
    RULE_NO_ROOM,
    RULE_NOT_APPLICABLE_HELD,
    RULE_POLICY_REQUIRED,
    RULE_PORTFOLIO_REQUIRED,
    RULE_QUESTION_UNMAPPED,
    EntryCase,
    decide,
)
from app.services.playbook_mapping import select_grounded
from app.services.understanding_engine import understand
from tests.reference_knowledge import reference_observations

DECIDED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


def _policy(stocks_target=60.0, cap=15.0):
    return InvestmentPolicy(
        risk_profile="moderate",
        target=AllocationTarget(
            stocks=stocks_target, etfs=20.0, crypto=10.0, cash=10.0
        ),
        constraints=InvestmentConstraints(
            max_single_position=cap, max_crypto=20.0, rebalance_threshold=5.0
        ),
    )


def _portfolio(stocks=40.0, holdings=()):
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=100.0 - stocks, stocks=stocks, etfs=0.0, crypto=0.0, unclassified=0.0
        ),
        total_value=10_000.0,
        positions=len(holdings),
        largest_position=None,
        largest_position_pct=0.0,
        risk_flags=(),
        holdings=tuple(holdings),
        last_sync=DECIDED_AT,
    )


def _held_jpm():
    return PortfolioPosition(
        symbol="JPM",
        quantity=10.0,
        invested_usd=1_000.0,
        market_value_usd=1_200.0,
        unrealized_pnl_usd=200.0,
        asset_class="stocks",
    )


def _jpm_observations():
    return reference_observations()


def _case(**overrides):
    fields = dict(
        subject="JPM",
        question=DecisionQuestion.ENTRY,
        occasion="asked by the investor (movrvest decide)",
        decided_at=DECIDED_AT,
        decision_id="JPM.entry.0001",
        predecessor=None,
        consensus=None,
        consensus_because="not gathered in this case",
        understanding=None,
        selection=None,
        selection_because=None,
        portfolio=_portfolio(),
        portfolio_because=None,
        policy=_policy(),
        policy_version="abc123def456",
        policy_because=None,
    )
    fields.update(overrides)
    return EntryCase(**fields)


def _quorate_case(**overrides):
    consensus = consensus_of(_jpm_observations())
    understanding = understand(consensus)
    selection = select_grounded(understanding)
    fields = dict(
        consensus=consensus,
        consensus_because=None,
        understanding=understanding,
        selection=selection,
        selection_because=None,
    )
    fields.update(overrides)
    return _case(**fields)


class TestRefusalPaths:
    def test_an_unmapped_question_is_refused_by_name(self):
        decision = decide(_case(question=DecisionQuestion.INCREASE))
        assert decision.is_refusal
        assert decision.decided_by == RULE_QUESTION_UNMAPPED
        assert "increase" in decision.refusal.because

    def test_the_spend_question_refusal_names_its_relationship(self):
        decision = decide(_case(question=DecisionQuestion.RESEARCH_SPEND))
        assert decision.is_refusal
        assert "INVESTIGATE" in decision.refusal.because

    def test_missing_policy_refuses_with_the_reason_passed_through(self):
        decision = decide(
            _case(policy=None, policy_version=None, policy_because="file missing")
        )
        assert decision.is_refusal
        assert decision.decided_by == RULE_POLICY_REQUIRED
        assert "file missing" in decision.refusal.because

    def test_missing_portfolio_refuses(self):
        decision = decide(_case(portfolio=None, portfolio_because="broker unreachable"))
        assert decision.is_refusal
        assert decision.decided_by == RULE_PORTFOLIO_REQUIRED
        assert "broker unreachable" in decision.refusal.because

    def test_a_held_position_refuses_the_entry_question(self):
        decision = decide(_case(portfolio=_portfolio(holdings=(_held_jpm(),))))
        assert decision.is_refusal
        assert decision.decided_by == RULE_NOT_APPLICABLE_HELD
        assert "does not apply to a held position" in decision.refusal.because

    def test_a_refusal_still_records_its_basis(self):
        decision = decide(_case(portfolio=None, portfolio_because="unreachable"))
        assert decision.policy is not None
        assert decision.portfolio.absent_because is not None
        assert decision.market.absent_because == MARKET_NOT_CONSUMED


class TestPolicyRoom:
    def test_no_room_rejects_on_arithmetic_alone(self):
        decision = decide(_case(portfolio=_portfolio(stocks=65.0)))
        assert decision.verdict is DecisionVerdict.REJECT
        assert decision.decided_by == RULE_NO_ROOM
        assert decision.rests_on is None
        assert "no consensus claim consumed" in decision.rests_on_because
        assert "on the current basis" in (decision.clauses.why_for_this_investor.states)

    def test_room_is_the_smaller_of_cap_and_allocation_distance(self):
        decision = decide(_quorate_case(portfolio=_portfolio(stocks=50.0)))
        # distance to target is 10%, below the 15% cap
        assert "maximum room permitted by policy: 10.0%" in (
            decision.clauses.why_for_this_investor.states
        )

    def test_the_cap_binds_when_the_allocation_distance_is_wider(self):
        decision = decide(_quorate_case(portfolio=_portfolio(stocks=40.0)))
        assert "maximum room permitted by policy: 15.0%" in (
            decision.clauses.why_for_this_investor.states
        )


class TestBelowQuorum:
    def test_below_quorum_investigates_and_raises_the_spend_question(self):
        consensus = consensus_of(_jpm_observations()[:1])
        decision = decide(
            _case(
                consensus=consensus,
                consensus_because=None,
                understanding=understand(consensus),
            )
        )
        assert decision.verdict is DecisionVerdict.INVESTIGATE
        assert decision.decided_by == RULE_BELOW_QUORUM
        assert decision.raises is DecisionQuestion.RESEARCH_SPEND
        assert "1 of 5" in decision.rests_on_because

    def test_no_observations_at_all_also_investigates(self):
        decision = decide(_case(consensus_because="nothing has been read"))
        assert decision.verdict is DecisionVerdict.INVESTIGATE
        assert decision.facts is None
        assert "nothing has been read" in decision.facts_because


class TestQuorateWithoutAuthoritativePlaybook:
    def test_a_rules_gap_monitors_with_the_refusal_verbatim(self):
        decision = decide(
            _quorate_case(
                selection=None,
                selection_because="the archetype is not mapped to a playbook",
            )
        )
        assert decision.verdict is DecisionVerdict.MONITOR
        assert decision.decided_by == RULE_NO_AUTHORITATIVE_PLAYBOOK
        assert "not mapped" in decision.clauses.why_it_matters.states


class TestJpmReferenceCase:
    """The first live decision: JPM, complete chain, eligible — MONITOR."""

    def test_jpm_monitors_because_no_assessment_establishes_a_case(self):
        decision = decide(_quorate_case())
        assert decision.verdict is DecisionVerdict.MONITOR
        assert decision.decided_by == RULE_NO_CASE
        assert decision.is_refusal is False

    def test_the_losing_implication_is_preserved(self):
        decision = decide(_quorate_case())
        losers = [i for i in decision.weighed if not i.prevailed]
        assert losers
        assert "eligible" in losers[0].because

    def test_it_rests_on_the_narrowest_consumed_agreement(self):
        decision = decide(_quorate_case())
        assert decision.rests_on is not None
        # Pinned to the committed JPM reference entry's own narrowest
        # agreement, so this moves when the corpus is legitimately
        # re-observed under a new reading protocol (schema 12 read the
        # document again and its five readings agree 4/5 on the
        # naming). The invariant is the sentence's shape and that the
        # narrowest *consumed* agreement is the one named.
        assert decision.rests_on.stated_majority() == "a majority (4/5)"
        assert decision.rests_on.question == "which segments the document names"

    def test_the_absences_are_carried_verbatim(self):
        decision = decide(_quorate_case())
        assert decision.absences

    def test_every_clause_names_its_edges(self):
        decision = decide(_quorate_case())
        for clause in (
            decision.clauses.what_changed,
            decision.clauses.why_it_matters,
            decision.clauses.why_for_this_investor,
        ):
            assert clause.rests_on

    def test_the_facts_name_the_playbook_and_its_rule(self):
        decision = decide(_quorate_case())
        assert any("playbook=" in fact for fact in decision.facts.facts)
        assert any(
            "diversified-activates-diversified-business" in fact
            for fact in decision.facts.facts
        )

    def test_the_market_context_is_absent_with_its_reason(self):
        decision = decide(_quorate_case())
        assert decision.market.absent_because == MARKET_NOT_CONSUMED

    def test_the_portfolio_context_is_labelled_as_observation(self):
        decision = decide(_quorate_case())
        assert "width-1, uncalibrated broker observation" in (decision.portfolio.facts)

    def test_the_same_case_decides_identically(self):
        assert decide(_quorate_case()) == decide(_quorate_case())

    def test_supersession_wording_names_the_predecessor(self):
        decision = decide(
            _quorate_case(decision_id="JPM.entry.0002", predecessor="JPM.entry.0001")
        )
        assert "supersedes JPM.entry.0001" in (decision.clauses.what_changed.states)
