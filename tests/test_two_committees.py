"""Two real committees coexisting, and what history must not do about it.

The slice's actual deliverable. Not *two committees* — the first
empirical evidence of how independent judgments sit beside one another,
and the guarantees that keep them independent while they do.

Every test here uses both **real** committees. The protocol acceptance
specimen in `test_committee_protocol.py` proved the framework could run
a committee it had never seen; this proves two committees that actually
ship do not contaminate each other.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.committee_judgment import Applicability
from app.domain.committee_protocol import Comparability
from app.domain.judgment_history import JudgmentChange, compare, record_from
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.crypto_committees import CONTRACTS, committees, contract_for
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.supply_governance_committee import (
    CONTRACT as SUPPLY_GOVERNANCE,
)
from app.services.supply_governance_committee import (
    SupplyGovernanceCommittee,
)
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import ValueCaptureCommittee

NOW = datetime(2026, 8, 11, tzinfo=UTC)


def _service(tmp_path) -> JudgmentHistoryService:  # type: ignore[no-untyped-def]
    return JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))


def _record_both(service: JudgmentHistoryService, asset: str, at: datetime = NOW):  # type: ignore[no-untyped-def]
    for committee in (SupplyGovernanceCommittee(), ValueCaptureCommittee()):
        judgment = asyncio.run(committee.judge(asset))

        service.record(judgment, committee.evidence(asset), now=at)


# ── the registry, and the failure that earned it ────────────────────


def test_the_registry_names_every_committee_exactly_once() -> None:
    """Earned by a failure, not anticipated.

    With one committee both surfaces named its contract directly and
    were right. With two, the history surface would have shown Fee
    Capture's record and stopped — and a reader would have concluded
    that the second committee had never judged anything.
    """

    keys = [contract.key for contract in CONTRACTS]

    assert sorted(keys) == sorted(set(keys))
    assert set(keys) == {FEE_CAPTURE.key, SUPPLY_GOVERNANCE.key}
    assert {committee.contract.key for committee in committees()} == set(keys)

    assert contract_for(FEE_CAPTURE.key) is FEE_CAPTURE
    assert contract_for(SUPPLY_GOVERNANCE.key) is SUPPLY_GOVERNANCE

    # A record written by a committee that no longer exists is still a
    # record. The lookup says so rather than raising.
    assert contract_for("a_committee_that_was_removed") is None


def test_the_registry_offers_no_ordering_that_means_anything() -> None:
    """A list, and deliberately not more than one.

    The moment this offers priority or weight, every consumer downstream
    can build an aggregate on it and call the aggregate earned.
    """

    from app.services import crypto_committees

    for forbidden in ("weight", "priority", "rank", "score", "primary", "default"):
        assert not hasattr(crypto_committees, forbidden), forbidden


# ── the histories do not pool ───────────────────────────────────────


def test_one_asset_carries_two_independent_histories(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The same asset, two questions, two records, no transition between."""

    service = _service(tmp_path)

    _record_both(service, "ADA")

    fees = service.history("ADA", FEE_CAPTURE.key)
    supply = service.history("ADA", SUPPLY_GOVERNANCE.key)

    assert len(fees) == 1
    assert len(supply) == 1

    assert fees[0].committee.key != supply[0].committee.key
    assert fees[0].record_id != supply[0].record_id

    # Each is the first judgment of its own committee, and neither has
    # been compared with the other.
    assert service.against_history(fees[0]).change is JudgmentChange.FIRST_JUDGMENT
    assert service.against_history(supply[0]).change is JudgmentChange.FIRST_JUDGMENT


def test_one_committees_history_never_reaches_the_others(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Records cannot migrate between committees, in either direction."""

    service = _service(tmp_path)

    _record_both(service, "ADA", NOW)
    _record_both(service, "ADA", NOW + timedelta(days=1))

    for contract in (FEE_CAPTURE, SUPPLY_GOVERNANCE):
        held = service.history("ADA", contract.key)

        assert held, contract.key
        assert {record.committee.key for record in held} == {contract.key}

    # A transition projected for one committee cites only its own
    # records — the ids are the check.
    fee_ids = {record.record_id for record in service.history("ADA", FEE_CAPTURE.key)}

    for transition in service.transitions("ADA", SUPPLY_GOVERNANCE.key):
        assert not set(transition.record_ids) & fee_ids


def test_a_judgment_is_only_ever_compared_within_its_own_committee(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """`against_history` reads the committee off the record, not the caller."""

    service = _service(tmp_path)

    _record_both(service, "ADA", NOW)

    supply = service.history("ADA", SUPPLY_GOVERNANCE.key)[0]

    assert service.against_history(supply).committee == SUPPLY_GOVERNANCE.key


def test_two_committees_records_are_structurally_incomparable() -> None:
    """Even placed side by side, the projection refuses to compare them."""

    fees = asyncio.run(ValueCaptureCommittee().judge("ADA"))
    supply = asyncio.run(SupplyGovernanceCommittee().judge("ADA"))

    transition = compare(
        record_from(supply, (), NOW),
        record_from(fees, (), NOW - timedelta(days=1)),
    )

    assert transition.comparability is Comparability.DIFFERENT_COMMITTEE
    assert transition.change is JudgmentChange.INCOMPARABLE_VERSION
    assert "not compared" in transition.stated


def test_the_contract_fingerprints_are_committee_specific() -> None:
    assert FEE_CAPTURE.fingerprint != SUPPLY_GOVERNANCE.fingerprint
    assert FEE_CAPTURE.identity.comparability(SUPPLY_GOVERNANCE.identity) is (
        Comparability.DIFFERENT_COMMITTEE
    )


# ── applicability is committee-specific ─────────────────────────────


def test_applicability_is_decided_per_committee_and_can_disagree() -> None:
    """The cross that proves the two are not one question twice.

    BTC and 1INCH swap sides, which is only possible because each
    committee owns its own rule in its own economic terms.
    """

    fees = ValueCaptureCommittee()
    supply = SupplyGovernanceCommittee()

    crossings = {
        "BTC": (
            Applicability.NOT_ECONOMICALLY_APPLICABLE,
            Applicability.APPLICABLE,
        ),
        "1INCH": (
            Applicability.APPLICABLE,
            Applicability.NOT_ECONOMICALLY_APPLICABLE,
        ),
    }

    for asset, (expected_fees, expected_supply) in crossings.items():
        assert fees.basis(asset).applicability is expected_fees, asset
        assert supply.basis(asset).applicability is expected_supply, asset


def test_an_applicability_change_moves_one_history_and_not_the_other(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """A committee-specific change stays in its own record.

    Built by recording one committee twice with a changed applicability
    while the other's record stands still — the shape a re-classified
    asset would produce.
    """

    service = _service(tmp_path)

    _record_both(service, "ADA", NOW)

    committee = SupplyGovernanceCommittee()

    judgment = asyncio.run(committee.judge("1INCH"))

    # 1INCH's applicability under this committee differs from ADA's, so
    # filing it as the same asset's later judgment is a clean stand-in
    # for a re-classification.
    reclassified = record_from(
        judgment,
        (),
        recorded_at=NOW + timedelta(days=1),
    )

    earlier = service.history("ADA", SUPPLY_GOVERNANCE.key)[0]

    moved = compare(reclassified, earlier)

    assert moved.change is JudgmentChange.APPLICABILITY_CHANGED

    # Fee Capture's record for ADA is untouched by any of it.
    fees = service.history("ADA", FEE_CAPTURE.key)

    assert len(fees) == 1
    assert service.against_history(fees[0]).change is JudgmentChange.FIRST_JUDGMENT


# ── the law from #113 and #114 still holds with two ─────────────────


def test_agreement_between_committees_is_not_representable() -> None:
    """No object can express *both committees agree*, and none may.

    The point of stopping here is that the layer above is supposed to be
    decided from the matrix rather than sketched before it — so nothing
    in this slice may quietly pre-decide it.
    """

    fees = record_from(asyncio.run(ValueCaptureCommittee().judge("SOL")), (), NOW)
    supply = record_from(asyncio.run(SupplyGovernanceCommittee().judge("SOL")), (), NOW)

    # Both answered. There is no field, property or helper anywhere that
    # combines them.
    for record in (fees, supply):
        for forbidden in ("agrees_with", "combined", "consensus", "aggregate"):
            assert not hasattr(record, forbidden), forbidden

    transition = compare(supply, fees)

    assert transition.comparability is Comparability.DIFFERENT_COMMITTEE

    for forbidden in ("agreement", "conviction", "score", "combined"):
        assert not hasattr(transition, forbidden), forbidden


def test_no_committee_can_read_another_committees_record() -> None:
    """Structural: neither committee imports history or the registry."""

    from tests.reachability import reachable

    for module in (
        "app/services/value_capture_committee.py",
        "app/services/supply_governance_committee.py",
    ):
        code = reachable(module)

        assert "judgment_history" not in code, module
        assert "crypto_committees" not in code, module
