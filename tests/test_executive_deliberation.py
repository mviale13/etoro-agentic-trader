"""The Executive layer's account of *why*, not only of *what happened*.

The gap this closes, in the platform's own output. Before it, every
conclusion carried the same sentence — *the investment case satisfies
quality, evidence, valuation, risk, and portfolio gates* — and an
investor could read which thresholds were cleared but never that two
committees concurred, that one dissented, or what remained unsettled.

Four claims are tested here, and each is something a scoring engine
cannot state: the conclusion names what prevailed and over what; a
dissent survives being overruled; unresolved uncertainty is its own
part of the conclusion rather than a reason against the security; and
every part still resolves to a canonical finding.
"""

from datetime import UTC, datetime

from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.application.committees.opinion_builder import Input, build
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.executive.decision_synthesis_builder import synthesise
from app.brain import BrainBuilder
from app.cio.artificial_cio import ArtificialCIO
from app.domain.committee.opinion import Stance, Uncertainty, UncertaintyKind
from app.domain.decision_state import DecisionState
from app.domain.executive_decision import ExecutiveDecision
from app.domain.finding import Dimension, Finding, FindingLedger
from app.domain.provenance import Provenance
from tests.test_brain_context import make_market, make_policy, make_portfolio
from tests.test_security_evidence import make_company

WIDE = Finding.favourable("Returns on capital are wide.", Dimension.QUALITY)
COMPOUNDS = Finding.favourable("It reinvests at high rates.", Dimension.QUALITY)
DEAR = Finding.adverse("It is priced for perfection.", Dimension.VALUATION)
FELL = Finding.adverse("It fell 61% from its high.", Dimension.RISK)


def ledger() -> FindingLedger:
    return FindingLedger.of((WIDE, COMPOUNDS, DEAR, FELL))


def investment(*, contested: bool = False):
    """A positive Investment Committee, optionally over an objection."""

    findings = (WIDE, COMPOUNDS, DEAR) if contested else (WIDE, COMPOUNDS)

    return build(
        committee="Investment Committee",
        remit=frozenset({Dimension.QUALITY, Dimension.VALUATION}),
        ledger=FindingLedger.of(findings),
        inputs=(
            Input(name="business quality", value=1),
            Input(name="valuation", value=1),
        ),
    )


def risk(*, negative: bool = True, unmeasured: bool = False):
    if unmeasured:
        return build(
            committee="Risk Committee",
            remit=frozenset({Dimension.RISK}),
            ledger=FindingLedger.of(()),
            abstain_because="The price history is too short to measure risk.",
        )

    return build(
        committee="Risk Committee",
        remit=frozenset({Dimension.RISK}),
        ledger=FindingLedger.of((FELL,) if negative else ()),
        inputs=(Input(name="price history", value=1),),
    )


def decision(
    *,
    opinions: tuple,
    state: DecisionState = DecisionState.RECOMMEND,
    strengths: tuple[str, ...] = (WIDE.statement, COMPOUNDS.statement),
    risks: tuple[str, ...] = (DEAR.statement,),
) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol="EXA",
        state=state,
        conviction=78,
        rationale=(
            "The investment case satisfies quality, evidence, valuation, "
            "risk, and portfolio gates."
        ),
        evidence_as_of=Provenance(source="test", observed_at=datetime.now(UTC)),
        key_strengths=strengths,
        key_risks=risks,
        findings=ledger(),
        opinions=opinions,
    )


# ── the conclusion names what prevailed ─────────────────────────────


def test_the_conclusion_says_why_and_not_only_which_gates_cleared() -> None:
    synthesis = synthesise(decision(opinions=(investment(), risk())))

    assert synthesis.deliberation is not None

    # The verdict, in the CIO's own recorded words.
    assert "RECOMMEND" in synthesis.deliberation.prevailed
    assert "78/100" in synthesis.deliberation.prevailed

    # And what the committees did, counted.
    assert "committee(s) took a position" in synthesis.deliberation.because


def test_a_dissent_survives_being_overruled() -> None:
    """
    The property a score cannot carry.

    A conviction of 78 is the same number whether one committee objected
    or none did. Preserving the losing position is what lets an investor
    weigh the decision instead of only receiving it.
    """

    synthesis = synthesise(decision(opinions=(investment(), risk(negative=True))))

    assert synthesis.deliberation is not None
    assert synthesis.deliberation.over is not None
    assert "Risk Committee" in synthesis.deliberation.over
    assert "did not carry" in synthesis.deliberation.over
    assert "recorded rather than dropped" in synthesis.deliberation.over


def test_the_dissent_is_whichever_side_the_decision_declined_to_take() -> None:
    """
    RECOMMEND is the only state that acts on the bullish case.

    Read off `belongs_to_watchlist` — true for everything but REJECT —
    this named the negative committee as the loser under PREPARE, where
    the platform had in fact declined to follow the *positive* one. Four
    of the five states reported the wrong dissent.
    """

    divided = (investment(), risk(negative=True))

    acted = synthesise(decision(opinions=divided, state=DecisionState.RECOMMEND))

    held = synthesise(decision(opinions=divided, state=DecisionState.PREPARE))

    rejected = synthesise(decision(opinions=divided, state=DecisionState.REJECT))

    assert acted.deliberation is not None
    assert held.deliberation is not None
    assert rejected.deliberation is not None

    # Acting on the case overrules the objection.
    assert "Risk Committee" in (acted.deliberation.over or "")

    # Declining to act overrules the case for it — under both the state
    # that is merely holding back and the state that refuses outright.
    assert "Investment Committee" in (held.deliberation.over or "")
    assert "Investment Committee" in (rejected.deliberation.over or "")


def test_agreement_is_reported_where_the_committees_agree() -> None:
    synthesis = synthesise(decision(opinions=(investment(), risk(negative=False))))

    assert synthesis.deliberation is not None
    assert synthesis.deliberation.over is None
    assert "agree" in synthesis.deliberation.agreement


def test_the_platform_never_claims_to_have_weighed_the_stances() -> None:
    """
    The Artificial CIO gates on scores. It does not tally committees.

    A sentence here implying the stances had been counted would describe
    a deliberation that did not happen — the most flattering possible
    misdescription of a gate.
    """

    synthesis = synthesise(decision(opinions=(investment(), risk())))

    assert synthesis.deliberation is not None
    assert "does not count committee stances" in synthesis.deliberation.because


def test_a_case_no_committee_spoke_on_has_no_deliberation() -> None:
    """Silence is reported as silence, not as an uncontested conclusion."""

    synthesis = synthesise(decision(opinions=(risk(unmeasured=True),)))

    assert synthesis.deliberation is None
    assert not synthesis.is_deliberated


# ── uncertainty is its own part ─────────────────────────────────────


def test_what_is_unknown_is_not_filed_as_a_reason_against() -> None:
    """
    Not knowing something is not bearishness.

    The opposing case carries facts that were read; an unmeasured input
    is the thing that would settle the case, and it belongs here.
    """

    unreadable = build(
        committee="Investment Committee",
        remit=frozenset({Dimension.QUALITY, Dimension.VALUATION}),
        ledger=FindingLedger.of((WIDE, COMPOUNDS)),
        inputs=(
            Input(name="business quality", value=1),
            Input(
                name="valuation",
                value=None,
                absent_because="Valuation could not be read for EXA.",
            ),
        ),
    )

    synthesis = synthesise(decision(opinions=(unreadable, risk()), risks=()))

    assert [item.about for item in synthesis.uncertainty] == [
        "Valuation could not be read for EXA."
    ]

    # And it is attributed, because which committee cannot see something
    # tells the investor which half of the case is held back.
    assert synthesis.uncertainty[0].committee == "Investment Committee"

    assert all(
        "Valuation could not be read" not in fact.statement
        for fact in synthesis.despite
    )


def test_an_unanswerable_question_is_never_reported_as_pending() -> None:
    token = build(
        committee="Investment Committee",
        remit=frozenset({Dimension.QUALITY}),
        ledger=FindingLedger.of((WIDE,)),
        uncertainty=(
            Uncertainty(
                kind=UncertaintyKind.OUTSIDE_KNOWLEDGE,
                about="A cryptocurrency has no business quality to assess.",
            ),
        ),
    )

    synthesis = synthesise(decision(opinions=(token,)))

    assert not synthesis.uncertainty[0].is_resolvable


def test_nothing_outstanding_is_distinguished_from_nobody_looking() -> None:
    """
    An empty list under a panel that never sat reads as a complete
    picture, which is the most flattering possible misreading.
    """

    reviewed = synthesise(decision(opinions=(investment(), risk())))

    unreviewed = synthesise(decision(opinions=()))

    assert reviewed.uncertainty_absent is not None
    assert "Nothing here says the picture is complete" in reviewed.uncertainty_absent

    assert unreviewed.uncertainty_absent is not None
    assert "absence of review" in unreviewed.uncertainty_absent


# ── every part still resolves to a canonical finding ────────────────


def test_each_fact_names_the_committee_that_stood_on_it() -> None:
    synthesis = synthesise(decision(opinions=(investment(contested=True), risk())))

    supporting = {fact.statement: fact.committee for fact in synthesis.because}

    assert supporting[WIDE.statement] == "Investment Committee"
    assert supporting[COMPOUNDS.statement] == "Investment Committee"

    opposing = {fact.statement: fact.committee for fact in synthesis.despite}

    assert opposing[DEAR.statement] == "Investment Committee"


def test_attribution_is_resolved_through_the_ledger_never_matched_on_words() -> None:
    """
    A fact no committee's remit covers attributes to nobody, and says so.

    Guessing from the wording is exactly what the preserved dimension
    exists to stop.
    """

    unclaimed = synthesise(
        decision(
            opinions=(risk(),),
            strengths=("A statement no committee ever pointed at.",),
        )
    )

    assert unclaimed.because[0].committee is None


# ── end to end, through the real pipeline ───────────────────────────


def test_a_real_case_reaches_the_investor_as_a_discussion() -> None:
    """
    The acceptance case: signals to conclusion, no fixtures in between.

    Everything here is built by the code the investor's dossier runs —
    the ledger the evidence builder gathers, the positions the real
    committees take over it, and the synthesis composed from the
    decision that resulted.
    """

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"EXA": (make_company("EXA"),)},
    ).build()

    builder = DecisionEvidenceBuilder()

    findings = builder.ledger("EXA", brain)

    opinions = CommitteeService().review(brain, "EXA", findings)

    evidence = builder.build(
        "EXA",
        brain,
        ReasoningService().reason(brain),
        opinions,
        findings=findings,
    )

    made = ArtificialCIO().decide(evidence)

    # The decision carries what the committees said, verbatim.
    assert made.opinions == opinions
    assert made.findings == findings

    synthesis = synthesise(made)

    # Every reference a committee recorded resolves in the decision's
    # own ledger — the property that makes the conclusion auditable.
    for opinion in synthesis_opinions(made):
        for ref in (*opinion.supporting, *opinion.opposing):
            assert made.findings.resolve(ref) is not None

    # And the conclusion states its uncertainty rather than implying none.
    assert synthesis.uncertainty or synthesis.uncertainty_absent


def synthesis_opinions(made: ExecutiveDecision):
    return made.opinions


def test_the_committees_never_see_each_other() -> None:
    """
    Independence, structurally: a committee's opinion is a pure function
    of the brain, the symbol and the ledger.

    Committees that could accommodate one another would move the
    adjudication a layer early, and the agreement an investor is shown
    would be partly an artefact of the order they ran in.
    """

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        evidence={"EXA": (make_company("EXA"),)},
    ).build()

    findings = DecisionEvidenceBuilder().ledger("EXA", brain)

    forwards = CommitteeService().review(brain, "EXA", findings)

    service = CommitteeService()

    # Reviewed alone, each committee reaches exactly what it reached
    # beside the other.
    assert service.investment.review(brain, "EXA", findings) == forwards[0]
    assert service.risk.review(brain, "EXA", findings) == forwards[1]


def test_a_neutral_stance_is_a_position_and_an_abstention_is_not() -> None:
    balanced = build(
        committee="Investment Committee",
        remit=frozenset({Dimension.QUALITY, Dimension.VALUATION}),
        ledger=FindingLedger.of((WIDE, DEAR)),
        inputs=(Input(name="business quality", value=1),),
    )

    synthesis = synthesise(decision(opinions=(balanced, risk(unmeasured=True))))

    assert balanced.stance is Stance.NEUTRAL
    assert synthesis.deliberation is not None
    assert "1 committee(s) took a position and 1 abstained" in (
        synthesis.deliberation.because
    )
