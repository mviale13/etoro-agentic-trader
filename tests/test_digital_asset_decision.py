"""One Artificial-CIO answer for a digital asset, and one only.

DV3. The measured defect: the crypto dossier held the platform's
best-grounded evidence and no decision sentence, while the legacy
executive surface still answered *INVESTIGATE, conviction 46* for BTC
from provider-fed signals the crypto rulings retired. One asset, two
live product answers, and the weaker surface was the only one that told
the investor anything.

Pinned here:

1. **The rule is posture arithmetic.** `digital-asset-gates@1` never
   reads a verdict's meaning, a committee's key or a number — a
   committee this rule has never heard of, with verdicts it cannot
   pronounce, travels the same path (#114's three-verdict lesson).
2. **Some committees answering is not a recommendation.** The reachable
   states are MONITOR and INVESTIGATE; PREPARE/RECOMMEND/REJECT cannot
   be produced, and a conviction can never be attached.
3. **Evidence discipline survives the crossing.** NOT_APPLICABLE stays
   distinct from unknown and is never adverse; an insufficiency keeps
   its owner's own sentence; a silence stays named.
4. **The legacy surface is retired**, not redirected: the executive
   dossier answers 410 for every asset in the crypto corpus, before the
   pipeline spends anything.
"""

from __future__ import annotations

import pytest

from app.cio.decision_state import DecisionState
from app.cio.digital_asset_decision import (
    DigitalAssetDecision,
    decide_digital_asset,
)
from app.domain.committee_judgment import Applicability, Confidence
from app.domain.committee_protocol import CommitteeIdentity, Comparability
from app.domain.investment_consideration import (
    BRIDGE_POLICY_VERSION,
    AssetConsiderations,
    InvestmentConsideration,
    InvestmentEffect,
)
from app.domain.investor_assessment import (
    InvestorAssessment,
    InvestorStatement,
    StatementShape,
)
from app.domain.judgment_history import JudgmentPosture

# ── fixtures: a committee this rule has never heard of ──────────────


def identity(
    key: str = "weather",
    name: str = "Weather Committee",
) -> CommitteeIdentity:
    return CommitteeIdentity(key=key, name=name, version=1, fingerprint="f" * 16)


def consideration(
    posture: JudgmentPosture,
    key: str = "weather",
    name: str = "Weather Committee",
    verdict: str | None = None,
    verdict_stated: str | None = None,
    because: str | None = None,
) -> InvestmentConsideration:
    applicability = {
        JudgmentPosture.KNOWN_NOT_APPLICABLE: Applicability.NOT_ECONOMICALLY_APPLICABLE,
        JudgmentPosture.APPLICABILITY_UNKNOWN: Applicability.UNESTABLISHED,
    }.get(posture, Applicability.APPLICABLE)

    return InvestmentConsideration(
        asset="TEST",
        committee=identity(key, name),
        question="What is the weather doing?",
        posture=posture,
        applicability=applicability,
        conclusion=verdict,
        conclusion_stated=verdict_stated,
        because=because,
        confidence=Confidence.SINGLE_OBSERVATION if posture.is_answered else None,
        effect=InvestmentEffect.UNRESOLVED,
        policy_version=BRIDGE_POLICY_VERSION,
        judgment_id="jid-1",
        comparability=Comparability.COMPARABLE,
    )


def considerations(*items: InvestmentConsideration) -> AssetConsiderations:
    return AssetConsiderations(asset="TEST", considerations=items)


EMPTY_ASSESSMENT = InvestorAssessment(asset="TEST")


def decide(*items: InvestmentConsideration) -> DigitalAssetDecision:
    return decide_digital_asset(considerations(*items), EMPTY_ASSESSMENT)


# ── 1. the reachable states, and only those ─────────────────────────

ALL_POSTURES = tuple(JudgmentPosture)


@pytest.mark.parametrize("first", ALL_POSTURES)
@pytest.mark.parametrize("second", ALL_POSTURES)
def test_every_posture_pair_reaches_monitor_or_investigate(
    first: JudgmentPosture,
    second: JudgmentPosture,
) -> None:
    """The whole input space of a two-committee corpus, exhaustively.

    Twenty-five cells, and none of them may reach an actionable state:
    knowing something structural about an asset is not permission to
    recommend it.
    """

    decision = decide(
        consideration(first, key="a", name="Committee A"),
        consideration(second, key="b", name="Committee B"),
    )

    assert decision.state in (DecisionState.MONITOR, DecisionState.INVESTIGATE)
    assert decision.conviction is None
    assert decision.rationale


def test_an_answer_makes_the_case_investigable() -> None:
    decision = decide(
        consideration(
            JudgmentPosture.ANSWERED,
            verdict="raining",
            verdict_stated="it is raining, structurally",
        )
    )

    assert decision.state is DecisionState.INVESTIGATE
    assert any("raining, structurally" in line for line in decision.established)


def test_a_named_evidence_gap_is_also_investigable() -> None:
    """The question applies and the committee names what is missing."""

    decision = decide(
        consideration(
            JudgmentPosture.EVIDENCE_INSUFFICIENT,
            because="No barometer reading is held for this asset.",
        )
    )

    assert decision.state is DecisionState.INVESTIGATE
    assert decision.established == ()
    assert [q.stated for q in decision.unresolved] == [
        "No barometer reading is held for this asset."
    ]


def test_an_unestablished_role_cannot_be_investigated() -> None:
    """TAO's shape: this platform cannot say which questions apply."""

    decision = decide(
        consideration(JudgmentPosture.APPLICABILITY_UNKNOWN, key="a", name="A"),
        consideration(JudgmentPosture.APPLICABILITY_UNKNOWN, key="b", name="B"),
    )

    assert decision.state is DecisionState.MONITOR
    assert "economic role" in decision.rationale


def test_every_question_wrong_instrument_is_watched_not_researched() -> None:
    decision = decide(
        consideration(JudgmentPosture.KNOWN_NOT_APPLICABLE, because="wrong tool")
    )

    assert decision.state is DecisionState.MONITOR
    assert "wrong instrument" in decision.rationale


def test_no_judgments_at_all_is_monitor_with_the_advance_named() -> None:
    decision = decide_digital_asset(
        AssetConsiderations(asset="TEST", silent=("Committee A",)),
        EMPTY_ASSESSMENT,
    )

    assert decision.state is DecisionState.MONITOR
    assert decision.silent_committees == ("Committee A",)


# ── 2. no verdict meaning, no number ────────────────────────────────


def test_the_state_is_blind_to_which_verdict_was_answered() -> None:
    """A negative-sounding verdict is not a negative grade.

    The same posture with opposite-sounding verdicts must reach the
    same state — the rule may know THAT a committee answered, never
    what the answer means.
    """

    evidenced = decide(
        consideration(JudgmentPosture.ANSWERED, verdict="mechanism_evidenced")
    )
    negated = decide(
        consideration(JudgmentPosture.ANSWERED, verdict="no_mechanism_evidenced")
    )

    assert evidenced.state is negated.state
    assert evidenced.rationale == negated.rationale


def test_conviction_is_a_property_and_always_none() -> None:
    """Structurally unfillable: there is no field to set."""

    decision = decide(consideration(JudgmentPosture.ANSWERED, verdict="x"))

    assert decision.conviction is None
    assert decision.conviction_withheld_because

    # Frozen + slots raises TypeError on a property, plain frozen an
    # AttributeError; either way the write is impossible.
    with pytest.raises((AttributeError, TypeError)):
        decision.conviction = 46  # type: ignore[misc, assignment]


def test_the_rule_module_knows_no_committee_and_no_verdict() -> None:
    """#114's fence, applied to the decider: no key, no token, no family.

    The source must not name a committee, a verdict token, or any of
    the evidence families the import guards fence away from this
    package.
    """

    import pathlib

    import app.cio.digital_asset_decision as module

    text = pathlib.Path(module.__file__).read_text(encoding="utf-8")

    for forbidden in (
        "fee_capture",
        "supply_governance",
        "value_capture",
        "mechanism_evidenced",
        "consensus_bound",
        "governance_set",
    ):
        assert forbidden not in text.lower(), forbidden


# ── 3. evidence discipline survives ─────────────────────────────────


def test_not_applicable_is_never_adverse_and_never_unresolved() -> None:
    decision = decide(
        consideration(
            JudgmentPosture.ANSWERED,
            key="a",
            name="A",
            verdict="x",
            verdict_stated="answered",
        ),
        consideration(
            JudgmentPosture.KNOWN_NOT_APPLICABLE,
            key="b",
            name="B",
            because="This question is the wrong instrument here.",
        ),
    )

    assert decision.adverse == ()
    assert decision.not_applicable == (
        "B: This question is the wrong instrument here.",
    )
    assert all("B" != q.owner for q in decision.unresolved)


def test_an_uncertain_statement_stays_an_uncertainty() -> None:
    """ARB's 81% circulating-supply spread: material, never adverse."""

    assessment = InvestorAssessment(
        asset="TEST",
        statements=(
            InvestorStatement(
                subject="Circulating supply",
                shape=StatementShape.UNCERTAIN,
                stated="Circulating supply cannot be stated as a single figure.",
            ),
        ),
    )

    decision = decide_digital_asset(
        considerations(consideration(JudgmentPosture.ANSWERED, verdict="x")),
        assessment,
    )

    assert decision.material_uncertainties == (
        "Circulating supply cannot be stated as a single figure.",
    )
    assert decision.adverse == ()


def test_a_committee_quoting_statement_is_not_carried_twice() -> None:
    """#126's rule: one fact, one owner — `from_committee` routes it."""

    assessment = InvestorAssessment(
        asset="TEST",
        statements=(
            InvestorStatement(
                subject="Weather",
                shape=StatementShape.INSUFFICIENT,
                stated="Too little to answer this question.",
                from_committee="weather",
            ),
        ),
    )

    decision = decide_digital_asset(
        considerations(
            consideration(
                JudgmentPosture.EVIDENCE_INSUFFICIENT,
                because="No barometer reading is held.",
            )
        ),
        assessment,
    )

    owners = [q.owner for q in decision.unresolved]

    assert owners == ["Weather Committee"]


def test_a_silence_is_named_in_the_platforms_own_words() -> None:
    assessment = InvestorAssessment(asset="TEST", silent_about=("Maximum supply",))

    decision = decide_digital_asset(
        considerations(consideration(JudgmentPosture.ANSWERED, verdict="x")),
        assessment,
    )

    assert any(q.owner == "Maximum supply" for q in decision.unresolved)


def test_the_ceiling_and_the_withheld_conviction_are_worded() -> None:
    """Abstention is a sentence, not silence (Invariant 10)."""

    decision = decide(consideration(JudgmentPosture.ANSWERED, verdict="x"))

    payload = decision.as_dict()

    # No `conviction` key at all — the crypto payload guard forbids the
    # key everywhere, and a field that exists as null invites a number.
    assert "conviction" not in payload
    assert payload["conviction_withheld_because"]
    assert "INVESTIGATE" in payload["ceiling"]
    assert "limit of this platform" in payload["ceiling"]
    assert payload["adverse_absent"]
    assert payload["decided_under"] == [{"key": "digital-asset-gates", "version": 1}]
