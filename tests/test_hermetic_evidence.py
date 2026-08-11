"""Analytical execution is hermetic with respect to undeclared evidence.

Five separate times across the crypto work, a test read evidence that
existed on the developer's machine and not in the repository. Each looked
like a test-writing mistake; five is an architectural boundary problem.

**The failure was never about caching.** It was that an analytical call
declared a *subject* and never an *evidence set* — `committee.judge("ADA")`
— so the service resolved its own evidence from a path literal and the
answer depended on the machine. Measured on this repository: a
hand-edited `data/cache/issuance_rules` flips Cardano from
`governance_set` to `consensus_bound` with the caller declaring nothing.

The tests below are **behavioural, not naming-only**. Each one builds a
tempting ambient cache, supplies explicit fixture evidence, and proves
the ambient copy cannot reach the answer. The inverse is tested too: the
stored path, deliberately selected, does participate — otherwise the
guarantee would be "nothing works" rather than "the declared input
wins".
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.domain.asset_class import AssetClass
from app.domain.committee_judgment import (
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    JudgmentState,
)
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.investor_assessment import StatementShape
from app.domain.mechanical_issuance import (
    IssuanceMechanism,
    IssuanceState,
    MechanicalIssuance,
    ProjectedIssuance,
    RuleMutability,
    RuleParameter,
)
from app.domain.supply_semantics import (
    PrimaryProvenance,
    SupplyConcept,
    SupplyFact,
    SupplyMethodology,
    SupplyPicture,
)
from app.infrastructure.cache.json_cache import JsonCache
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.infrastructure.evidence_root import ROOT_ENV, evidence_path, evidence_root
from app.providers.cached_issuance_provider import SCHEMA as ISSUANCE_SCHEMA
from app.providers.cached_issuance_provider import CachedIssuanceRuleProvider
from app.providers.cached_issuance_provider import _encode as encode_rule
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.investor_assessment_service import InvestorAssessmentService
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.supply_governance_committee import (
    CONTRACT as SUPPLY_GOVERNANCE,
)
from app.services.supply_governance_committee import (
    SupplyGovernanceCommittee,
)
from app.services.supply_governance_committee import (
    Verdict as SupplyVerdict,
)
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import Verdict as FeeVerdict

NOW = datetime(2026, 8, 11, tzinfo=UTC)


# ── fixtures: evidence this repository owns ─────────────────────────


def _rule(mutability: RuleMutability) -> MechanicalIssuance:
    return MechanicalIssuance(
        symbol="ADA",
        mechanism=IssuanceMechanism.RESERVE_DRAW,
        state=IssuanceState(unit="ADA", position="epoch 500", observed_at=NOW),
        formula="reserves * rho each epoch",
        parameters=(
            RuleParameter(
                name="rho",
                value=0.003,
                unit="proportion",
                read_from="cardano ledger /genesis",
                means="the share of reserves drawn each epoch",
            ),
        ),
        mutability=mutability,
        provenance=PrimaryProvenance(
            surface_is_canonical=True,
            identity_because="the chain endpoint is the asset",
            rule_version="ada-reserve-draw/1",
            formula="reserves * rho",
        ),
        authority=EvidenceAuthority.PRIMARY_DERIVED,
        standing=EvidenceStanding.CLAIMED,
        source="Cardano ledger",
        path=(
            ProjectedIssuance(
                horizon="1 year",
                issuance=1_000.0,
                unit="ADA",
                share_of_emitted=0.01,
                rule_version="ada-reserve-draw/1",
            ),
        ),
    )


class _Issuance:
    """A declared issuance door. Returns what it was handed and nothing else."""

    def __init__(self, rule: MechanicalIssuance | None) -> None:
        self._rule = rule

    def rule(self, symbol: str) -> MechanicalIssuance | None:
        return self._rule


def _poison_issuance_cache(mutability: RuleMutability) -> None:
    """Put a tempting, contradictory rule where the ambient door looks.

    Written through the real cache so the bait is genuinely readable —
    a stub that merely looked like a cache would prove nothing.
    """

    JsonCache(evidence_path("cache", "issuance_rules"), schema=ISSUANCE_SCHEMA).write(
        "ADA", {"rule": encode_rule(_rule(mutability))}
    )


# ── 1, 2, 8. a poisoned cache cannot reach a declared committee ─────


def test_a_poisoned_cache_cannot_alter_a_fixture_backed_verdict() -> None:
    """The measured failure, run in both directions.

    The ambient cache says `protocol_fixed`, which would answer
    `consensus_bound`. The declared evidence says `governance_parameter`.
    The declared evidence wins completely.
    """

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    declared = SupplyGovernanceCommittee(
        issuance=_Issuance(_rule(RuleMutability.GOVERNANCE_PARAMETER))  # type: ignore[arg-type]
    )

    judgment = asyncio.run(declared.judge("ADA"))

    assert judgment.state is JudgmentState.JUDGED
    assert judgment.verdict is SupplyVerdict.GOVERNANCE_SET

    # And the bait was genuinely readable — otherwise this proves
    # nothing about the boundary.
    stored = CachedIssuanceRuleProvider.stored().rule("ADA")

    assert stored is not None
    assert stored.mutability is RuleMutability.PROTOCOL_FIXED


def test_the_stored_path_deliberately_selected_does_participate() -> None:
    """The inverse. The guarantee is *declared wins*, not *nothing works*.

    Production legitimately reads acquired evidence, and that dependency
    is explicit in the execution path rather than discovered.
    """

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    committee = SupplyGovernanceCommittee(issuance=CachedIssuanceRuleProvider.stored())

    judgment = asyncio.run(committee.judge("ADA"))

    assert judgment.verdict is SupplyVerdict.CONSENSUS_BOUND


def test_a_committee_given_no_evidence_says_so_rather_than_discovering_some() -> None:
    """An empty declared door produces an abstention, not a hunt."""

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    committee = SupplyGovernanceCommittee(issuance=_Issuance(None))  # type: ignore[arg-type]

    judgment = asyncio.run(committee.judge("ADA"))

    assert judgment.state is JudgmentState.ABSTAINED
    assert judgment.verdict is None


# ── 9. the same for Investor Assessment ─────────────────────────────


def _picture(*values: float) -> SupplyPicture:
    return SupplyPicture(
        symbol="ETH",
        facts=tuple(
            SupplyFact(
                concept=SupplyConcept.CIRCULATING_ESTIMATE,
                methodology=SupplyMethodology(
                    key="undisclosed",
                    defined_by=f"source-{index}",
                    stated="publishes a figure and not its exclusions",
                    disclosed=False,
                ),
                value=value,
                unit="tokens",
                authority=EvidenceAuthority.SECONDARY_AGGREGATE,
                standing=EvidenceStanding.CLAIMED,
                source=f"source-{index}",
                observed_at=NOW,
                reported_as="circulating supply",
            )
            for index, value in enumerate(values, start=1)
        ),
        comparisons=(),
        unresolved=(),
    )


class _Supply:
    def __init__(self, picture: SupplyPicture | None) -> None:
        self._picture = picture

    def established(self, symbol: str, asset_class: AssetClass) -> SupplyPicture | None:
        return self._picture


def test_a_poisoned_cache_cannot_alter_a_fixture_backed_assessment(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """The assessment answers from what it was given, whatever is on disk."""

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    # A judgment store the assessment could otherwise wander into.
    ambient = JudgmentHistoryService(
        store=JudgmentHistoryStore(root=evidence_path("judgments"))
    )

    ambient.record(
        CommitteeJudgment(
            asset="ETH",
            contract=FEE_CAPTURE,
            state=JudgmentState.JUDGED,
            basis=ApplicabilityBasis(Applicability.APPLICABLE, "ambient"),
            verdict=FeeVerdict.MECHANISM_EVIDENCED,
            refs=("F.1",),
            judged_at=NOW,
        ),
        (),
        now=NOW,
    )

    declared = InvestorAssessmentService(
        supply=_Supply(_picture(120_682_057.0)),  # type: ignore[arg-type]
        matrix=CommitteeMatrixService(
            history=JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))
        ),
    )

    assessment = declared.for_asset("ETH")

    statement = assessment.about("Circulating supply")

    assert statement is not None
    assert statement.shape is StatementShape.PRECISE

    # The ambient judgment is readable and did not reach the answer.
    assert ambient.history("ETH", FEE_CAPTURE.key)
    assert assessment.about("Value Capture") is None


# ── 4. the ETH regression, from committed fixtures ──────────────────


def test_eth_reproduces_from_committed_fixtures(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The fifth occurrence, turned into a regression.

    Every input is declared here, so this reproduces identically on a
    clean checkout and on a developer machine with a full cache.
    """

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    history.record(
        CommitteeJudgment(
            asset="ETH",
            contract=FEE_CAPTURE,
            state=JudgmentState.JUDGED,
            basis=ApplicabilityBasis(Applicability.APPLICABLE, "fixture"),
            verdict=FeeVerdict.MECHANISM_EVIDENCED,
            refs=("H.ethereum",),
            because=(
                "Users paid fees over a day, and value reached token holders "
                "via the stated mechanism: amount of ETH burned."
            ),
            judged_at=NOW,
        ),
        (),
        now=NOW,
    )

    history.record(
        CommitteeJudgment(
            asset="ETH",
            contract=SUPPLY_GOVERNANCE,
            state=JudgmentState.ABSTAINED,
            basis=ApplicabilityBasis(Applicability.APPLICABLE, "fixture"),
            abstained_because=None,
            because="No mechanical issuance rule is held for this asset.",
            judged_at=NOW,
        ),
        (),
        now=NOW,
    )

    assessment = InvestorAssessmentService(
        supply=_Supply(  # type: ignore[arg-type]
            _picture(120_682_057.5739018, 120_682_057.5739018, 120_682_072.0)
        ),
        matrix=CommitteeMatrixService(history=history),
    ).for_asset("ETH")

    # Circulating supply, from its available observations.
    circulating = assessment.about("Circulating supply")

    assert circulating is not None
    assert circulating.shape is StatementShape.PRECISE
    assert len(circulating.observed) == 3

    # Fee Capture's burn mechanism, where supplied.
    fees = assessment.about("Value Capture")

    assert fees is not None
    assert fees.shape is StatementShape.STRUCTURAL
    assert "burned" in (fees.qualification or "")

    # Supply Governance stays unresolved for its own remit.
    supply = assessment.about("Supply Governance")

    assert supply is not None
    assert supply.shape is StatementShape.INSUFFICIENT
    assert not supply.is_useful

    # Maximum supply remains unknown under the current evidence model.
    assert assessment.about("Maximum supply") is None
    assert "Maximum supply" in assessment.silent_about


# ── the root itself ─────────────────────────────────────────────────


def test_the_suite_never_points_at_the_repositorys_own_evidence() -> None:
    """The guard that makes every test above possible.

    If this ever fails, the whole class of failure is back: analytical
    tests would again be reading whatever the developer acquired.
    """

    root = evidence_root()

    assert root.is_absolute()
    assert Path("data").resolve() not in (root, *root.parents)


def test_writing_evidence_under_test_never_touches_the_repository() -> None:
    """The half that was missed for longest.

    Running the suite was observed creating `data/cache/fx` in the
    developer's own tree — tests were mutating the state they were
    accidentally reading.
    """

    _poison_issuance_cache(RuleMutability.PROTOCOL_FIXED)

    written = evidence_path("cache", "issuance_rules")

    assert written.exists()
    assert Path("data").resolve() not in written.resolve().parents


def test_every_store_resolves_its_root_at_construction() -> None:
    """A root captured at import would ignore every later redirection.

    Ruff caught this as `B008` on three stores, and it is the same class
    of bug as the one being fixed: a value frozen once and silently
    reused everywhere.
    """

    import os

    original = os.environ[ROOT_ENV]

    try:
        os.environ[ROOT_ENV] = str(Path(original) / "moved")

        assert (
            JudgmentHistoryStore()
            .path_for("ADA")
            .is_relative_to(Path(original) / "moved")
        )
    finally:
        os.environ[ROOT_ENV] = original


def test_no_module_names_an_evidence_directory_of_its_own() -> None:
    """One owner for the root, enforced over the source.

    Seventeen modules used to name their own path. Each was correct in
    production and an undeclared input everywhere else, and a
    seventeen-way redirection is not a boundary. Docstrings are exempt:
    describing the layout is not depending on it.
    """

    import ast

    root = Path(__file__).resolve().parent.parent

    offenders: list[tuple[str, str]] = []

    for module in sorted((root / "app").rglob("*.py")):
        if module.name == "evidence_root.py":
            continue

        tree = ast.parse(module.read_text(encoding="utf-8"))

        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(
                node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
            )
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        }

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue

            if not isinstance(node.value, str) or id(node) in docstrings:
                continue

            if node.value.startswith(("data/cache", "data/journal", "data/judgments")):
                offenders.append((str(module.relative_to(root)), node.value))

    assert not offenders, offenders


def test_a_json_cache_configured_by_hand_is_unaffected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Redirection is a default, never an override of an explicit path."""

    cache = JsonCache(tmp_path / "somewhere", schema=1)

    cache.write("ADA", {"rule": None})

    assert (tmp_path / "somewhere").exists()
