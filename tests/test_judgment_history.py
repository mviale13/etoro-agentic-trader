"""Judgment history: what changed, what did not, and what may be said now.

Ten acceptance demonstrations, and the experiment at the centre of them
is §4 — **evidence change and judgment change are separate facts**. All
four of its cases are demonstrated here against controlled records,
because the failure this slice exists to prevent is not a crash: it is a
true sentence about a moved number presented as a moved conclusion.

No test asserts that any asset is worth owning, that a transition is
welcome, or that a verdict is a grade. Where a verdict appears it is
asserted from the record shape that produced it.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
)
from app.domain.committee_protocol import (
    CommitteeContract,
    Comparability,
    fingerprint_of,
)
from app.domain.crypto_intelligence import ClaimType
from app.domain.judgment_history import (
    EvidenceMovement,
    JudgmentChange,
    JudgmentPosture,
    JudgmentRecord,
    JudgmentTransition,
    StandingKind,
    SupportChange,
    compare,
    coverage,
    posture_of,
    record_from,
    standing,
    transitions,
)
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.value_capture_committee import (
    APPLICABILITY_RULE,
    CONTRACT,
    ValueCaptureCommittee,
    Verdict,
)

#: The live contract's identity, as a record carries it.
VERSION = CONTRACT.identity

NOW = datetime(2026, 8, 10, tzinfo=UTC)

#: A second committee contract, as a genuine redefinition would produce
#: it: a different applicability rule and a verdict vocabulary that
#: gained a member, so the same word no longer means the same thing.
#:
#: A real contract rather than a stub identity, because the fingerprint
#: is *derived* — asserting incomparability against a hand-written
#: digest would prove the test could type, not that the derivation
#: notices.
CONTRACT_V2 = CommitteeContract(
    key=CONTRACT.key,
    name=CONTRACT.name,
    question=CONTRACT.question,
    version=2,
    applicability_rule="something-else@2",
    verdicts=(*CONTRACT.verdicts, "mechanism_partially_evidenced"),
    eligible_claim_types=CONTRACT.eligible_claim_types,
)

V2 = CONTRACT_V2.identity


# ── builders ────────────────────────────────────────────────────────


def _finding(ref: str, stated: str) -> EligibleFinding:
    return EligibleFinding(
        ref=ref,
        stated=stated,
        claim_type=ClaimType.REPORTED,
        established_by="test fixture",
    )


def _judgment(
    *,
    asset: str = "HYPE",
    at: datetime = NOW,
    applicability: Applicability = Applicability.APPLICABLE,
    state: JudgmentState = JudgmentState.JUDGED,
    verdict: Verdict | None = Verdict.MECHANISM_EVIDENCED,
    confidence: Confidence | None = Confidence.SINGLE_OBSERVATION,
    refs: tuple[str, ...] = ("F.venue",),
    contract: CommitteeContract = CONTRACT,
    abstained: AbstentionReason | None = None,
    unavailable: str | None = None,
    role: str | None = "Exchange venue",
) -> CommitteeJudgment:
    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=state,
        basis=ApplicabilityBasis(
            applicability=applicability,
            because="test fixture",
            economic_role=role,
        ),
        verdict=verdict,
        confidence=confidence,
        refs=refs,
        abstained_because=abstained,
        unavailable_because=unavailable,
        judged_at=at,
    )


def _record(
    *,
    at: datetime = NOW,
    evidence: tuple[EligibleFinding, ...] = (),
    **kwargs: object,
) -> JudgmentRecord:
    return record_from(
        _judgment(at=at, **kwargs),  # type: ignore[arg-type]
        evidence,
        recorded_at=at,
    )


def _service(tmp_path) -> JudgmentHistoryService:  # type: ignore[no-untyped-def]
    return JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))


# ── 1. the first judgment ───────────────────────────────────────────


def test_a_first_judgment_is_first_and_compares_with_nothing() -> None:
    """§Acceptance 1. Nothing precedes it, and nothing is implied.

    The support and evidence axes are `NOT_COMPARABLE` rather than
    "unchanged": there is no previous judgment for them to be unchanged
    *from*, and a first reading that claimed stability would be the
    smallest possible version of this layer's central error.
    """

    transition = compare(_record())

    assert transition.change is JudgmentChange.FIRST_JUDGMENT
    assert transition.support is SupportChange.NOT_COMPARABLE
    assert transition.evidence is EvidenceMovement.NOT_COMPARABLE
    assert transition.previous is None
    assert transition.is_grounded


# ── 2. §4 case A: evidence moved, judgment did not ──────────────────


def test_moved_evidence_under_a_steady_verdict_is_not_a_changed_conclusion() -> None:
    """§4 A, and the sentence this whole slice exists to refuse.

    Fees are a different number every day. If a moved figure produced a
    changed conclusion, this platform would announce a reversal roughly
    daily while the committee had not moved at all.
    """

    monday = _record(
        at=NOW,
        evidence=(_finding("F.venue", "Hyperliquid: users paid $842k in fees."),),
    )

    tuesday = _record(
        at=NOW + timedelta(days=1),
        evidence=(_finding("F.venue", "Hyperliquid: users paid $1m in fees."),),
    )

    transition = compare(tuesday, monday)

    assert transition.evidence is EvidenceMovement.CHANGED
    assert transition.change is JudgmentChange.VERDICT_UNCHANGED
    assert not transition.change.is_verdict_movement

    # And the wording says so out loud rather than leaving a reader to
    # infer it from two enum values.
    assert "the committee's answer did not" in transition.stated
    assert "not a change in what the committee concluded" in transition.stated


# ── 3. §4 case B: evidence moved and so did the judgment ────────────


def test_a_verdict_transition_is_reported_as_exactly_that_transition() -> None:
    """§4 B and §7. The transition means itself and nothing more."""

    before = _record(
        verdict=Verdict.NO_MECHANISM_EVIDENCED,
        evidence=(_finding("N.venue", "No holder-revenue figure is published."),),
    )

    after = _record(
        at=NOW + timedelta(days=7),
        verdict=Verdict.MECHANISM_EVIDENCED,
        evidence=(_finding("H.venue", "$535k reached token holders."),),
    )

    transition = compare(after, before)

    assert transition.change is JudgmentChange.VERDICT_CHANGED
    assert transition.evidence is EvidenceMovement.CHANGED
    assert transition.change.is_verdict_movement

    # The answer in the committee's own words, quoted rather than read:
    # the framework says "the committee answered" and the committee
    # finishes the sentence.
    assert JudgmentPosture.ANSWERED.stated in transition.stated
    assert Verdict.MECHANISM_EVIDENCED.stated in transition.stated
    assert JudgmentChange.VERDICT_CHANGED.stated in transition.stated


# ── 4. §4 case D: same verdict, different support ───────────────────


def test_more_observation_behind_an_unchanged_verdict_is_not_a_firmer_view() -> None:
    """§4 D. Support is a count, and it moves on its own axis.

    Confidence is established by code counting observations and the
    verdict is chosen by the judge; neither sees the other. So support
    moving under a fixed verdict is arithmetic about evidence, and the
    wording is required to say observations rather than certainty.
    """

    thin = _record(confidence=Confidence.SINGLE_OBSERVATION)

    thick = _record(
        at=NOW + timedelta(days=3),
        confidence=Confidence.MULTIPLE_OBSERVATIONS,
    )

    transition = compare(thick, thin)

    assert transition.change is JudgmentChange.VERDICT_UNCHANGED
    assert transition.support is SupportChange.INCREASED
    assert "independent observations" in transition.support.stated

    # The reverse direction is available and equally plain.
    assert compare(thin, thick).support is SupportChange.DECREASED


def test_support_is_not_compared_across_a_judgment_with_no_verdict() -> None:
    """Confidence without a verdict is meaningless, so it is not compared."""

    judged = _record()

    abstained = _record(
        at=NOW + timedelta(days=1),
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
    )

    assert compare(abstained, judged).support is SupportChange.NOT_COMPARABLE


# ── 5. §4 case C + §5: a previous verdict is never carried forward ──


def test_a_previous_verdict_is_history_and_never_todays_answer(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """§4 C, §Acceptance 5, and the ruling's own worked example.

    The dangerous sentence is *"the mechanism remains evidenced"*. It is
    dangerous because it is almost true — the committee did conclude
    that — and because nothing in today's evidence supports the present
    tense.
    """

    service = _service(tmp_path)

    judged = _record(
        evidence=(_finding("H.venue", "$535k reached token holders."),),
    )

    service.record(_judgment(), (), now=NOW)

    today = _record(
        at=NOW + timedelta(days=5),
        state=JudgmentState.UNAVAILABLE,
        verdict=None,
        confidence=None,
        unavailable="The judging model could not be reached.",
        evidence=(),
    )

    where = standing(today, [judged])

    assert where.kind is StandingKind.PREVIOUS_NOT_REFRESHED

    # The structural half: there is no way to read the old verdict as
    # current, because the property that offers a current verdict
    # returns nothing.
    assert where.verdict is None
    assert where.previously is not None
    assert where.previously.verdict == Verdict.MECHANISM_EVIDENCED

    # The worded half.
    assert "the previous judgment" in where.stated
    assert "is not restated as a current finding" in where.stated
    assert "remains evidenced" not in where.stated

    # And the transition is an unrefreshed answer, never a reversal.
    transition = compare(today, judged)

    assert transition.change is JudgmentChange.BECAME_UNANSWERABLE
    assert "rather than contradicted" in transition.change.stated
    assert transition.evidence is EvidenceMovement.WITHDRAWN


# ── 6. the five states that must never collapse ─────────────────────


def test_known_not_applicable_stays_distinct_from_applicability_unknown() -> None:
    """§2 and §Acceptance 6. The owner's PR #112 catch, carried into history.

    BTC and TAO both produce no verdict and their problems are
    opposite: one question is the wrong instrument, and the other
    cannot be established as applicable at all. A history storing *"no
    verdict"* would make them the same asset.
    """

    bitcoin = _record(
        asset="BTC",
        applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
        role="Monetary network",
    )

    bittensor = _record(
        asset="TAO",
        applicability=Applicability.UNESTABLISHED,
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.APPLICABILITY_UNESTABLISHED,
        role=None,
    )

    assert bitcoin.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE
    assert bittensor.posture is JudgmentPosture.APPLICABILITY_UNKNOWN
    assert bitcoin.posture.stated != bittensor.posture.stated

    # Neither is an answer, and neither is adverse.
    assert not bitcoin.posture.is_answered
    assert not bittensor.posture.is_answered


def test_every_combination_of_applicability_and_state_has_its_own_posture() -> None:
    """§2 made total. Six states, and nothing falls through to a default."""

    seen = {
        posture_of(applicability, state, verdict)
        for applicability in Applicability
        for state in JudgmentState
        for verdict in (None, *Verdict)
    }

    assert seen == set(JudgmentPosture)


def test_an_unestablished_applicability_becoming_established_is_its_own_fact() -> None:
    """§3. Learning what an asset is, is not the committee changing its mind."""

    before = _record(
        asset="TAO",
        applicability=Applicability.UNESTABLISHED,
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.APPLICABILITY_UNESTABLISHED,
        role=None,
    )

    after = _record(
        asset="TAO",
        at=NOW + timedelta(days=14),
        applicability=Applicability.APPLICABLE,
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
        role="Compute network",
    )

    transition = compare(after, before)

    assert transition.change is JudgmentChange.APPLICABILITY_ESTABLISHED


def test_a_changed_applicability_names_the_understanding_that_moved() -> None:
    """§3's last clause: attributed to a changed role, or stated as unexplained."""

    before = _record(applicability=Applicability.APPLICABLE, role="Exchange venue")

    after = _record(
        at=NOW + timedelta(days=30),
        applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
        role="Monetary network",
    )

    transition = compare(after, before)

    assert transition.change is JudgmentChange.APPLICABILITY_CHANGED
    assert "economic role changed from Exchange venue to Monetary network" in (
        transition.stated
    )

    # And where the role did *not* move, the platform says it cannot
    # account for the difference rather than implying a reason.
    unexplained = compare(
        _record(
            at=NOW + timedelta(days=30),
            applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
            state=JudgmentState.ABSTAINED,
            verdict=None,
            confidence=None,
            abstained=AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
            role="Exchange venue",
        ),
        before,
    )

    assert "cannot account for the difference" in unexplained.stated


# ── 7. committee version is part of identity ────────────────────────


def test_two_committee_contracts_are_not_compared_as_though_identical() -> None:
    """§6 and §Acceptance 7. Incomparability short-circuits everything.

    The other two axes are not computed and hedged — they are set to
    `NOT_COMPARABLE`, because a verdict transition across a
    redefinition is arithmetic over two different questions.
    """

    old = _record(verdict=Verdict.NO_MECHANISM_EVIDENCED, contract=CONTRACT)

    new = _record(
        at=NOW + timedelta(days=20),
        verdict=Verdict.MECHANISM_EVIDENCED,
        contract=CONTRACT_V2,
    )

    transition = compare(new, old)

    assert transition.change is JudgmentChange.INCOMPARABLE_VERSION
    assert transition.comparability is Comparability.DIFFERENT_VERSION
    assert transition.support is SupportChange.NOT_COMPARABLE
    assert transition.evidence is EvidenceMovement.NOT_COMPARABLE

    # Two different verdicts, and the surface must not call it a change
    # of view.
    assert "not compared" in transition.stated
    assert JudgmentChange.VERDICT_CHANGED.stated not in transition.stated


def test_a_contract_that_changed_without_a_version_bump_is_caught() -> None:
    """The failure nobody declares, and the reason the fingerprint exists."""

    silent = CommitteeContract(
        key=CONTRACT.key,
        name=CONTRACT.name,
        # Same declared version, different question: nobody bumped the
        # number, and the derived fingerprint is what notices.
        question=CONTRACT.question + " And is it large enough to matter?",
        version=CONTRACT.version,
        applicability_rule=CONTRACT.applicability_rule,
        verdicts=CONTRACT.verdicts,
        eligible_claim_types=CONTRACT.eligible_claim_types,
    )

    transition = compare(_record(contract=silent), _record(contract=CONTRACT))

    assert transition.comparability is Comparability.CONTRACT_CHANGED
    assert "without its version changing" in transition.comparability.stated


def test_the_live_fingerprint_is_derived_from_the_contract_it_describes() -> None:
    """A version that could drift from its own meaning would guarantee nothing."""

    assert VERSION.fingerprint == fingerprint_of(
        question=CONTRACT.question,
        applicability_rule=APPLICABILITY_RULE,
        eligible=CONTRACT.eligible_claim_types,
        verdicts=CONTRACT.verdicts,
    )

    # Change any one of the four and the fingerprint changes.
    for altered in (
        fingerprint_of(
            "a different question",
            APPLICABILITY_RULE,
            CONTRACT.eligible_claim_types,
            CONTRACT.verdicts,
        ),
        fingerprint_of(
            CONTRACT.question,
            "another-rule@1",
            CONTRACT.eligible_claim_types,
            CONTRACT.verdicts,
        ),
        fingerprint_of(
            CONTRACT.question,
            APPLICABILITY_RULE,
            frozenset({"measured"}),
            CONTRACT.verdicts,
        ),
        fingerprint_of(
            CONTRACT.question,
            APPLICABILITY_RULE,
            CONTRACT.eligible_claim_types,
            ("mechanism_evidenced",),
        ),
    ):
        assert altered != VERSION.fingerprint


def test_an_earlier_verdict_under_an_incomparable_contract_is_not_the_standing() -> (
    None
):
    """§5 and §6 together: nobody can say what that verdict would mean now."""

    old = _record(contract=CONTRACT_V2, verdict=Verdict.MECHANISM_EVIDENCED)

    today = _record(
        at=NOW + timedelta(days=1),
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
    )

    where = standing(today, [old])

    assert where.kind is StandingKind.NONE
    assert where.previously is None


# ── 8. the record is the only evidence that the view was held ───────


def test_deleting_the_record_removes_the_ability_to_claim_the_earlier_view(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """§Acceptance 8. Nothing reconstructs a judgment from evidence.

    Running the committee again produces *today's* judgment from
    today's evidence, which is a different fact. So the record is not a
    cache of a derivable thing — it is the whole of the claim, and
    losing it must lose the claim rather than silently regenerate one.
    """

    service = _service(tmp_path)

    assert (
        service.record(_judgment(verdict=Verdict.MECHANISM_EVIDENCED), (), now=NOW)
        is not None
    )
    assert service.history("HYPE", CONTRACT.key)

    today = _record(
        at=NOW + timedelta(days=2),
        state=JudgmentState.ABSTAINED,
        verdict=None,
        confidence=None,
        abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
    )

    assert service.standing(today).kind is StandingKind.PREVIOUS_NOT_REFRESHED

    JudgmentHistoryStore(root=tmp_path).path_for("HYPE").unlink()

    assert service.history("HYPE", CONTRACT.key) == []
    assert service.standing(today).kind is StandingKind.NONE
    assert service.standing(today).previously is None
    assert "no recorded judgment" not in service.standing(today).stated

    assert service.coverage("HYPE", CONTRACT.key).span is None
    assert "recorded no judgment" in service.coverage("HYPE", CONTRACT.key).stated


def test_the_store_appends_and_never_rewrites(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Append-only is structural: the file only ever grows."""

    store = JudgmentHistoryStore(root=tmp_path)

    first = _record(verdict=Verdict.NO_MECHANISM_EVIDENCED)
    second = _record(at=NOW + timedelta(days=1), verdict=Verdict.MECHANISM_EVIDENCED)

    assert store.append(first)
    assert store.append(second)

    # The same judgment replayed is not a second event.
    assert not store.append(first)

    held = store.records("HYPE")

    assert [record.verdict for record in held] == [
        Verdict.NO_MECHANISM_EVIDENCED,
        Verdict.MECHANISM_EVIDENCED,
    ]

    # Every field the ruling requires survives the round trip.
    assert held[0].applicability is Applicability.APPLICABLE
    assert held[0].committee.fingerprint == VERSION.fingerprint
    assert held[0].economic_role == "Exchange venue"
    assert held[0].refs == ("F.venue",)


def test_a_judgment_with_no_stated_applicability_is_refused() -> None:
    """Not knowing whether a question applies is a state, not a silence."""

    with pytest.raises(ValueError, match="applicability"):
        record_from(
            CommitteeJudgment(
                asset="HYPE",
                contract=CONTRACT,
                state=JudgmentState.UNAVAILABLE,
                unavailable_because="off",
            ),
            (),
            recorded_at=NOW,
        )


# ── 9. synthesis explains a transition it could not have discovered ─


def test_the_synthesist_may_cite_a_transition_code_established() -> None:
    """§8 and §Acceptance 9. The model explains; it does not discover."""

    from app.renderers.intelligence_synthesist import (
        SynthesisRejected,
        build_findings,
        synthesis_from_payload,
    )
    from tests.test_intelligence_synthesis import _snapshot

    transition = compare(
        _record(at=NOW + timedelta(days=7), verdict=Verdict.MECHANISM_EVIDENCED),
        _record(verdict=Verdict.NO_MECHANISM_EVIDENCED),
    )

    snapshot = _snapshot()

    findings = build_findings(snapshot, (), (transition,))

    supplied = [finding for finding in findings if finding.id.startswith("J")]

    assert len(supplied) == 1
    assert transition.record_ids[0] in supplied[0].source

    payload = {
        "what_matters": [
            {
                "stated": (
                    "The committee now finds an evidenced mechanism where the "
                    "previous comparable judgment found none."
                ),
                "theme": "committee judgment",
                "refs": ["J1"],
            }
        ],
        "why_it_matters": [
            {
                "stated": "That transition is a change in the committee's answer.",
                "theme": "what it means",
                "refs": ["J1"],
            }
        ],
        "watch_next": [
            {
                "stated": (
                    "Whether the next comparable judgment reaches the same answer."
                ),
                "theme": "next judgment",
                "refs": ["J1"],
            }
        ],
    }

    what, _, _ = synthesis_from_payload(
        payload, findings=findings, causal_allowed=False
    )

    assert what[0].refs == ("J1",)

    # And with no transition established, the same sentence has nothing
    # to cite — the model cannot be the thing that noticed.
    bare = build_findings(snapshot, (), ())

    assert not [finding for finding in bare if finding.id.startswith("J")]

    with pytest.raises(SynthesisRejected, match="not supplied"):
        synthesis_from_payload(payload, findings=bare, causal_allowed=False)


# ── 10. no transition may inflate into a view about the asset ───────

#: Vocabulary that would take a transition beyond what it says. §7's
#: list, plus the neighbouring words a reader would take as a verdict.
INFLATION = (
    "buy",
    "sell",
    "recommend",
    "recommendation",
    "overweight",
    "underweight",
    "allocate",
    "allocation",
    "portfolio",
    "conviction",
    "thesis",
    "bullish",
    "bearish",
    "improve",
    "improved",
    "improvement",
    "deteriorated",
    "strengthen",
    "strengthened",
    "weakened",
    "upgrade",
    "downgrade",
    "outperform",
    "underperform",
    "sentiment",
    "momentum",
    "attractive",
    "unattractive",
    "undervalued",
    "overvalued",
    "opportunity",
    "quality",
    "score",
    "rating",
    "favourable",
    "favorable",
    "adverse",
    "fundamentals",
)


def _every_sentence() -> list[str]:
    """Every sentence this layer can produce, from every state it has."""

    spoken = [member.stated for member in JudgmentChange]
    spoken += [member.stated for member in SupportChange]
    spoken += [member.stated for member in EvidenceMovement]
    spoken += [member.stated for member in Comparability]
    spoken += [member.stated for member in JudgmentPosture]

    postures = [
        _record(
            applicability=applicability,
            state=state,
            verdict=verdict,
            confidence=confidence,
            role=role,
        )
        for applicability in Applicability
        for state in JudgmentState
        for verdict in (None, *Verdict)
        for confidence in (None, *Confidence)
        for role in (None, "Exchange venue", "Monetary network")
    ]

    for current in postures:
        spoken.append(current.stated)
        spoken.append(compare(current).stated)
        spoken.append(standing(current, []).stated)

        for previous in postures[:12]:
            spoken.append(compare(current, previous).stated)
            spoken.append(standing(current, [previous]).stated)

        spoken.append(compare(current, _record(contract=CONTRACT_V2)).stated)

    spoken.append(coverage("HYPE", CONTRACT.key, []).stated)
    spoken.append(coverage("HYPE", CONTRACT.key, [postures[0]]).stated)
    spoken.append(coverage("HYPE", CONTRACT.key, postures[:5]).stated)

    return spoken


def test_no_transition_can_produce_a_recommendation_or_a_view() -> None:
    """§7 and §Acceptance 10, checked over every sentence, not a sample.

    The wording of this layer is built only from its own enumerations,
    which is what makes the vocabulary finite — and finite is what makes
    this test possible rather than reassuring.
    """

    import re

    for sentence in _every_sentence():
        lowered = sentence.lower()

        for word in INFLATION:
            assert not re.search(rf"\b{word}\b", lowered), (
                f"{word!r} appears in a judgment-history statement: {sentence!r}"
            )


def test_the_transition_schema_has_no_room_for_a_recommendation() -> None:
    """The structural half of §7: the fence is the schema, not the prose."""

    fields = set(JudgmentTransition.__dataclass_fields__)

    assert fields == {
        "asset",
        "committee",
        "comparability",
        "change",
        "support",
        "evidence",
        "current",
        "previous",
        "record_ids",
    }

    forbidden = {
        "recommendation",
        "action",
        "conviction",
        "score",
        "rating",
        "stance",
        "sentiment",
        "thesis",
        "weight",
        "signal",
    }

    assert not fields & forbidden
    assert not set(JudgmentRecord.__dataclass_fields__) & forbidden

    # And no field carries the *synthesist's* prose. §1: a model's
    # reading of a judgment is communication, and persisting it would
    # make last week's wording into this week's history.
    assert "synthesis" not in JudgmentRecord.__dataclass_fields__
    assert "narrative" not in JudgmentRecord.__dataclass_fields__

    # `because` is a different thing and is deliberately kept: it is the
    # committee's own account of its own outcome, produced with the
    # answer and part of it. The assessment matrix forced it — two
    # assets abstaining under one committee for genuinely different
    # reasons were indistinguishable from the record, because the
    # abstention enum is three members wide and the difference lives in
    # the sentence.
    assert "because" in JudgmentRecord.__dataclass_fields__


# ── the committee actually carries what history needs ───────────────


def test_the_live_committee_states_applicability_on_every_outcome() -> None:
    """A judgment that forgot its applicability could not be recorded at all.

    Run against the real committee for the two assets whose outcomes
    need no model: one where the question is the wrong instrument, and
    one where applicability cannot be established.
    """

    committee = ValueCaptureCommittee()

    bitcoin = asyncio.run(committee.judge("BTC"))

    assert bitcoin.applicability is Applicability.NOT_ECONOMICALLY_APPLICABLE
    assert bitcoin.economic_role
    assert record_from(bitcoin, (), NOW).posture is (
        JudgmentPosture.KNOWN_NOT_APPLICABLE
    )

    bittensor = asyncio.run(committee.judge("TAO"))

    assert bittensor.applicability is Applicability.UNESTABLISHED
    assert bittensor.economic_role is None
    assert record_from(bittensor, (), NOW).posture is (
        JudgmentPosture.APPLICABILITY_UNKNOWN
    )


def test_the_committee_version_is_recorded_and_survives_the_round_trip(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """§1: committee identity and version travel with every judgment."""

    service = _service(tmp_path)

    committee = ValueCaptureCommittee()

    judgment = asyncio.run(committee.judge("BTC"))

    written = service.record(judgment, (), now=NOW)

    assert written is not None

    held = service.latest("BTC", CONTRACT.key)

    assert held is not None
    assert held.committee == VERSION
    assert held.applicability is Applicability.NOT_ECONOMICALLY_APPLICABLE

    # Recording the identical judgment again appends nothing.
    assert service.record(judgment, (), now=NOW) is None


# ── coverage never becomes a duration ───────────────────────────────


def test_a_count_of_judgments_is_never_a_duration_of_review() -> None:
    """The journal's hardest rule, inherited without softening."""

    sparse = [
        _record(at=NOW),
        _record(at=NOW + timedelta(days=19)),
        _record(at=NOW + timedelta(days=21)),
    ]

    stated = coverage("HYPE", CONTRACT.key, sparse).stated

    assert "3 recorded judgments" in stated
    assert "spanning 21 day(s)" in stated
    assert "longest gap between them 19 day(s)" in stated
    assert "not a duration of continuous review" in stated

    # One judgment describes a moment, and says so.
    assert "not a history" in coverage("HYPE", CONTRACT.key, sparse[:1]).stated


def test_transitions_are_ordered_and_every_one_is_checkable() -> None:
    """§3: a projection over the record, oldest first, all grounded."""

    records = [
        _record(at=NOW, verdict=Verdict.NO_MECHANISM_EVIDENCED),
        _record(at=NOW + timedelta(days=1), verdict=Verdict.MECHANISM_EVIDENCED),
        _record(at=NOW + timedelta(days=2), verdict=Verdict.MECHANISM_EVIDENCED),
    ]

    found = transitions(records)

    assert [transition.change for transition in found] == [
        JudgmentChange.FIRST_JUDGMENT,
        JudgmentChange.VERDICT_CHANGED,
        JudgmentChange.VERDICT_UNCHANGED,
    ]

    assert all(transition.is_grounded for transition in found)


def test_a_json_line_that_cannot_be_read_does_not_cost_the_record(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """One bad line must not lose the history around it."""

    store = JudgmentHistoryStore(root=tmp_path)

    store.append(_record())

    path = store.path_for("HYPE")

    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json\n")
        handle.write(json.dumps({"asset": "HYPE"}) + "\n")

    assert len(store.records("HYPE")) == 1
