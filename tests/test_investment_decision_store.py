"""The decision store: append-only, chain-checked, loud on corruption."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from app.domain.investment_decision import DecisionQuestion
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.repositories.investment_decision_store import (
    DECISION_SCHEMA_VERSION,
    JsonInvestmentDecisionStore,
)
from app.services.entry_question import EntryCase, decide
from app.services.playbook_mapping import select_grounded
from app.services.understanding_engine import understand
from tests.reference_knowledge import reference_observations

DECIDED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


def _policy():
    return InvestmentPolicy(
        risk_profile="moderate",
        target=AllocationTarget(stocks=60.0, etfs=20.0, crypto=10.0, cash=10.0),
        constraints=InvestmentConstraints(
            max_single_position=15.0, max_crypto=20.0, rebalance_threshold=5.0
        ),
    )


def _portfolio(stocks=40.0):
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=100.0 - stocks, stocks=stocks, etfs=0.0, crypto=0.0, unclassified=0.0
        ),
        total_value=10_000.0,
        positions=0,
        largest_position=None,
        largest_position_pct=0.0,
        risk_flags=(),
        last_sync=DECIDED_AT,
    )


def _jpm_decision(decision_id="JPM.entry.0001", predecessor=None, stocks=40.0):
    consensus = consensus_of(reference_observations())
    understanding = understand(consensus)
    case = EntryCase(
        subject="JPM",
        question=DecisionQuestion.ENTRY,
        occasion="asked by the investor (movrvest decide)",
        decided_at=DECIDED_AT,
        decision_id=decision_id,
        predecessor=predecessor,
        consensus=consensus,
        consensus_because=None,
        understanding=understanding,
        selection=select_grounded(understanding),
        selection_because=None,
        portfolio=_portfolio(stocks),
        portfolio_because=None,
        policy=_policy(),
        policy_version="abc123def456",
        policy_because=None,
    )
    return decide(case)


def _refusal_decision(decision_id="JPM.increase.0001", predecessor=None):
    case = EntryCase(
        subject="JPM",
        question=DecisionQuestion.INCREASE,
        occasion="asked by the investor (movrvest decide)",
        decided_at=DECIDED_AT,
        decision_id=decision_id,
        predecessor=predecessor,
        consensus=None,
        consensus_because="not gathered",
        understanding=None,
        selection=None,
        selection_because=None,
        portfolio=_portfolio(),
        portfolio_because=None,
        policy=_policy(),
        policy_version="abc123def456",
        policy_because=None,
    )
    return decide(case)


class TestRoundTrip:
    def test_a_verdict_survives_the_store_unchanged(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        decision = _jpm_decision()
        store.append(decision)
        assert store.read("JPM", DecisionQuestion.ENTRY) == (decision,)

    def test_a_refusal_survives_the_store_unchanged(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        decision = _refusal_decision()
        store.append(decision)
        assert store.read("JPM", DecisionQuestion.INCREASE) == (decision,)

    def test_the_current_stance_is_the_latest_answer(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        first = _jpm_decision()
        store.append(first)
        second = _jpm_decision(
            decision_id="JPM.entry.0002", predecessor="JPM.entry.0001"
        )
        store.append(second)
        assert store.current("JPM", DecisionQuestion.ENTRY) == second
        assert store.read("JPM", DecisionQuestion.ENTRY) == (first, second)

    def test_an_empty_stream_reads_as_absent(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        assert store.read("JPM", DecisionQuestion.ENTRY) == ()
        assert store.current("JPM", DecisionQuestion.ENTRY) is None


class TestStreamsAreScopedPerSubjectAndQuestion:
    def test_questions_do_not_share_a_stream(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        store.append(_refusal_decision())
        assert len(store.read("JPM", DecisionQuestion.ENTRY)) == 1
        assert len(store.read("JPM", DecisionQuestion.INCREASE)) == 1

    def test_identity_runs_per_stream(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        assert store.next_id("JPM", DecisionQuestion.ENTRY) == "JPM.entry.0001"
        store.append(_jpm_decision())
        assert store.next_id("JPM", DecisionQuestion.ENTRY) == "JPM.entry.0002"
        assert store.next_id("JPM", DecisionQuestion.INCREASE) == ("JPM.increase.0001")


class TestAppendOnlyIntegrity:
    def test_a_wrong_predecessor_is_refused(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        broken = _jpm_decision(decision_id="JPM.entry.0002", predecessor=None)
        with pytest.raises(ValueError, match="predecessor"):
            store.append(broken)

    def test_a_wrong_identity_is_refused(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        broken = _jpm_decision(
            decision_id="JPM.entry.0009", predecessor="JPM.entry.0001"
        )
        with pytest.raises(ValueError, match="identity"):
            store.append(broken)

    def test_a_superseding_append_preserves_history(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        store.append(
            _jpm_decision(decision_id="JPM.entry.0002", predecessor="JPM.entry.0001")
        )
        stream = store.read("JPM", DecisionQuestion.ENTRY)
        assert [d.decision_id for d in stream] == [
            "JPM.entry.0001",
            "JPM.entry.0002",
        ]


class TestCorruptionIsLoudNeverAbsent:
    def test_an_unreadable_history_raises(self, tmp_path):
        path = tmp_path / "JPM.entry.json"
        path.write_text("not json", encoding="utf-8")
        store = JsonInvestmentDecisionStore(tmp_path)
        with pytest.raises(ValueError, match="unreadable"):
            store.read("JPM", DecisionQuestion.ENTRY)

    def test_a_schema_mismatch_raises_and_never_upgrades(self, tmp_path):
        path = tmp_path / "JPM.entry.json"
        path.write_text('{"schema_version": 0, "decisions": []}', encoding="utf-8")
        store = JsonInvestmentDecisionStore(tmp_path)
        with pytest.raises(ValueError, match="schema"):
            store.read("JPM", DecisionQuestion.ENTRY)

    def test_a_corrupt_stream_cannot_be_silently_replaced(self, tmp_path):
        path = tmp_path / "JPM.entry.json"
        path.write_text("not json", encoding="utf-8")
        store = JsonInvestmentDecisionStore(tmp_path)
        with pytest.raises(ValueError, match="unreadable"):
            store.append(_jpm_decision())
        assert path.read_text(encoding="utf-8") == "not json"


class TestSchemaVersion:
    def test_the_written_payload_carries_the_schema_version(self, tmp_path):
        import json

        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        payload = json.loads((tmp_path / "JPM.entry.json").read_text(encoding="utf-8"))
        assert payload["schema_version"] == DECISION_SCHEMA_VERSION

    def test_supersession_metadata_round_trips(self, tmp_path):
        store = JsonInvestmentDecisionStore(tmp_path)
        store.append(_jpm_decision())
        second = _jpm_decision(
            decision_id="JPM.entry.0002", predecessor="JPM.entry.0001"
        )
        store.append(second)
        restored = store.read("JPM", DecisionQuestion.ENTRY)[-1]
        assert restored.predecessor == "JPM.entry.0001"
        assert restored == replace(second)
