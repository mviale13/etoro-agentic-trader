"""The independent committee portfolio: everything beside, nothing combined.

The slice's acceptance surface. Every test builds its own records in a
temporary store — **nothing here reads the acquired judgment record**,
because a test that did would pass locally and fail on a clean checkout,
which this repository has now watched happen four times.

The matrix's whole job is to lose nothing. So most of these tests are
preservation tests: the eight-asset corpus contains four different
causes of "no answer" and two structurally unrelated kinds of answer,
and a projection that flattened any of them would be easier to read and
false.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    JudgmentState,
)
from app.domain.committee_matrix import (
    AssetCommitteeMatrix,
    CommitteeAssessment,
    UnjudgedCommittee,
)
from app.domain.committee_protocol import CommitteeContract, Comparability
from app.domain.judgment_history import JudgmentPosture
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.crypto_committees import CONTRACTS
from app.services.supply_governance_committee import (
    CONTRACT as SUPPLY_GOVERNANCE,
)
from app.services.supply_governance_committee import (
    Verdict as SupplyVerdict,
)
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import Verdict as FeeVerdict
from tests.reachability import reachable

NOW = datetime(2026, 8, 11, tzinfo=UTC)


# ── the live corpus, rebuilt as records ─────────────────────────────
#
# The #115 matrix, written out so the preservation tests measure the
# projection rather than the acquisition state. Each entry is exactly
# what that committee concluded, including the reason where there is no
# answer.

CORPUS: dict[str, dict[str, dict[str, object]]] = {
    "BTC": {
        FEE_CAPTURE.key: {
            "applicability": Applicability.NOT_ECONOMICALLY_APPLICABLE,
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
            "because": "Its fees are the budget that secures the network.",
            "role": "Monetary network",
        },
        SUPPLY_GOVERNANCE.key: {
            "verdict": SupplyVerdict.CONSENSUS_BOUND,
            "confidence": Confidence.MULTIPLE_OBSERVATIONS,
            "role": "Monetary network",
        },
    },
    "ETH": {
        FEE_CAPTURE.key: {
            "verdict": FeeVerdict.MECHANISM_EVIDENCED,
            "confidence": Confidence.MULTIPLE_OBSERVATIONS,
        },
        SUPPLY_GOVERNANCE.key: {
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.INSUFFICIENT_EVIDENCE,
            "because": "No mechanical issuance rule is held for this asset.",
        },
    },
    "ADA": {
        FEE_CAPTURE.key: {
            "verdict": FeeVerdict.NO_MECHANISM_EVIDENCED,
            "confidence": Confidence.MULTIPLE_OBSERVATIONS,
        },
        SUPPLY_GOVERNANCE.key: {
            "verdict": SupplyVerdict.GOVERNANCE_SET,
            "confidence": Confidence.MULTIPLE_OBSERVATIONS,
        },
    },
    "HYPE": {
        FEE_CAPTURE.key: {
            "state": JudgmentState.UNAVAILABLE,
            "unavailable": "A judgment was drafted and refused.",
        },
        SUPPLY_GOVERNANCE.key: {
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.INSUFFICIENT_EVIDENCE,
            "because": "No mechanical issuance rule is held for this asset.",
        },
    },
    "1INCH": {
        FEE_CAPTURE.key: {
            "verdict": FeeVerdict.NO_MECHANISM_EVIDENCED,
            "confidence": Confidence.MULTIPLE_OBSERVATIONS,
        },
        SUPPLY_GOVERNANCE.key: {
            "applicability": Applicability.NOT_ECONOMICALLY_APPLICABLE,
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
            "because": "Its supply reaches the market by release, not issuance.",
            "role": "Application protocol",
        },
    },
    "TAO": {
        FEE_CAPTURE.key: {
            "applicability": Applicability.UNESTABLISHED,
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.APPLICABILITY_UNESTABLISHED,
            "because": "No economic role is established for this asset.",
            "role": None,
        },
        SUPPLY_GOVERNANCE.key: {
            "applicability": Applicability.UNESTABLISHED,
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.APPLICABILITY_UNESTABLISHED,
            "because": "No economic role is established for this asset.",
            "role": None,
        },
    },
}

_CONTRACTS = {FEE_CAPTURE.key: FEE_CAPTURE, SUPPLY_GOVERNANCE.key: SUPPLY_GOVERNANCE}


def _judgment(asset: str, contract: CommitteeContract, spec: dict[str, object]):  # type: ignore[no-untyped-def]
    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=spec.get("state", JudgmentState.JUDGED),  # type: ignore[arg-type]
        basis=ApplicabilityBasis(
            applicability=spec.get("applicability", Applicability.APPLICABLE),  # type: ignore[arg-type]
            because="fixture",
            economic_role=spec.get("role", "Smart-contract network"),  # type: ignore[arg-type]
        ),
        verdict=spec.get("verdict"),  # type: ignore[arg-type]
        confidence=spec.get("confidence"),  # type: ignore[arg-type]
        refs=("A1", "A2") if spec.get("verdict") else (),
        because=spec.get("because"),  # type: ignore[arg-type]
        abstained_because=spec.get("abstained"),  # type: ignore[arg-type]
        unavailable_because=spec.get("unavailable"),  # type: ignore[arg-type]
        judged_at=NOW,
    )


def _service(tmp_path) -> CommitteeMatrixService:  # type: ignore[no-untyped-def]
    from app.services.judgment_history_service import JudgmentHistoryService

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    for asset, per_committee in CORPUS.items():
        for key, spec in per_committee.items():
            history.record(_judgment(asset, _CONTRACTS[key], spec), now=NOW)

    return CommitteeMatrixService(history=history)


# ── 1. every registered committee appears ───────────────────────────


def test_every_registered_committee_appears(tmp_path) -> None:  # type: ignore[no-untyped-def]
    matrix = _service(tmp_path).for_asset("ADA")

    seen = {cell.committee.key for cell in matrix.assessments}
    seen |= {cell.committee.key for cell in matrix.unjudged}

    assert seen == {contract.key for contract in CONTRACTS}


def test_a_committee_that_never_ran_is_its_own_state(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """*Never tried* and *tried and could not answer* are different facts."""

    matrix = _service(tmp_path).for_asset("SOL")

    assert not matrix.assessments
    assert len(matrix.unjudged) == len(CONTRACTS)

    missing = matrix.unjudged[0]

    assert isinstance(missing, UnjudgedCommittee)
    assert "recorded no judgment" in missing.stated
    assert missing.question


# ── 2. committee N+1 needs no matrix-specific branch ────────────────


def test_a_third_committee_appears_without_touching_the_matrix(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The core invariant, checked with a committee that ships nowhere.

    The protocol acceptance specimen from PR #114 is registered by
    passing its contract in, and the matrix renders it without a single
    branch learning it exists — which it could not have, because this
    layer does not know what any verdict means.
    """

    from app.services.judgment_history_service import JudgmentHistoryService
    from tests.test_committee_protocol import CUSTODY, CustodyCommittee, CustodyVerdict

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    committee = CustodyCommittee(CustodyVerdict.MIXED)

    history.record(asyncio.run(committee.judge("XYZ")), now=NOW)

    matrix = CommitteeMatrixService(history=history).for_asset(
        "XYZ", contracts=(*CONTRACTS, CUSTODY)
    )

    cell = matrix.for_committee(CUSTODY.key)

    assert cell is not None
    assert cell.is_answered
    assert cell.verdict == CustodyVerdict.MIXED.value
    assert cell.verdict_stated == CustodyVerdict.MIXED.stated
    assert cell.question == CUSTODY.question

    # Its three-verdict vocabulary survives a projection built when only
    # two-verdict committees existed.
    assert len(CUSTODY.verdicts) == 3

    # And the matrix module names no committee at all.
    for module in (
        "app/domain/committee_matrix.py",
        "app/services/committee_matrix_service.py",
    ):
        code = reachable(module)

        for token in (*FEE_CAPTURE.verdicts, *SUPPLY_GOVERNANCE.verdicts):
            assert token not in code, (module, token)

        assert "value_capture" not in code, module
        assert "supply_governance" not in code, module


# ── 3–6. the corpus distinctions survive ────────────────────────────


def test_btc_and_1inch_keep_their_opposite_applicability(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The cross that proves the committees are not one question twice."""

    service = _service(tmp_path)

    bitcoin = service.for_asset("BTC")
    inch = service.for_asset("1INCH")

    assert bitcoin.for_committee(FEE_CAPTURE.key).applicability is (  # type: ignore[union-attr]
        Applicability.NOT_ECONOMICALLY_APPLICABLE
    )
    assert bitcoin.for_committee(SUPPLY_GOVERNANCE.key).is_answered  # type: ignore[union-attr]

    assert inch.for_committee(FEE_CAPTURE.key).is_answered  # type: ignore[union-attr]
    assert inch.for_committee(SUPPLY_GOVERNANCE.key).applicability is (  # type: ignore[union-attr]
        Applicability.NOT_ECONOMICALLY_APPLICABLE
    )


def test_hype_keeps_two_different_unanswered_reasons(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Identical-looking absences are not flattened into "unknown".

    One committee's machinery failed; the other's evidence could not
    answer. Both read "no answer" and they are different facts about
    different things.
    """

    matrix = _service(tmp_path).for_asset("HYPE")

    fees = matrix.for_committee(FEE_CAPTURE.key)
    supply = matrix.for_committee(SUPPLY_GOVERNANCE.key)

    assert fees is not None and supply is not None

    assert not fees.is_answered
    assert not supply.is_answered

    assert fees.posture is JudgmentPosture.EXECUTION_UNAVAILABLE
    assert supply.posture is JudgmentPosture.EVIDENCE_INSUFFICIENT

    assert fees.posture is not supply.posture
    assert fees.stated != supply.stated

    # Each keeps its own sentence, which is where the difference lives.
    assert fees.unavailable_because
    assert supply.because
    assert fees.unavailable_because != supply.because


def test_ada_keeps_two_structurally_different_answers(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Neither answer is mapped onto the other, or onto a shared scale."""

    matrix = _service(tmp_path).for_asset("ADA")

    fees = matrix.for_committee(FEE_CAPTURE.key)
    supply = matrix.for_committee(SUPPLY_GOVERNANCE.key)

    assert fees is not None and supply is not None

    assert fees.is_answered and supply.is_answered

    assert fees.verdict == FeeVerdict.NO_MECHANISM_EVIDENCED.value
    assert supply.verdict == SupplyVerdict.GOVERNANCE_SET.value

    # Different vocabularies, and the projection never translates one
    # into the other's terms.
    assert fees.verdict not in SUPPLY_GOVERNANCE.verdicts
    assert supply.verdict not in FEE_CAPTURE.verdicts

    # Each is worded by its own committee.
    assert fees.verdict_stated == FeeVerdict.NO_MECHANISM_EVIDENCED.stated
    assert supply.verdict_stated == SupplyVerdict.GOVERNANCE_SET.stated


def test_tao_keeps_applicability_uncertainty_per_committee(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Two committees reaching the same state is still two statements."""

    matrix = _service(tmp_path).for_asset("TAO")

    cells = {cell.committee.key: cell for cell in matrix.assessments}

    assert len(cells) == 2

    for cell in cells.values():
        assert cell.applicability is Applicability.UNESTABLISHED
        assert cell.posture is JudgmentPosture.APPLICABILITY_UNKNOWN
        assert cell.economic_role is None

    # And they are two cells, not one shared conclusion.
    assert cells[FEE_CAPTURE.key] is not cells[SUPPLY_GOVERNANCE.key]
    assert (
        cells[FEE_CAPTURE.key].committee.fingerprint
        != cells[SUPPLY_GOVERNANCE.key].committee.fingerprint
    )


# ── 7. no aggregate anywhere ────────────────────────────────────────

#: What this layer must never offer. Every one of them would be the
#: layer above wearing a projection's name.
FORBIDDEN = (
    "aggregate",
    "aggregated",
    "agreement",
    "agree",
    "consensus",
    "combined",
    "overall",
    "total",
    "score",
    "scored",
    "weight",
    "weighted",
    "rank",
    "ranking",
    "majority",
    "vote",
    "votes",
    "recommendation",
    "recommend",
    "conviction",
    "thesis",
    "favourable",
    "favorable",
    "adverse",
    "bullish",
    "bearish",
    "sentiment",
    "quality_score",
    "strength",
)


def test_the_matrix_offers_no_aggregation_of_any_kind() -> None:
    """The negative architectural test. Searched, not asserted about."""

    for surface in (CommitteeAssessment, AssetCommitteeMatrix, UnjudgedCommittee):
        names = set(dir(surface))

        for forbidden in FORBIDDEN:
            assert forbidden not in names, (surface.__name__, forbidden)

    assert set(AssetCommitteeMatrix.__dataclass_fields__) == {
        "asset",
        "assessments",
        "unjudged",
    }


def test_no_matrix_module_defines_an_aggregating_api() -> None:
    """And the source itself carries no such vocabulary.

    A word test rather than a field test, because the next aggregate
    would arrive as a helper function rather than as a dataclass field.
    """

    import re

    for module in (
        "app/domain/committee_matrix.py",
        "app/services/committee_matrix_service.py",
        "app/commands/committees.py",
    ):
        code = reachable(module)

        definitions = re.findall(r"^\s*(?:def|class)\s+(\w+)", code, re.M)

        for name in definitions:
            for forbidden in FORBIDDEN:
                assert forbidden not in name.lower(), (module, name)


def test_the_serialised_cell_carries_no_combination(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The frontend receives states and sentences, never raw material."""

    payload = _service(tmp_path).for_asset("ADA").as_dict()

    assert set(payload) == {"asset", "committees"}
    assert len(payload["committees"]) == len(CONTRACTS)

    for cell in payload["committees"]:
        for forbidden in FORBIDDEN:
            assert forbidden not in cell, forbidden

        # Every semantic decision is already made: the surface renders
        # `posture_stated` and `verdict_stated`, and is never handed the
        # material to infer them.
        assert "posture_stated" in cell
        assert "stated" in cell


# ── 8. confidence carried, never aggregated ─────────────────────────


def test_confidence_is_carried_per_committee_and_never_combined(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Two committees express confidence; the matrix expresses none.

    The measured reason: Supply Governance saturates at
    `MULTIPLE_OBSERVATIONS` for 8, 9 and 11 findings, so the value means
    something different in each column. Carrying it is honest; comparing
    it would not be.
    """

    matrix = _service(tmp_path).for_asset("ADA")

    for cell in matrix.assessments:
        assert cell.confidence is Confidence.MULTIPLE_OBSERVATIONS

    # Identical values, and nothing offers to combine or compare them.
    assert not hasattr(matrix, "confidence")

    for name in dir(AssetCommitteeMatrix):
        assert "confidence" not in name.lower()


def test_evidence_counts_are_never_summed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """They count different kinds of thing, so a total is about neither."""

    matrix = _service(tmp_path).for_asset("ADA")

    assert all(cell.evidence_count >= 0 for cell in matrix.assessments)

    for name in dir(AssetCommitteeMatrix):
        assert "evidence" not in name.lower()


# ── 9–10. traceability and contract identity ────────────────────────


def test_every_cell_traces_to_its_own_judgment(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Refs, evidence count and the committee's own reason travel per cell."""

    matrix = _service(tmp_path).for_asset("ADA")

    for cell in matrix.assessments:
        assert cell.refs
        assert cell.judged_at is not None
        assert cell.committee.fingerprint

    # The refs belong to their own committee's judgment and are never
    # pooled into a shared list.
    assert not hasattr(matrix, "refs")


def test_contract_identity_and_comparability_survive_projection(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """#114's comparability is carried, so a stale conclusion says so."""

    matrix = _service(tmp_path).for_asset("ADA")

    for cell in matrix.assessments:
        assert cell.comparability is Comparability.COMPARABLE
        assert cell.is_current_contract
        assert cell.judgments_recorded == 1


def test_a_conclusion_under_an_earlier_contract_is_visibly_historical(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """A verdict reached under a revised contract is not quietly current."""

    from app.services.judgment_history_service import JudgmentHistoryService

    revised = CommitteeContract(
        key=SUPPLY_GOVERNANCE.key,
        name=SUPPLY_GOVERNANCE.name,
        question=SUPPLY_GOVERNANCE.question,
        version=2,
        applicability_rule="something-else@2",
        verdicts=SUPPLY_GOVERNANCE.verdicts,
        eligible_claim_types=SUPPLY_GOVERNANCE.eligible_claim_types,
    )

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    history.record(
        _judgment("ADA", SUPPLY_GOVERNANCE, {"verdict": SupplyVerdict.GOVERNANCE_SET}),
        now=NOW - timedelta(days=1),
    )

    matrix = CommitteeMatrixService(history=history).for_asset(
        "ADA", contracts=(revised,)
    )

    cell = matrix.for_committee(SUPPLY_GOVERNANCE.key)

    assert cell is not None
    assert cell.comparability is Comparability.DIFFERENT_VERSION
    assert not cell.is_current_contract

    # The conclusion is still shown — it is what the committee
    # concluded then — and its contract says it is not today's.
    assert cell.verdict == SupplyVerdict.GOVERNANCE_SET.value
    assert cell.committee.version == 1


# ── the projection reads and never writes ───────────────────────────


def test_reading_the_matrix_convenes_nothing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A surface that judged would manufacture judgment events."""

    service = _service(tmp_path)

    before = JudgmentHistoryStore(root=tmp_path).records("ADA")

    for _ in range(3):
        service.for_asset("ADA")

    after = JudgmentHistoryStore(root=tmp_path).records("ADA")

    assert len(before) == len(after)

    code = reachable("app/services/committee_matrix_service.py")

    for forbidden in ("judge(", "committees(", "provider", "acquire"):
        assert forbidden not in code, forbidden
