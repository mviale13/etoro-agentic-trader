"""What a judgment's evidence count counts, and when it may be compared.

PR #126 removed *"Evidence it weighed"* from the crypto dossier after
finding that Bitcoin's Value Capture declined the question as the wrong
instrument, cited nothing, and was recorded as having weighed three
findings. That was a presentation fix over a recording defect, and this
is the recording defect.

**The field was an accidental mixture, and the corpus settles it.** The
recording command resolved `committee.evidence(asset)` itself, beside
the judgment — so on every path where `judge()` consults its evidence
the count meant *what the committee was given*, and on the two
applicability paths, which return before consulting anything, it meant
*what this platform happened to hold*. Sixty-seven stored records, and
the split is visible in them: `value_capture` records ten declined and
unestablished judgments carrying counts of 3 and 1 with no refs at all.

**And it is not `refs`.** Eleven of twenty-six answered judgments cite
fewer findings than they were given, so *supplied* and *cited* are two
facts and one counter could never have carried both.

The repair has two halves and needs both:

1. the judgment carries the evidence it was given, so a caller cannot
   disagree with it — PR #113's identity fix, applied to evidence;
2. the record says which meaning it was written under, so a correction
   to this platform's bookkeeping is never reported as evidence moving.

Without the second, correcting the first made four live series announce
evidence appearing or vanishing with nothing about any asset having
changed. Every fixture here is built rather than acquired.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    ClaimType,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
    abstain,
    unavailable,
)
from app.domain.committee_protocol import CommitteeContract
from app.domain.judgment_history import (
    CURRENT_EVIDENCE_SEMANTICS,
    EvidenceMovement,
    EvidenceSemantics,
    JudgmentPosture,
    compare,
    record_from,
)
from app.infrastructure.evidence.judgment_history_store import (
    SCHEMA,
    JudgmentHistoryStore,
)
from app.services.supply_governance_committee import SupplyGovernanceCommittee
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import ValueCaptureCommittee
from app.services.value_capture_committee import Verdict as FeeVerdict

NOW = datetime(2026, 8, 16, tzinfo=UTC)

#: The postures reached only *after* a committee has asked for its
#: evidence. Every other posture is reached before, and must therefore
#: record nothing — which is the invariant the whole file exists for.
CONSULTED = frozenset(
    {
        JudgmentPosture.ANSWERED,
        JudgmentPosture.EVIDENCE_INSUFFICIENT,
        JudgmentPosture.EXECUTION_UNAVAILABLE,
    }
)


def _findings(count: int) -> tuple[EligibleFinding, ...]:
    return tuple(
        EligibleFinding(
            ref=f"A{index}",
            stated=f"finding {index}",
            claim_type=ClaimType.MEASURED,
            established_by="Test fixture",
        )
        for index in range(1, count + 1)
    )


def _judgment(
    *,
    contract: CommitteeContract = FEE_CAPTURE,
    considered: tuple[EligibleFinding, ...] = (),
    refs: tuple[str, ...] = (),
    state: JudgmentState = JudgmentState.JUDGED,
    applicability: Applicability = Applicability.APPLICABLE,
    verdict: object = FeeVerdict.MECHANISM_EVIDENCED,
    at: datetime = NOW,
) -> CommitteeJudgment:
    return CommitteeJudgment(
        asset="TEST",
        contract=contract,
        state=state,
        basis=ApplicabilityBasis(applicability, "fixture", "Exchange network"),
        verdict=verdict if state is JudgmentState.JUDGED else None,  # type: ignore[arg-type]
        confidence=(
            Confidence.SINGLE_OBSERVATION if state is JudgmentState.JUDGED else None
        ),
        refs=refs,
        considered=considered,
        abstained_because=(
            AbstentionReason.NOT_ECONOMICALLY_APPLICABLE
            if state is JudgmentState.ABSTAINED
            else None
        ),
        unavailable_because=("off" if state is JudgmentState.UNAVAILABLE else None),
        judged_at=at,
    )


# ── 1. the two concepts are distinct, and both are kept ─────────────


def test_supplied_and_cited_are_two_facts() -> None:
    """A verdict may rest on fewer findings than it was handed.

    Eleven of the live corpus's twenty-six answered judgments do exactly
    that, which is why one counter could never have carried both. The
    record keeps `evidence_count` for what was supplied and `refs` for
    what was cited, and neither is derived from the other.
    """

    record = record_from(
        _judgment(considered=_findings(5), refs=("A1", "A2")),
        recorded_at=NOW,
    )

    assert record.evidence_count == 5
    assert len(record.refs) == 2


def test_a_judgment_never_cites_what_it_was_not_given() -> None:
    """The one direction that would be incoherent, over both committees."""

    for committee in (ValueCaptureCommittee(), SupplyGovernanceCommittee()):
        for asset in ("BTC", "ADA", "HYPE", "TAO", "1INCH"):
            record = record_from(asyncio.run(committee.judge(asset)), recorded_at=NOW)

            assert len(record.refs) <= record.evidence_count, (
                f"{asset}/{record.committee.key} cites more than it was given"
            )


# ── 2. a committee that never asked never claims to have weighed ────


@pytest.mark.parametrize(
    ("committee", "asset"),
    [
        (ValueCaptureCommittee(), "BTC"),
        (ValueCaptureCommittee(), "TAO"),
        (SupplyGovernanceCommittee(), "1INCH"),
        (SupplyGovernanceCommittee(), "TAO"),
    ],
)
def test_a_declined_question_records_no_evidence(
    committee: object,
    asset: str,
) -> None:
    """The defect itself, on the four live cases that produced it.

    BTC's Value Capture is the one PR #126 found: the question is the
    wrong instrument for a monetary asset, `judge()` returns before
    reading anything, and the record said three findings.
    """

    record = record_from(asyncio.run(committee.judge(asset)), recorded_at=NOW)  # type: ignore[attr-defined]

    assert record.posture not in CONSULTED
    assert record.evidence_count == 0
    assert record.refs == ()


def test_a_committee_that_declines_never_reaches_its_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Structural, not observational: the evidence door is made to explode.

    Asserting the count is zero would pass for a committee that read its
    evidence and threw it away. This asserts the stronger thing — that
    the call never happens — which is the invariant the recorded count
    now rests on.
    """

    def detonate(self: object, symbol: str) -> tuple[EligibleFinding, ...]:
        raise AssertionError(
            f"{symbol}: evidence was consulted on a path that declines the "
            "question, so a recorded count would describe findings the "
            "committee never weighed"
        )

    monkeypatch.setattr(ValueCaptureCommittee, "evidence", detonate)
    monkeypatch.setattr(SupplyGovernanceCommittee, "evidence", detonate)

    for committee, asset in (
        (ValueCaptureCommittee(), "BTC"),
        (ValueCaptureCommittee(), "TAO"),
        (SupplyGovernanceCommittee(), "1INCH"),
        (SupplyGovernanceCommittee(), "TAO"),
    ):
        judgment = asyncio.run(committee.judge(asset))

        assert judgment.considered == ()


def test_asked_and_given_nothing_is_not_the_same_as_never_asking() -> None:
    """Both record zero, and the postures keep them apart.

    `EVIDENCE_INSUFFICIENT` means the committee asked and was handed
    nothing; an applicability abstention means it never reached the
    question. A count alone cannot tell them apart and is not asked to.
    """

    asked = record_from(
        abstain(
            "TEST",
            FEE_CAPTURE,
            AbstentionReason.INSUFFICIENT_EVIDENCE,
            ApplicabilityBasis(Applicability.APPLICABLE, "fixture", "Venue"),
            considered=(),
        ),
        recorded_at=NOW,
    )

    never = record_from(
        abstain(
            "TEST",
            FEE_CAPTURE,
            AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
            ApplicabilityBasis(
                Applicability.NOT_ECONOMICALLY_APPLICABLE, "fixture", "Money"
            ),
        ),
        recorded_at=NOW,
    )

    assert asked.evidence_count == never.evidence_count == 0
    assert asked.posture is JudgmentPosture.EVIDENCE_INSUFFICIENT
    assert never.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE


def test_the_recorder_cannot_be_told_what_a_judgment_weighed() -> None:
    """The signature is the guard, exactly as PR #113 made it for identity."""

    from inspect import signature

    from app.services.judgment_history_service import JudgmentHistoryService

    assert "evidence" not in signature(record_from).parameters
    assert "evidence" not in signature(JudgmentHistoryService.record).parameters


def test_machinery_failing_after_the_evidence_arrived_keeps_it() -> None:
    """An unavailable judgment is not automatically an empty one.

    Value Capture reads its findings before it checks whether judging is
    switched on, so a run with the flag off has been given its evidence
    and reached no verdict — and zeroing it would lose a true fact to
    fix a different one.
    """

    record = record_from(
        unavailable(
            "TEST",
            FEE_CAPTURE,
            "Committee judgment is off.",
            ApplicabilityBasis(Applicability.APPLICABLE, "fixture", "Venue"),
            considered=_findings(4),
        ),
        recorded_at=NOW,
    )

    assert record.posture is JudgmentPosture.EXECUTION_UNAVAILABLE
    assert record.evidence_count == 4
    assert record.refs == ()


# ── 3. history is versioned, never rewritten ────────────────────────


def test_a_record_written_today_declares_todays_meaning() -> None:
    record = record_from(_judgment(considered=_findings(2)), recorded_at=NOW)

    assert record.evidence_semantics is CURRENT_EVIDENCE_SEMANTICS
    assert record.evidence_semantics is EvidenceSemantics.SUPPLIED_TO_COMMITTEE


def test_a_line_without_the_field_decodes_as_the_old_meaning(
    tmp_path: object,
) -> None:
    """Absent is not unknown. Those lines were written by a recorder that
    resolved the evidence itself, and that is what they say."""

    import json

    store = JudgmentHistoryStore(root=tmp_path)  # type: ignore[arg-type]

    written = record_from(_judgment(considered=_findings(3)), recorded_at=NOW)

    assert store.append(written)

    path = store.path_for("TEST")

    row = json.loads(path.read_text().strip())

    assert row["schema"] == SCHEMA
    assert row["evidence_semantics"] == EvidenceSemantics.SUPPLIED_TO_COMMITTEE

    # The same line as a schema-4 writer would have left it.
    del row["evidence_semantics"]
    row["schema"] = 4
    path.write_text(json.dumps(row, sort_keys=True) + "\n")

    read = store.records("TEST")

    assert len(read) == 1
    assert read[0].evidence_semantics is EvidenceSemantics.HELD_AT_RECORDING
    assert read[0].evidence_count == 3


def test_two_meanings_are_never_subtracted_from_each_other() -> None:
    """The correction the migration exists to keep out of the record.

    Under the old meaning BTC's declined Value Capture recorded three
    findings; under the new one it records none. That is this platform
    correcting its own bookkeeping, and reporting it as `WITHDRAWN`
    would make an asset look like it had lost its evidence.
    """

    old = replace(
        record_from(_judgment(considered=_findings(3)), recorded_at=NOW),
        evidence_semantics=EvidenceSemantics.HELD_AT_RECORDING,
    )

    new = record_from(
        _judgment(considered=(), at=NOW + timedelta(days=1)), recorded_at=NOW
    )

    moved = compare(new, old)

    assert moved.evidence is EvidenceMovement.SEMANTICS_CHANGED
    assert not moved.evidence.moved
    assert "not compared" in moved.evidence.stated


def test_a_semantics_change_is_not_a_contract_change() -> None:
    """Two different incomparabilities, and conflating them would lie.

    `NOT_COMPARABLE` says the *question* differed. Here the committee,
    the contract and the question are identical and only this platform's
    account of what it counted has moved, so the sentence must not claim
    a contract change.
    """

    assert (
        EvidenceMovement.SEMANTICS_CHANGED.stated
        != EvidenceMovement.NOT_COMPARABLE.stated
    )
    assert "contract" not in EvidenceMovement.SEMANTICS_CHANGED.stated
    assert not EvidenceMovement.SEMANTICS_CHANGED.moved


def test_records_under_one_meaning_still_compare_normally() -> None:
    """Versioning must not silence the axis it protects."""

    first = record_from(_judgment(considered=_findings(3)), recorded_at=NOW)

    same = record_from(
        _judgment(considered=_findings(3), at=NOW + timedelta(days=1)),
        recorded_at=NOW,
    )
    richer = record_from(
        _judgment(considered=_findings(4), at=NOW + timedelta(days=2)),
        recorded_at=NOW,
    )
    empty = record_from(
        _judgment(considered=(), at=NOW + timedelta(days=3)),
        recorded_at=NOW,
    )

    assert compare(same, first).evidence is EvidenceMovement.UNCHANGED
    assert compare(richer, same).evidence is EvidenceMovement.CHANGED
    assert compare(empty, richer).evidence is EvidenceMovement.WITHDRAWN
    assert compare(richer, empty).evidence is EvidenceMovement.ARRIVED


def test_every_evidence_movement_has_a_sentence() -> None:
    """The vocabulary stays finite and fully enumerated — PR #113's rule."""

    said = {member.stated for member in EvidenceMovement}

    assert len(said) == len(EvidenceMovement)
    assert all(sentence and sentence[0].islower() for sentence in said)


def test_every_semantics_has_a_sentence() -> None:
    said = {member.stated for member in EvidenceSemantics}

    assert len(said) == len(EvidenceSemantics)
