"""The entry question's rule table — the first verdicts this platform makes.

One deterministic table for one question (*should this security enter
the portfolio?*), proven on JPM, per the first slice
`docs/architecture/INVESTMENT_DECISION.md` scoped. The other three
questions are refused by name until a case and a table earn them —
never answered by a neighbouring table.

The table is a pure function: the caller gathers the basis (facts from
the store, policy from its file, portfolio from the broker) and the
same case in produces the same decision out. No model is asked, nothing
is read, and nothing downstream of the gathered inputs can vary.

Two boundaries the rules keep, stated because they are easy to lose:

- **Policy is obeyed, not weighed.** A rejection for lack of policy
  room is arithmetic, not an adjudication of the case's merits — the
  merits are recorded as not reached.
- **No admissible assessment layer exists yet**, so RECOMMEND and a
  reasoned REJECT-on-merits are unreachable by construction: the rules
  select only among courses their inputs actually imply. The honest
  terminal verdict for a complete, eligible case is MONITOR, with the
  eligibility implication preserved as the loser.

The room arithmetic reads the stocks allocation target because the
table's one earned case (JPM) is an equity; another asset class earns
its own reading or refuses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.business_understanding import BusinessUnderstanding
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
from app.domain.investment_policy import InvestmentPolicy
from app.domain.knowledge_consensus import CompanyKnowledgeConsensus
from app.domain.playbook_selection import PlaybookSelection
from app.domain.portfolio_snapshot import PortfolioSnapshot

RULE_QUESTION_UNMAPPED = "question-unmapped-refuses"
RULE_POLICY_REQUIRED = "entry-requires-declared-policy"
RULE_PORTFOLIO_REQUIRED = "entry-requires-portfolio-context"
RULE_NOT_APPLICABLE_HELD = "entry-not-applicable-to-held"
RULE_NO_ROOM = "entry-no-policy-room-rejects"
RULE_BELOW_QUORUM = "entry-below-quorum-investigates"
RULE_NO_AUTHORITATIVE_PLAYBOOK = "entry-no-authoritative-playbook-monitors"
RULE_NO_CASE = "entry-no-assessment-establishes-a-case"

#: v1 consumes no market context; the basis says so rather than staying
#: silent about it.
MARKET_NOT_CONSUMED = (
    "not consumed: rule table entry-v1 consumes established facts, declared "
    "policy, and portfolio context only"
)


@dataclass(frozen=True, slots=True)
class EntryCase:
    """Everything the entry-v1 table may consume, gathered by the caller.

    Every absent input arrives with its reason, so the table never has
    to invent one — it only ever passes another layer's wording through.
    """

    subject: str
    question: DecisionQuestion
    occasion: str
    decided_at: datetime
    decision_id: str
    predecessor: str | None

    consensus: CompanyKnowledgeConsensus | None
    consensus_because: str | None
    understanding: BusinessUnderstanding | None
    selection: PlaybookSelection | None
    selection_because: str | None

    portfolio: PortfolioSnapshot | None
    portfolio_because: str | None

    policy: InvestmentPolicy | None
    policy_version: str | None
    policy_because: str | None


def decide(case: EntryCase) -> InvestmentDecision:
    """Answer the case's question, or refuse with the reason.

    Rules fire in a fixed order and the first that applies decides;
    the order is part of the table's semantics, not an implementation
    detail: policy and portfolio are mandatory context, applicability
    (held) precedes arithmetic (room), and room precedes the quorum
    ladder because no spend is decided for a case policy forbids.
    """

    if case.question is not DecisionQuestion.ENTRY:
        return _refuse(case, RULE_QUESTION_UNMAPPED, _unmapped_because(case))
    if case.policy is None:
        return _refuse(
            case,
            RULE_POLICY_REQUIRED,
            "declared policy is a mandatory input to the entry question: "
            + (case.policy_because or "no reason recorded"),
        )
    if case.portfolio is None:
        return _refuse(
            case,
            RULE_PORTFOLIO_REQUIRED,
            "portfolio context is a mandatory input to the entry question: "
            + (case.portfolio_because or "no reason recorded"),
        )

    held_pct = _held_weight(case.subject, case.portfolio)
    if held_pct is not None:
        return _refuse(
            case,
            RULE_NOT_APPLICABLE_HELD,
            f"the entry question does not apply to a held position: "
            f"{case.subject} is held at {held_pct:.1f}% of the portfolio; "
            "the increase and decrease questions apply",
        )

    cap = case.policy.constraints.max_single_position
    allocation_room = case.policy.target.stocks - case.portfolio.allocation.stocks
    room = min(cap, allocation_room)
    if room <= 0:
        return _reject_no_room(case, cap=cap, allocation_room=allocation_room)

    if case.consensus is None or not case.consensus.is_quorate:
        return _investigate_below_quorum(case, room=room)
    if case.selection is None or not case.selection.authoritative:
        return _monitor_without_playbook(case, room=room)
    return _monitor_eligible(case, room=room)


def _unmapped_because(case: EntryCase) -> str:
    because = (
        f"no rule table answers the {case.question.value} question in v1; "
        "the vocabulary reserves it until a case and a table are earned"
    )
    if case.question is DecisionQuestion.RESEARCH_SPEND:
        because += (
            " (it is raised by INVESTIGATE and will be decided when its table exists)"
        )
    return because


def _held_weight(subject: str, portfolio: PortfolioSnapshot) -> float | None:
    for holding in portfolio.holdings:
        if holding.is_resolved and holding.symbol.upper() == subject:
            return portfolio.weight_pct(holding) or 0.0
    return None


def _policy_edges(case: EntryCase) -> tuple[str, ...]:
    policy = case.policy
    assert policy is not None
    return (
        f"policy:version={case.policy_version or 'unstated'}",
        f"policy:risk_profile={policy.risk_profile}",
        f"policy:target.stocks={policy.target.stocks:g}%",
        "policy:constraints.max_single_position="
        f"{policy.constraints.max_single_position:g}%",
    )


def _portfolio_edges(case: EntryCase) -> tuple[str, ...]:
    portfolio = case.portfolio
    assert portfolio is not None
    as_of = portfolio.last_sync.isoformat() if portfolio.last_sync else "unstated"
    return (
        f"portfolio:{case.subject}_held=no",
        f"portfolio:allocation.stocks={portfolio.allocation.stocks:.1f}%",
        f"portfolio:as_of={as_of}",
    )


def _fact_edges(case: EntryCase) -> tuple[str, ...]:
    facts = _established(case)
    if facts is None:
        return (f"facts:absent={case.consensus_because or 'no reason recorded'}",)
    return tuple(f"facts:{fact}" for fact in facts.facts)


def _room_statement(case: EntryCase, *, room: float) -> str:
    policy = case.policy
    portfolio = case.portfolio
    assert policy is not None and portfolio is not None
    allocation_room = policy.target.stocks - portfolio.allocation.stocks
    return (
        f"room to enter: {room:.1f}% of the portfolio — the smaller of the "
        f"{policy.constraints.max_single_position:g}% single-position cap "
        f"and the {allocation_room:.1f}% distance from the current "
        f"{portfolio.allocation.stocks:.1f}% stocks allocation to its "
        f"{policy.target.stocks:g}% target"
    )


def _established(case: EntryCase) -> EstablishedFacts | None:
    consensus = case.consensus
    if consensus is None:
        return None
    facts: tuple[str, ...] = (
        f"source={consensus.stated_source()}",
        f"observations={consensus.observation_count}/{consensus.quorum}",
    )
    if case.understanding is not None:
        facts += (f"archetype={case.understanding.characteristics.stated}",)
    if case.selection is not None and case.selection.authoritative:
        facts += (
            f"playbook={case.selection.playbook.name}",
            f"playbook_rule={case.selection.rule_fired}",
        )
        facts += tuple(case.selection.facts_consumed)
    return EstablishedFacts(
        source=consensus.stated_source(),
        consensus_state=consensus.state.value,
        observation_count=consensus.observation_count,
        quorum=consensus.quorum,
        reading=consensus.reading,
        facts=facts,
    )


def _declared_policy(case: EntryCase) -> DeclaredPolicy | None:
    policy = case.policy
    if policy is None:
        return None
    return DeclaredPolicy(
        version=case.policy_version or "unstated",
        clauses=(
            f"risk_profile: {policy.risk_profile}",
            f"target.stocks: {policy.target.stocks:g}%",
            "constraints.max_single_position: "
            f"{policy.constraints.max_single_position:g}%",
        ),
    )


def _portfolio_observation(case: EntryCase) -> ContextObservation:
    portfolio = case.portfolio
    if portfolio is None:
        return ContextObservation(
            kind="portfolio",
            observed_at=None,
            facts=(),
            absent_because=case.portfolio_because or "unavailable",
        )
    held = _held_weight(case.subject, portfolio)
    held_fact = (
        f"{case.subject} held at {held:.1f}%"
        if held is not None
        else f"{case.subject} not held"
    )
    return ContextObservation(
        kind="portfolio",
        observed_at=portfolio.last_sync,
        facts=(
            "width-1, uncalibrated broker observation",
            held_fact,
            f"allocation.stocks={portfolio.allocation.stocks:.1f}%",
            f"positions={portfolio.positions}",
        ),
        absent_because=None,
    )


def _market_observation() -> ContextObservation:
    return ContextObservation(
        kind="market",
        observed_at=None,
        facts=(),
        absent_because=MARKET_NOT_CONSUMED,
    )


def _absences(case: EntryCase) -> tuple[str, ...]:
    if case.understanding is None:
        return ()
    return tuple(
        f"{gap.segment} {gap.dimension.value} not established: {gap.because}"
        for gap in case.understanding.not_established
    )


def _what_changed(case: EntryCase) -> Clause:
    if case.predecessor is None:
        return Clause(
            states=(
                f"first consideration of the {case.question.value} question "
                f"for {case.subject}; nothing preceded"
            ),
            rests_on=(f"occasion:{case.occasion}",),
        )
    return Clause(
        states=(
            f"the {case.question.value} question was asked again; this "
            f"decision supersedes {case.predecessor}"
        ),
        rests_on=(
            f"occasion:{case.occasion}",
            f"predecessor:{case.predecessor}",
        ),
    )


def _decision(
    case: EntryCase,
    *,
    rule: str,
    verdict: DecisionVerdict | None,
    refusal: Refusal | None,
    clauses: Clauses | None,
    weighed: tuple[Implication, ...],
    action: str | None = None,
    raises: DecisionQuestion | None = None,
    rests_on_because: str | None = None,
) -> InvestmentDecision:
    facts = _established(case)
    narrowest = None
    if (
        verdict is not None
        and rests_on_because is None
        and case.understanding is not None
    ):
        narrowest = case.understanding.characteristics.narrowest
    if verdict is not None and narrowest is None and rests_on_because is None:
        rests_on_because = "the consumed conclusion carried no narrowest agreement"
    return InvestmentDecision(
        decision_id=case.decision_id,
        subject=case.subject,
        question=case.question,
        decided_at=case.decided_at,
        occasion=case.occasion,
        occasioned_by=(),
        facts=facts,
        facts_because=(
            None
            if facts is not None
            else case.consensus_because or "no stored observations"
        ),
        portfolio=_portfolio_observation(case),
        market=_market_observation(),
        policy=_declared_policy(case),
        policy_because=(
            None if case.policy is not None else case.policy_because or "unavailable"
        ),
        verdict=verdict,
        refusal=refusal,
        action=action,
        raises=raises,
        clauses=clauses,
        weighed=weighed,
        decided_by=rule,
        rests_on=narrowest if verdict is not None else None,
        rests_on_because=rests_on_because if verdict is not None else None,
        absences=_absences(case),
        predecessor=case.predecessor,
    )


def _refuse(case: EntryCase, rule: str, because: str) -> InvestmentDecision:
    return _decision(
        case,
        rule=rule,
        verdict=None,
        refusal=Refusal(because=because),
        clauses=None,
        weighed=(),
    )


def _reject_no_room(
    case: EntryCase, *, cap: float, allocation_room: float
) -> InvestmentDecision:
    policy_edges = _policy_edges(case)
    portfolio_edges = _portfolio_edges(case)
    arithmetic = (
        f"allocation room is {allocation_room:.1f}% against the "
        f"{cap:g}% single-position cap; the smaller is not positive"
    )
    return _decision(
        case,
        rule=RULE_NO_ROOM,
        verdict=DecisionVerdict.REJECT,
        refusal=None,
        clauses=Clauses(
            what_changed=_what_changed(case),
            why_it_matters=Clause(
                states=(
                    "the declared policy leaves no room to enter any new "
                    "equity position; the case's merits were not reached"
                ),
                rests_on=policy_edges + portfolio_edges,
            ),
            why_for_this_investor=Clause(
                states=(
                    "rejected on the current basis, for this question, at "
                    f"this time: {arithmetic}; a policy edit or a portfolio "
                    "change is the occasion to ask again"
                ),
                rests_on=policy_edges + portfolio_edges,
            ),
        ),
        weighed=(
            Implication(
                course="do not enter; the declared policy leaves no room",
                because=arithmetic,
                rests_on=policy_edges + portfolio_edges,
                prevailed=True,
            ),
        ),
        rests_on_because=(
            "no consensus claim consumed: the declared policy left no room "
            "to enter, and the outcome is arithmetic over policy and "
            "portfolio alone"
        ),
    )


def _investigate_below_quorum(case: EntryCase, *, room: float) -> InvestmentDecision:
    fact_edges = _fact_edges(case)
    width = (
        f"{case.consensus.observation_count} of {case.consensus.quorum} observations"
        if case.consensus is not None
        else "no stored observations"
    )
    return _decision(
        case,
        rule=RULE_BELOW_QUORUM,
        verdict=DecisionVerdict.INVESTIGATE,
        refusal=None,
        raises=DecisionQuestion.RESEARCH_SPEND,
        clauses=Clauses(
            what_changed=_what_changed(case),
            why_it_matters=Clause(
                states=(
                    "the entry question is worth answering and cannot yet "
                    f"be answered: understanding rests on {width}, below "
                    "quorum, and the gap is acquirable by observation"
                ),
                rests_on=fact_edges,
            ),
            why_for_this_investor=Clause(
                states=(
                    f"{_room_statement(case, room=room)}; nothing enters "
                    "the book from sub-quorum knowledge, and the spend "
                    "itself is decided by the research-spend question this "
                    "decision raises"
                ),
                rests_on=_policy_edges(case) + _portfolio_edges(case),
            ),
        ),
        weighed=(
            Implication(
                course=(
                    "defer the entry question and raise the research-spend question"
                ),
                because=(
                    f"understanding rests on {width}; a conclusion at this "
                    "width would present one reading as the account"
                ),
                rests_on=fact_edges,
                prevailed=True,
            ),
        ),
        rests_on_because=(
            f"below quorum ({width}): no claim is called settled at this width"
        ),
    )


def _monitor_without_playbook(case: EntryCase, *, room: float) -> InvestmentDecision:
    fact_edges = _fact_edges(case)
    gap = (
        case.selection_because
        or "the grounded route did not produce an authoritative selection"
    )
    return _decision(
        case,
        rule=RULE_NO_AUTHORITATIVE_PLAYBOOK,
        verdict=DecisionVerdict.MONITOR,
        refusal=None,
        clauses=Clauses(
            what_changed=_what_changed(case),
            why_it_matters=Clause(
                states=(
                    "the business is at quorum but no authoritative "
                    f"playbook activates: {gap}; more observations would "
                    "not close a rules gap, so nothing is spent"
                ),
                rests_on=fact_edges,
            ),
            why_for_this_investor=Clause(
                states=(
                    f"{_room_statement(case, room=room)}; the entry "
                    "question stays open with no case put to it, and "
                    "nothing changes on the book"
                ),
                rests_on=_policy_edges(case) + _portfolio_edges(case),
            ),
        ),
        weighed=(
            Implication(
                course="keep the entry question open without concluding",
                because=gap,
                rests_on=fact_edges,
                prevailed=True,
            ),
        ),
    )


def _monitor_eligible(case: EntryCase, *, room: float) -> InvestmentDecision:
    selection = case.selection
    understanding = case.understanding
    assert selection is not None and understanding is not None
    fact_edges = _fact_edges(case)
    policy_edges = _policy_edges(case)
    portfolio_edges = _portfolio_edges(case)
    return _decision(
        case,
        rule=RULE_NO_CASE,
        verdict=DecisionVerdict.MONITOR,
        refusal=None,
        clauses=Clauses(
            what_changed=_what_changed(case),
            why_it_matters=Clause(
                states=(
                    f"every link is established: the {selection.playbook.name} "
                    f"playbook is active by rule {selection.rule_fired} on a "
                    f"quorate understanding ({understanding.engine}); nothing "
                    "yet establishes a case for or against entering, because "
                    "the assessment layer the playbook prescribes has not run "
                    "under the decision contract"
                ),
                rests_on=fact_edges,
            ),
            why_for_this_investor=Clause(
                states=(
                    f"{_room_statement(case, room=room)}; until an admissible "
                    "assessment exists, the honest stance is to keep the "
                    "entry question open"
                ),
                rests_on=policy_edges + portfolio_edges,
            ),
        ),
        weighed=(
            Implication(
                course="progress the entry question toward an assessment",
                because=(
                    "the chain is complete and the declared policy leaves "
                    "room; the case is eligible to be put to an assessment"
                ),
                rests_on=fact_edges + policy_edges,
                prevailed=False,
            ),
            Implication(
                course="keep the entry question open without concluding",
                because=(
                    "no admissible assessment exists under the decision "
                    "contract; a conclusion for or against entry would be "
                    "unsupported by the inputs"
                ),
                rests_on=("facts:assessments=absent",),
                prevailed=True,
            ),
        ),
    )
