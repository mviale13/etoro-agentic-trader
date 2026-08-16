"""The append-only store of investment decisions.

A decision is an event: it happened at a time, on a recorded basis,
and the investor may have acted on it. The store therefore only ever
appends — a later decision supersedes an earlier one in the same
(subject, question) stream, citing it, and nothing is revised. The
current stance is derived on read as the latest answer per question,
never stored as another source of truth.

One deliberate divergence from the knowledge store's pattern: an
unreadable or schema-mismatched history is a loud error, never treated
as absent. Observations can be re-acquired from the filing; a decision
history cannot be re-acquired from anywhere, so silently starting a
fresh stream over it would destroy the one record of the platform
changing its mind.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.agreement import Agreement, Answer
from app.domain.investment_decision import (
    Clause,
    Clauses,
    ContextObservation,
    DecisionQuestion,
    DecisionVerdict,
    DeclaredPolicy,
    EstablishedFacts,
    Implication,
    InvestmentDecision,
    Refusal,
)
from app.domain.provenance import Provenance
from app.infrastructure.evidence_root import evidence_path

DECISION_SCHEMA_VERSION = 1


class JsonInvestmentDecisionStore:
    """One JSON file per (subject, question) stream, append-only."""

    def __init__(self, directory: Path | str | None = None) -> None:
        # The evidence root, resolved at construction (#118, BQ10).
        self._directory = (
            Path(directory) if directory is not None else evidence_path("decisions")
        )

    def read(
        self, subject: str, question: DecisionQuestion
    ) -> tuple[InvestmentDecision, ...]:
        """The stream, oldest first; empty when none exists.

        Raises ValueError on an unreadable or schema-mismatched file —
        see the module docstring for why this never degrades to absent.
        """

        path = self._path(subject, question)
        if not path.exists():
            return ()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"decision history at {path} is unreadable: {error}"
            ) from error
        version = payload.get("schema_version")
        if version != DECISION_SCHEMA_VERSION:
            raise ValueError(
                f"decision history at {path} carries schema {version!r}; "
                f"this platform writes schema {DECISION_SCHEMA_VERSION} and "
                "never upgrades a history in place"
            )
        return tuple(_decode_decision(entry) for entry in payload["decisions"])

    def current(
        self, subject: str, question: DecisionQuestion
    ) -> InvestmentDecision | None:
        """The latest non-superseded answer — the derived stance."""

        stream = self.read(subject, question)
        return stream[-1] if stream else None

    def next_id(self, subject: str, question: DecisionQuestion) -> str:
        """The identity the next decision in this stream will carry."""

        count = len(self.read(subject, question))
        return f"{subject}.{question.value}.{count + 1:04d}"

    def append(self, decision: InvestmentDecision) -> None:
        """Append one decision, enforcing the stream's integrity.

        The decision must carry the stream's next identity and cite the
        current latest as its predecessor (or none where the stream is
        empty) — supersession is a property of the stream, and the
        store refuses a decision that would break the chain.
        """

        existing = self.read(decision.subject, decision.question)
        expected_predecessor = existing[-1].decision_id if existing else None
        if decision.predecessor != expected_predecessor:
            raise ValueError(
                f"append-only stream: expected predecessor "
                f"{expected_predecessor!r}, got {decision.predecessor!r}"
            )
        expected_id = self.next_id(decision.subject, decision.question)
        if decision.decision_id != expected_id:
            raise ValueError(
                f"append-only stream: expected identity {expected_id!r}, "
                f"got {decision.decision_id!r}"
            )
        payload = {
            "schema_version": DECISION_SCHEMA_VERSION,
            "subject": decision.subject,
            "question": decision.question.value,
            "decisions": [_encode_decision(entry) for entry in (*existing, decision)],
        }
        path = self._path(decision.subject, decision.question)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _path(self, subject: str, question: DecisionQuestion) -> Path:
        return self._directory / f"{_safe(subject)}.{question.value}.json"


def _safe(fragment: str) -> str:
    return "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in fragment.upper()
    )


def _encode_decision(decision: InvestmentDecision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "subject": decision.subject,
        "question": decision.question.value,
        "decided_at": decision.decided_at.isoformat(),
        "occasion": decision.occasion,
        "occasioned_by": list(decision.occasioned_by),
        "facts": _encode_facts(decision.facts),
        "facts_because": decision.facts_because,
        "portfolio": _encode_context(decision.portfolio),
        "market": _encode_context(decision.market),
        "policy": (
            None
            if decision.policy is None
            else {
                "version": decision.policy.version,
                "clauses": list(decision.policy.clauses),
            }
        ),
        "policy_because": decision.policy_because,
        "verdict": None if decision.verdict is None else decision.verdict.value,
        "refusal": (
            None if decision.refusal is None else {"because": decision.refusal.because}
        ),
        "action": decision.action,
        "raises": None if decision.raises is None else decision.raises.value,
        "clauses": _encode_clauses(decision.clauses),
        "weighed": [
            {
                "course": implication.course,
                "because": implication.because,
                "rests_on": list(implication.rests_on),
                "prevailed": implication.prevailed,
            }
            for implication in decision.weighed
        ],
        "decided_by": decision.decided_by,
        "rests_on": _encode_agreement(decision.rests_on),
        "rests_on_because": decision.rests_on_because,
        "absences": list(decision.absences),
        "predecessor": decision.predecessor,
    }


def _encode_facts(facts: EstablishedFacts | None) -> dict[str, Any] | None:
    if facts is None:
        return None
    return {
        "source": facts.source,
        "consensus_state": facts.consensus_state,
        "observation_count": facts.observation_count,
        "quorum": facts.quorum,
        "reading": {
            "source": facts.reading.source,
            "observed_at": facts.reading.observed_at.isoformat(),
            "last_known": facts.reading.last_known,
        },
        "facts": list(facts.facts),
    }


def _encode_context(context: ContextObservation) -> dict[str, Any]:
    return {
        "kind": context.kind,
        "observed_at": (
            None if context.observed_at is None else context.observed_at.isoformat()
        ),
        "facts": list(context.facts),
        "absent_because": context.absent_because,
    }


def _encode_clauses(clauses: Clauses | None) -> dict[str, Any] | None:
    if clauses is None:
        return None
    return {
        "what_changed": _encode_clause(clauses.what_changed),
        "why_it_matters": _encode_clause(clauses.why_it_matters),
        "why_for_this_investor": _encode_clause(clauses.why_for_this_investor),
    }


def _encode_clause(clause: Clause) -> dict[str, Any]:
    return {"states": clause.states, "rests_on": list(clause.rests_on)}


def _encode_agreement(agreement: Agreement | None) -> dict[str, Any] | None:
    if agreement is None:
        return None
    return {
        "question": agreement.question,
        "answers": [
            {"stated": answer.stated, "given": answer.given}
            for answer in agreement.answers
        ],
    }


def _decode_decision(entry: dict[str, Any]) -> InvestmentDecision:
    return InvestmentDecision(
        decision_id=entry["decision_id"],
        subject=entry["subject"],
        question=DecisionQuestion(entry["question"]),
        decided_at=datetime.fromisoformat(entry["decided_at"]),
        occasion=entry["occasion"],
        occasioned_by=tuple(entry["occasioned_by"]),
        facts=_decode_facts(entry["facts"]),
        facts_because=entry["facts_because"],
        portfolio=_decode_context(entry["portfolio"]),
        market=_decode_context(entry["market"]),
        policy=(
            None
            if entry["policy"] is None
            else DeclaredPolicy(
                version=entry["policy"]["version"],
                clauses=tuple(entry["policy"]["clauses"]),
            )
        ),
        policy_because=entry["policy_because"],
        verdict=(
            None if entry["verdict"] is None else DecisionVerdict(entry["verdict"])
        ),
        refusal=(
            None
            if entry["refusal"] is None
            else Refusal(because=entry["refusal"]["because"])
        ),
        action=entry["action"],
        raises=(None if entry["raises"] is None else DecisionQuestion(entry["raises"])),
        clauses=_decode_clauses(entry["clauses"]),
        weighed=tuple(
            Implication(
                course=item["course"],
                because=item["because"],
                rests_on=tuple(item["rests_on"]),
                prevailed=item["prevailed"],
            )
            for item in entry["weighed"]
        ),
        decided_by=entry["decided_by"],
        rests_on=_decode_agreement(entry["rests_on"]),
        rests_on_because=entry["rests_on_because"],
        absences=tuple(entry["absences"]),
        predecessor=entry["predecessor"],
    )


def _decode_facts(payload: dict[str, Any] | None) -> EstablishedFacts | None:
    if payload is None:
        return None
    return EstablishedFacts(
        source=payload["source"],
        consensus_state=payload["consensus_state"],
        observation_count=payload["observation_count"],
        quorum=payload["quorum"],
        reading=Provenance(
            source=payload["reading"]["source"],
            observed_at=datetime.fromisoformat(payload["reading"]["observed_at"]),
            last_known=payload["reading"]["last_known"],
        ),
        facts=tuple(payload["facts"]),
    )


def _decode_context(payload: dict[str, Any]) -> ContextObservation:
    return ContextObservation(
        kind=payload["kind"],
        observed_at=(
            None
            if payload["observed_at"] is None
            else datetime.fromisoformat(payload["observed_at"])
        ),
        facts=tuple(payload["facts"]),
        absent_because=payload["absent_because"],
    )


def _decode_clauses(payload: dict[str, Any] | None) -> Clauses | None:
    if payload is None:
        return None
    return Clauses(
        what_changed=_decode_clause(payload["what_changed"]),
        why_it_matters=_decode_clause(payload["why_it_matters"]),
        why_for_this_investor=_decode_clause(payload["why_for_this_investor"]),
    )


def _decode_clause(payload: dict[str, Any]) -> Clause:
    return Clause(states=payload["states"], rests_on=tuple(payload["rests_on"]))


def _decode_agreement(payload: dict[str, Any] | None) -> Agreement | None:
    if payload is None:
        return None
    return Agreement(
        question=payload["question"],
        answers=tuple(
            Answer(stated=item["stated"], given=item["given"])
            for item in payload["answers"]
        ),
    )
