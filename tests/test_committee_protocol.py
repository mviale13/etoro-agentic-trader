"""The Crypto Committee Protocol, tested against a committee that is not real.

The slice's acceptance criterion in one file: **describe a second
committee to the framework without teaching the framework what its
verdicts mean.**

The committee below ships nowhere. It is not registered, not exported
from `app`, not reachable from any surface, and it exists only to be
different from Fee Capture in every way the protocol claims not to
care about:

```text
                    Fee Capture              the fixture here
question            fee capture              custody concentration
verdicts            2                        3
applicability rule  monetary role declines   supply-visibility rule
evidence            protocol fees            holder counts
```

Three verdicts rather than two matters most. A framework that had
quietly assumed a binary — a `bool`, an `is_positive`, a pair of
postures named presence and absence — passes every Fee Capture test and
fails here. That assumption is exactly what PR #113 shipped, and this
file is where it would have been caught.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import pytest

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
    abstain,
    confidence_from,
    unavailable,
)
from app.domain.committee_protocol import (
    Committee,
    CommitteeContract,
    Comparability,
    StructuralVerdict,
    fingerprint_of,
)
from app.domain.crypto_intelligence import ClaimType
from app.domain.judgment_history import (
    EvidenceMovement,
    JudgmentChange,
    JudgmentPosture,
    JudgmentTransition,
    StandingKind,
    SupportChange,
    compare,
    record_from,
    standing,
)
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from tests.reachability import reachable

NOW = datetime(2026, 8, 11, tzinfo=UTC)


# ── a committee the framework has never heard of ────────────────────


class CustodyVerdict(StrEnum):
    """Three answers, none of which divides into presence and absence.

    Deliberately not a pair, and deliberately not orderable. `MIXED` is
    not "between" the other two — it is a third structural finding, and
    a framework that tried to rank these would have to invent an order
    nobody supplied.
    """

    CONCENTRATED = "concentrated"
    DISPERSED = "dispersed"
    MIXED = "mixed"

    @property
    def stated(self) -> str:
        return {
            CustodyVerdict.CONCENTRATED: (
                "the identified holders of record sit in few enough addresses "
                "for the distribution to be described as concentrated"
            ),
            CustodyVerdict.DISPERSED: (
                "the identified holders of record are spread across enough "
                "addresses for the distribution to be described as dispersed"
            ),
            CustodyVerdict.MIXED: (
                "the identified holders of record are concentrated at the top "
                "and dispersed below it, and neither description alone fits"
            ),
        }[self]


CUSTODY = CommitteeContract(
    key="custody_concentration",
    name="Custody Concentration Committee",
    question="How is identified custody of this token distributed?",
    version=1,
    applicability_rule="supply-visibility@1",
    verdicts=tuple(verdict.value for verdict in CustodyVerdict),
    eligible_claim_types=frozenset({ClaimType.MEASURED.value}),
)


class CustodyCommittee:
    """A committee the framework runs and does not understand.

    Implements the protocol and nothing else. Note what it does *not*
    do: it does not register itself anywhere, does not declare a
    polarity for its verdicts, and does not tell the framework which of
    its three answers a reader should prefer — because there is no
    field in which to say so.
    """

    def __init__(
        self,
        answer: CustodyVerdict | None = CustodyVerdict.MIXED,
        holders: int = 2,
        role: str | None = "Exchange venue",
    ) -> None:
        self._answer = answer
        self._holders = holders
        self._role = role

    @property
    def contract(self) -> CommitteeContract:
        return CUSTODY

    def basis(self, symbol: str) -> ApplicabilityBasis:
        if self._role is None:
            return ApplicabilityBasis(
                applicability=Applicability.UNESTABLISHED,
                because="No economic role is established for this asset.",
            )

        if self._role == "Monetary network":
            return ApplicabilityBasis(
                applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
                because=(
                    "Custody of a monetary asset is not a property of the "
                    "asset, so the question is the wrong instrument."
                ),
                economic_role=self._role,
            )

        return ApplicabilityBasis(
            applicability=Applicability.APPLICABLE,
            because="Identified custody is part of what this token is.",
            economic_role=self._role,
        )

    def evidence(self, symbol: str) -> tuple[EligibleFinding, ...]:
        return tuple(
            EligibleFinding(
                ref=f"A{index}",
                stated=f"{symbol}: address {index} holds a disclosed balance.",
                claim_type=ClaimType.MEASURED,
                established_by="Test fixture",
            )
            for index in range(1, self._holders + 1)
        )

    async def judge(self, symbol: str) -> CommitteeJudgment:
        basis = self.basis(symbol)

        if basis.applicability is Applicability.UNESTABLISHED:
            return abstain(
                symbol, CUSTODY, AbstentionReason.APPLICABILITY_UNESTABLISHED, basis
            )

        if not basis.is_applicable:
            return abstain(
                symbol, CUSTODY, AbstentionReason.NOT_ECONOMICALLY_APPLICABLE, basis
            )

        findings = self.evidence(symbol)

        # Every exit below has asked for its evidence and says so; the
        # two applicability exits above have not. A specimen that got
        # this wrong would prove the framework runs a committee, not
        # that it records one honestly.
        if not findings:
            return abstain(
                symbol,
                CUSTODY,
                AbstentionReason.INSUFFICIENT_EVIDENCE,
                basis,
                considered=findings,
            )

        if self._answer is None:
            return unavailable(
                symbol,
                CUSTODY,
                "The fixture declined.",
                basis,
                considered=findings,
            )

        return CommitteeJudgment(
            asset=symbol,
            contract=CUSTODY,
            state=JudgmentState.JUDGED,
            basis=basis,
            verdict=self._answer,
            confidence=confidence_from(supporting=len(findings), across_captures=False),
            refs=tuple(finding.ref for finding in findings),
            considered=findings,
            judged_at=NOW,
        )


def _service(tmp_path) -> JudgmentHistoryService:  # type: ignore[no-untyped-def]
    return JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))


def _record(committee: CustodyCommittee, asset: str = "XYZ", at: datetime = NOW):  # type: ignore[no-untyped-def]
    judgment = asyncio.run(committee.judge(asset))

    return record_from(judgment, recorded_at=at)


# ── the protocol is satisfied structurally ──────────────────────────


def test_a_committee_satisfies_the_protocol_without_inheriting_anything() -> None:
    """Structural typing, so no committee is forced into a base class.

    A committee is defined by what it can answer, not by what it
    inherits — and an ABC would have made the framework the place a new
    committee is registered, which is the coupling this slice removed.
    """

    assert isinstance(CustodyCommittee(), Committee)
    assert isinstance(CustodyVerdict.MIXED, StructuralVerdict)

    from app.services.value_capture_committee import ValueCaptureCommittee

    assert isinstance(ValueCaptureCommittee(), Committee)


def test_a_committee_cannot_answer_outside_its_own_vocabulary() -> None:
    """The fingerprint describes a vocabulary; the judgment must be in it.

    Otherwise the contract a record was compared under would be a
    description of something the record does not contain.
    """

    from app.services.value_capture_committee import Verdict as FeeVerdict

    with pytest.raises(ValueError, match="verdict vocabulary"):
        CommitteeJudgment(
            asset="XYZ",
            contract=CUSTODY,
            state=JudgmentState.JUDGED,
            basis=ApplicabilityBasis(Applicability.APPLICABLE, "x"),
            verdict=FeeVerdict.MECHANISM_EVIDENCED,
        )


# ── the framework runs it without understanding it ──────────────────


def test_the_whole_lifecycle_runs_for_a_committee_the_framework_never_saw(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """Judge, record, project, stand and count — with three verdicts."""

    service = _service(tmp_path)

    judgment = asyncio.run(CustodyCommittee().judge("XYZ"))

    written = service.record(judgment, now=NOW)

    assert written is not None
    assert written.committee.key == "custody_concentration"
    assert written.committee.name == "Custody Concentration Committee"
    assert written.verdict == CustodyVerdict.MIXED

    # The framework words the answer by quoting the committee.
    assert CustodyVerdict.MIXED.stated in written.stated

    held = service.latest("XYZ", CUSTODY.key)

    assert held is not None
    assert held.verdict == CustodyVerdict.MIXED
    assert held.posture is JudgmentPosture.ANSWERED

    assert service.coverage("XYZ", CUSTODY.key).span is not None


def test_no_framework_module_knows_what_any_verdict_means() -> None:
    """The important test, enforced by reading the framework's own source.

    Neither committee's answer tokens may appear anywhere in the
    framework. A module that mentioned one would be a module that could
    branch on it, and PR #113 contained exactly that line.
    """

    framework = (
        "app/domain/judgment_history.py",
        "app/domain/committee_protocol.py",
        "app/domain/committee_judgment.py",
        "app/infrastructure/evidence/judgment_history_store.py",
        "app/services/judgment_history_service.py",
    )

    tokens = (*FEE_CAPTURE.verdicts, *CUSTODY.verdicts, "custody_concentration")

    for module in framework:
        code = reachable(module)

        for token in tokens:
            assert token not in code, (module, token)

    # And the framework imports no committee at all.
    for module in framework:
        assert "value_capture_committee" not in reachable(module), module


# ── every #113 distinction survives through the generic contract ────


def test_all_ten_distinctions_survive_for_a_three_verdict_committee() -> None:
    """History loses nothing when it cannot read the verdicts.

    The ruling's list, walked end to end against a committee whose
    answers the framework has never seen. Each assertion is the same
    fact PR #113 established, reached now through the protocol.
    """

    dispersed = _record(CustodyCommittee(CustodyVerdict.DISPERSED))
    later = _record(
        CustodyCommittee(CustodyVerdict.DISPERSED), at=NOW + timedelta(days=1)
    )
    # One observation, then three: the count has to actually cross a
    # confidence boundary, and 2 → 4 does not.
    concentrated = _record(
        CustodyCommittee(CustodyVerdict.CONCENTRATED, holders=1),
        at=NOW + timedelta(days=2),
    )
    richer = _record(
        CustodyCommittee(CustodyVerdict.CONCENTRATED, holders=3),
        at=NOW + timedelta(days=3),
    )
    thin = _record(
        CustodyCommittee(CustodyVerdict.CONCENTRATED, holders=0),
        at=NOW + timedelta(days=4),
    )
    broken = _record(CustodyCommittee(None), at=NOW + timedelta(days=5))
    unknown = _record(CustodyCommittee(role=None), at=NOW + timedelta(days=6))
    monetary = _record(
        CustodyCommittee(role="Monetary network"), at=NOW + timedelta(days=7)
    )

    # 1. first judgment
    assert compare(dispersed).change is JudgmentChange.FIRST_JUDGMENT

    # 2. answer unchanged — and the evidence unchanged with it
    steady = compare(later, dispersed)
    assert steady.change is JudgmentChange.VERDICT_UNCHANGED
    assert steady.evidence is EvidenceMovement.UNCHANGED

    # 3. answer changed
    assert compare(concentrated, later).change is JudgmentChange.VERDICT_CHANGED

    # 4. observation-count movement, under an unchanged answer
    supported = compare(richer, concentrated)
    assert supported.change is JudgmentChange.VERDICT_UNCHANGED
    assert supported.support is SupportChange.INCREASED

    # 5. evidence changed / unchanged, on its own axis
    assert compare(richer, concentrated).evidence is EvidenceMovement.CHANGED

    # 6. answered → abstained (evidence ran out)
    ran_out = compare(thin, richer)
    assert ran_out.change is JudgmentChange.BECAME_UNANSWERABLE
    assert thin.posture is JudgmentPosture.EVIDENCE_INSUFFICIENT
    assert ran_out.evidence is EvidenceMovement.WITHDRAWN

    # 7. answered → unavailable, told apart from abstained
    assert broken.posture is JudgmentPosture.EXECUTION_UNAVAILABLE
    assert broken.posture is not thin.posture

    # 8. unanswered → answered
    assert compare(dispersed, thin).change is JudgmentChange.BECAME_ANSWERABLE

    # 9. applicability changes, and the two non-applicable states differ
    assert unknown.posture is JudgmentPosture.APPLICABILITY_UNKNOWN
    assert monetary.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE
    assert compare(unknown, dispersed).change is JudgmentChange.APPLICABILITY_CHANGED
    assert compare(monetary, unknown).change is JudgmentChange.APPLICABILITY_ESTABLISHED

    # 10. economic-role change is named where it explains applicability
    assert "Exchange venue to Monetary network" in compare(monetary, dispersed).stated


def test_an_incompatible_revision_of_an_unknown_committee_is_not_compared() -> None:
    """Contract identity works without the framework knowing the contract."""

    revised = CommitteeContract(
        key=CUSTODY.key,
        name=CUSTODY.name,
        question=CUSTODY.question,
        version=2,
        applicability_rule="supply-visibility@2",
        verdicts=CUSTODY.verdicts,
        eligible_claim_types=CUSTODY.eligible_claim_types,
    )

    assert revised.fingerprint != CUSTODY.fingerprint

    before = _record(CustodyCommittee(CustodyVerdict.DISPERSED))

    after = record_from(
        CommitteeJudgment(
            asset="XYZ",
            contract=revised,
            state=JudgmentState.JUDGED,
            basis=ApplicabilityBasis(Applicability.APPLICABLE, "x", "Exchange venue"),
            verdict=CustodyVerdict.CONCENTRATED,
            confidence=Confidence.SINGLE_OBSERVATION,
            refs=("A1",),
            judged_at=NOW + timedelta(days=1),
        ),
        recorded_at=NOW + timedelta(days=1),
    )

    transition = compare(after, before)

    assert transition.change is JudgmentChange.INCOMPARABLE_VERSION
    assert transition.comparability is Comparability.DIFFERENT_VERSION
    assert transition.support is SupportChange.NOT_COMPARABLE
    assert transition.evidence is EvidenceMovement.NOT_COMPARABLE


def test_a_previous_verdict_of_an_unknown_committee_is_still_never_current() -> None:
    """§5 holds for a committee whose answers mean nothing here."""

    answered = _record(CustodyCommittee(CustodyVerdict.CONCENTRATED))
    broken = _record(CustodyCommittee(None), at=NOW + timedelta(days=1))

    where = standing(broken, [answered])

    assert where.kind is StandingKind.PREVIOUS_NOT_REFRESHED
    assert where.verdict is None
    assert where.previously is not None
    assert where.previously.verdict == CustodyVerdict.CONCENTRATED

    # Worded by quoting the committee, never by reading it.
    assert CustodyVerdict.CONCENTRATED.stated in where.stated
    assert "is not restated as a current finding" in where.stated


# ── two committees do not pool ──────────────────────────────────────


def test_two_committees_judging_one_asset_keep_separate_histories(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """One asset, two questions, two records, and no transition between them.

    Pooling them would be the same category error as pooling two
    evidence streams — and the filter is a plain string comparison, so
    it works for a committee whose code the reader does not have.
    """

    service = _service(tmp_path)

    from app.services.value_capture_committee import ValueCaptureCommittee

    custody = asyncio.run(CustodyCommittee().judge("HYPE"))
    fees = asyncio.run(ValueCaptureCommittee().judge("HYPE"))

    assert service.record(custody, now=NOW) is not None
    assert service.record(fees, now=NOW) is not None

    mine = service.history("HYPE", CUSTODY.key)
    theirs = service.history("HYPE", FEE_CAPTURE.key)

    assert len(mine) == 1
    assert len(theirs) == 1
    assert mine[0].committee.key != theirs[0].committee.key

    # A transition is projected within one committee's history only.
    assert service.against_history(mine[0]).change is JudgmentChange.FIRST_JUDGMENT
    assert service.against_history(theirs[0]).change is JudgmentChange.FIRST_JUDGMENT


def test_the_fingerprint_separates_two_different_committees() -> None:
    """Different questions cannot collide into one contract identity."""

    assert CUSTODY.fingerprint != FEE_CAPTURE.fingerprint
    assert CUSTODY.identity.comparability(FEE_CAPTURE.identity) is (
        Comparability.DIFFERENT_COMMITTEE
    )

    # And the fingerprint is derived, so each input moves it.
    for altered in (
        fingerprint_of(
            "other",
            CUSTODY.applicability_rule,
            CUSTODY.eligible_claim_types,
            CUSTODY.verdicts,
        ),
        fingerprint_of(
            CUSTODY.question, "other@1", CUSTODY.eligible_claim_types, CUSTODY.verdicts
        ),
        fingerprint_of(
            CUSTODY.question,
            CUSTODY.applicability_rule,
            frozenset({"reported"}),
            CUSTODY.verdicts,
        ),
        fingerprint_of(
            CUSTODY.question,
            CUSTODY.applicability_rule,
            CUSTODY.eligible_claim_types,
            ("concentrated",),
        ),
    ):
        assert altered != CUSTODY.fingerprint


def test_the_protocol_offers_no_way_to_ask_whether_a_verdict_is_good() -> None:
    """A protocol is also a statement about what may not be asked.

    Checked over the surfaces a future caller would reach for, because
    the moment one of these exists, every consumer downstream is free to
    build a score on it and call the score earned.
    """

    forbidden = (
        "polarity",
        "is_favourable",
        "is_positive",
        "is_adverse",
        "rank",
        "score",
        "weight",
        "sentiment",
        "direction",
    )

    for surface in (CommitteeContract, JudgmentTransition):
        for name in forbidden:
            assert not hasattr(surface, name), (surface.__name__, name)

    assert not set(CUSTODY.__dataclass_fields__) & set(forbidden)
