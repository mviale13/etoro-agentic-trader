"""The canonical decision's shape enforces the accepted properties."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.agreement import Agreement, Answer
from app.domain.investment_decision import (
    Clause,
    Clauses,
    ContextObservation,
    DecisionQuestion,
    DecisionVerdict,
    DeclaredPolicy,
    Implication,
    InvestmentDecision,
    Refusal,
)

DECIDED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


def _clause(text="a statement"):
    return Clause(states=text, rests_on=("policy:risk_profile=moderate",))


def _clauses():
    return Clauses(
        what_changed=_clause("first consideration; nothing preceded"),
        why_it_matters=_clause("the chain is complete"),
        why_for_this_investor=_clause("room exists"),
    )


def _weighed(prevailed=True):
    return (
        Implication(
            course="keep the question open",
            because="no assessment exists",
            rests_on=("facts:assessments=absent",),
            prevailed=prevailed,
        ),
    )


def _portfolio():
    return ContextObservation(
        kind="portfolio",
        observed_at=DECIDED_AT,
        facts=("JPM not held",),
        absent_because=None,
    )


def _market():
    return ContextObservation(
        kind="market",
        observed_at=None,
        facts=(),
        absent_because="not consumed by entry-v1",
    )


def _decision(**overrides):
    fields = dict(
        decision_id="JPM.entry.0001",
        subject="JPM",
        question=DecisionQuestion.ENTRY,
        decided_at=DECIDED_AT,
        occasion="asked by the investor",
        occasioned_by=(),
        facts=None,
        facts_because="no stored observations",
        portfolio=_portfolio(),
        market=_market(),
        policy=DeclaredPolicy(version="abc123", clauses=("risk_profile: moderate",)),
        policy_because=None,
        verdict=DecisionVerdict.MONITOR,
        refusal=None,
        action=None,
        raises=None,
        clauses=_clauses(),
        weighed=_weighed(),
        decided_by="entry-no-assessment-establishes-a-case",
        rests_on=None,
        rests_on_because="no consensus claim consumed",
        absences=(),
        predecessor=None,
    )
    fields.update(overrides)
    return InvestmentDecision(**fields)


def _refusal_fields():
    return dict(
        verdict=None,
        refusal=Refusal(because="a mandatory context is missing"),
        clauses=None,
        weighed=(),
        rests_on=None,
        rests_on_because=None,
    )


class TestOutcomeExclusivity:
    def test_a_verdict_constructs(self):
        assert _decision().verdict is DecisionVerdict.MONITOR

    def test_a_refusal_constructs(self):
        decision = _decision(**_refusal_fields())
        assert decision.is_refusal
        assert decision.refusal.because == "a mandatory context is missing"

    def test_verdict_and_refusal_together_are_invalid(self):
        with pytest.raises(ValueError, match="exactly one"):
            _decision(refusal=Refusal(because="also refused"))

    def test_neither_verdict_nor_refusal_is_invalid(self):
        with pytest.raises(ValueError, match="exactly one"):
            _decision(verdict=None, clauses=None, weighed=())

    def test_a_refusal_wears_no_clauses(self):
        with pytest.raises(ValueError, match="clauses"):
            _decision(**{**_refusal_fields(), "clauses": _clauses()})

    def test_a_verdict_requires_clauses(self):
        with pytest.raises(ValueError, match="clauses"):
            _decision(clauses=None)

    def test_an_empty_refusal_reason_is_invalid(self):
        with pytest.raises(ValueError, match="reason"):
            Refusal(because="   ")


class TestActionAttachesToRecommendOnly:
    def test_an_action_on_monitor_is_invalid(self):
        with pytest.raises(ValueError, match="RECOMMEND"):
            _decision(action="open up to 15.0%")

    def test_recommend_without_an_action_is_invalid(self):
        with pytest.raises(ValueError, match="affirmative"):
            _decision(verdict=DecisionVerdict.RECOMMEND)

    def test_recommend_with_an_action_constructs(self):
        decision = _decision(
            verdict=DecisionVerdict.RECOMMEND,
            action="open up to 15.0% of the portfolio",
        )
        assert decision.action is not None


class TestInvestigateRaisesTheSpendQuestion:
    def test_investigate_without_raises_is_invalid(self):
        with pytest.raises(ValueError, match="raises"):
            _decision(verdict=DecisionVerdict.INVESTIGATE)

    def test_raises_without_investigate_is_invalid(self):
        with pytest.raises(ValueError, match="INVESTIGATE"):
            _decision(raises=DecisionQuestion.RESEARCH_SPEND)

    def test_investigate_raises_only_the_research_spend_question(self):
        with pytest.raises(ValueError, match="research-spend"):
            _decision(
                verdict=DecisionVerdict.INVESTIGATE,
                raises=DecisionQuestion.INCREASE,
            )

    def test_investigate_on_the_spend_question_is_circular(self):
        with pytest.raises(ValueError, match="circular"):
            _decision(
                question=DecisionQuestion.RESEARCH_SPEND,
                verdict=DecisionVerdict.INVESTIGATE,
                raises=DecisionQuestion.RESEARCH_SPEND,
            )

    def test_investigate_constructs_when_well_formed(self):
        decision = _decision(
            verdict=DecisionVerdict.INVESTIGATE,
            raises=DecisionQuestion.RESEARCH_SPEND,
        )
        assert decision.raises is DecisionQuestion.RESEARCH_SPEND


class TestClausesCarryEdges:
    def test_a_clause_without_edges_cannot_be_stated(self):
        with pytest.raises(ValueError, match="edges"):
            Clause(states="unsupported", rests_on=())

    def test_a_clause_without_a_statement_is_invalid(self):
        with pytest.raises(ValueError, match="state"):
            Clause(states="  ", rests_on=("policy:x",))


class TestWeighing:
    def test_a_verdict_without_weighed_implications_is_invalid(self):
        with pytest.raises(ValueError, match="implications"):
            _decision(weighed=())

    def test_a_verdict_where_nothing_prevailed_is_invalid(self):
        with pytest.raises(ValueError, match="prevailed"):
            _decision(weighed=_weighed(prevailed=False))

    def test_losing_implications_are_preserved(self):
        decision = _decision(weighed=_weighed() + _weighed(prevailed=False))
        assert any(not i.prevailed for i in decision.weighed)


class TestRestsOn:
    def test_a_verdict_carries_agreement_or_reason_never_both(self):
        agreement = Agreement(
            question="which segments the document names",
            answers=(Answer(stated="a, b, c", given=3), Answer(stated="a, b", given=2)),
        )
        with pytest.raises(ValueError, match="narrowest"):
            _decision(rests_on=agreement, rests_on_because="also worded")

    def test_a_verdict_carries_at_least_one(self):
        with pytest.raises(ValueError, match="narrowest"):
            _decision(rests_on=None, rests_on_because=None)


class TestContextObservation:
    def test_absent_with_facts_is_invalid(self):
        with pytest.raises(ValueError, match="never both"):
            ContextObservation(
                kind="market",
                observed_at=None,
                facts=("something",),
                absent_because="also absent",
            )

    def test_silent_absence_is_invalid(self):
        with pytest.raises(ValueError, match="reason"):
            ContextObservation(
                kind="market", observed_at=None, facts=(), absent_because=None
            )


class TestBasisAbsencesAreWorded:
    def test_facts_absent_without_reason_is_invalid(self):
        with pytest.raises(ValueError, match="reason"):
            _decision(facts_because=None)

    def test_policy_absent_without_reason_is_invalid(self):
        with pytest.raises(ValueError, match="reason"):
            _decision(policy=None, policy_because=None)


class TestNoConfidenceInteger:
    def test_the_object_has_no_confidence_field(self):
        assert "confidence" not in InvestmentDecision.__slots__
