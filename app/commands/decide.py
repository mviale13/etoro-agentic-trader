"""`movrvest decide SYMBOL QUESTION` — ask the platform one question.

The surface gathers the basis and renders the decision; it decides
nothing itself. Established facts come from the knowledge store only
(never the acquiring service — asking what the platform should do must
not spend anything), declared policy from its file with a content-hash
version, and portfolio context from the broker — absent with its
reason when the broker is unreachable, which the rule table turns into
the honest outcome rather than this surface guessing one.

Every run appends one decision event to the (subject, question)
stream and shows the full object: the outcome, the clauses with their
edges, the implications weighed with the losers preserved, and what it
all rests on.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import get_settings
from app.domain.business_understanding import BusinessUnderstanding
from app.domain.investment_decision import DecisionQuestion, InvestmentDecision
from app.domain.knowledge_consensus import CompanyKnowledgeConsensus, consensus_of
from app.domain.playbook_selection import PlaybookSelection, RefusedGrounding
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.repositories.investment_decision_store import JsonInvestmentDecisionStore
from app.services.account_service import AccountService
from app.services.entry_question import EntryCase, decide
from app.services.playbook_mapping import select_grounded
from app.services.policy_service import PolicyService
from app.services.portfolio_service import PortfolioService
from app.services.understanding_engine import understand

POLICY_PATH = Path("config/policy.yaml")


class DecideCommand:
    async def run(self, symbol: str, question_raw: str) -> int:
        normalized = symbol.upper().strip()
        try:
            question = DecisionQuestion(question_raw.lower().strip())
        except ValueError:
            questions = ", ".join(q.value for q in DecisionQuestion)
            print(f"Unknown question '{question_raw}'. The vocabulary: {questions}.")
            return 2

        consensus, consensus_because = _stored_consensus(normalized)
        understanding: BusinessUnderstanding | None = None
        selection: PlaybookSelection | None = None
        selection_because: str | None = None
        if consensus is not None:
            understanding = understand(consensus)
            grounded = select_grounded(understanding)
            if isinstance(grounded, RefusedGrounding):
                selection_because = grounded.because
            else:
                selection = grounded

        policy = None
        policy_version: str | None = None
        policy_because: str | None = None
        try:
            policy = PolicyService().load()
            policy_version = _policy_version()
        except Exception as error:  # noqa: BLE001 — worded absence, never a crash
            policy_because = f"declared policy unavailable: {error}"

        portfolio, portfolio_because = await _broker_portfolio()

        store = JsonInvestmentDecisionStore()
        current = store.current(normalized, question)
        case = EntryCase(
            subject=normalized,
            question=question,
            occasion="asked by the investor (movrvest decide)",
            decided_at=datetime.now(UTC),
            decision_id=store.next_id(normalized, question),
            predecessor=current.decision_id if current is not None else None,
            consensus=consensus,
            consensus_because=consensus_because,
            understanding=understanding,
            selection=selection,
            selection_because=selection_because,
            portfolio=portfolio,
            portfolio_because=portfolio_because,
            policy=policy,
            policy_version=policy_version,
            policy_because=policy_because,
        )
        decision = decide(case)
        store.append(decision)
        _render(decision)
        return 0 if decision.verdict is not None else 1


def _stored_consensus(
    symbol: str,
) -> tuple[CompanyKnowledgeConsensus | None, str | None]:
    observations = JsonCompanyKnowledgeStore().latest(symbol)
    if not observations:
        return None, (f"no stored observations of {symbol}; nothing has been read")
    return consensus_of(observations), None


def _policy_version() -> str:
    digest = hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
    return digest[:12]


async def _broker_portfolio() -> tuple[PortfolioSnapshot | None, str | None]:
    try:
        account = await AccountService(EtoroAccountBroker(get_settings())).snapshot()
        return PortfolioService().analyze(account), None
    except Exception as error:  # noqa: BLE001 — worded absence, never a crash
        return None, f"portfolio context unavailable: {error}"


def _render(decision: InvestmentDecision) -> None:
    print(f"{decision.subject} — the {decision.question.value} question")
    print(f"  decision {decision.decision_id}, {decision.decided_at.isoformat()}")
    print(f"  occasion: {decision.occasion}")
    if decision.predecessor is not None:
        print(f"  supersedes: {decision.predecessor}")
    print()
    if decision.verdict is not None:
        print(f"  verdict: {decision.verdict.value.upper()}")
    if decision.refusal is not None:
        print(f"  refused: {decision.refusal.because}")
    print(f"  decided by: {decision.decided_by}")
    if decision.action is not None:
        print(f"  action: {decision.action}")
    if decision.raises is not None:
        print(f"  raises: the {decision.raises.value} question")
    print()
    if decision.clauses is not None:
        _clause("what changed", decision.clauses.what_changed.states)
        _clause("why it matters", decision.clauses.why_it_matters.states)
        _clause(
            "why it matters for this investor",
            decision.clauses.why_for_this_investor.states,
        )
        print()
    if decision.weighed:
        print("  weighed:")
        for implication in decision.weighed:
            marker = "prevailed" if implication.prevailed else "did not prevail"
            print(f"    - {implication.course} ({marker})")
            print(f"      because {implication.because}")
        print()
    if decision.rests_on is not None:
        print(
            f"  rests on: {decision.rests_on.stated_majority()} — "
            f"{decision.rests_on.question}"
        )
    if decision.rests_on_because is not None:
        print(f"  rests on: {decision.rests_on_because}")
    for absence in decision.absences:
        print(f"  absent: {absence}")
    print()
    print("  basis:")
    if decision.facts is not None:
        print(
            f"    facts: {decision.facts.source} — "
            f"{decision.facts.observation_count}/{decision.facts.quorum} "
            f"observations, {decision.facts.consensus_state}"
        )
    if decision.facts_because is not None:
        print(f"    facts: absent — {decision.facts_because}")
    if decision.policy is not None:
        clauses = "; ".join(decision.policy.clauses)
        print(f"    policy: version {decision.policy.version} — {clauses}")
    if decision.policy_because is not None:
        print(f"    policy: absent — {decision.policy_because}")
    _context("portfolio", decision.portfolio.facts, decision.portfolio.absent_because)
    _context("market", decision.market.facts, decision.market.absent_because)


def _clause(label: str, states: str) -> None:
    print(f"  {label}: {states}")


def _context(kind: str, facts: tuple[str, ...], absent_because: str | None) -> None:
    if absent_because is not None:
        print(f"    {kind}: {absent_because}")
    else:
        print(f"    {kind}: {'; '.join(facts)}")


async def run(symbol: str, question: str) -> int:
    return await DecideCommand().run(symbol, question)
