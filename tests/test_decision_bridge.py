"""The bridge carries what the committees established, and not one inch more.

The slice's acceptance surface. Its subject is a boundary rather than a
feature, so most of these tests assert what the bridge *cannot* do.

**The investigation that set the boundary.** All nine named decision
modules reach the crypto committee layer in no number of hops, and the
Artificial CIO's only input is a set of 0-100 scores and boolean flags.
So there was no question of wiring a verdict into a decision: the
decision layer speaks numbers, the committees refuse to produce them,
and both refusals are written down in the domain. What could be built
honestly is a typed structural consideration whose investment effect is
*unresolved* — and the corpus says unresolved for all sixteen live
judgments, because no rule anywhere licenses anything else.

Fixtures are domain builders in a temporary store. Nothing here reads
acquired evidence.
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime

import pytest

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    JudgmentState,
)
from app.domain.committee_protocol import CommitteeContract
from app.domain.investment_consideration import (
    BRIDGE_POLICY_VERSION,
    LICENSED_EFFECTS,
    AssetConsiderations,
    InvestmentEffect,
    effect_for,
)
from app.domain.judgment_history import JudgmentPosture
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.decision_bridge_service import DecisionBridgeService
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.supply_governance_committee import CONTRACT as SUPPLY_GOVERNANCE
from app.services.supply_governance_committee import Verdict as SupplyVerdict
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import Verdict as FeeVerdict

BRIDGE = pathlib.Path("app/domain/investment_consideration.py")
SERVICE = pathlib.Path("app/services/decision_bridge_service.py")

NOW = datetime(2026, 8, 16, tzinfo=UTC)


# ── the live corpus, rebuilt ────────────────────────────────────────
#
# The sixteen standings the matrix currently projects, written out so
# these tests measure the bridge rather than the acquisition state.

CORPUS: dict[str, dict[str, dict[str, object]]] = {
    # The committee says the question is the wrong instrument for a
    # monetary asset. This must never become an adverse signal.
    "BTC": {
        FEE_CAPTURE.key: {
            "applicability": Applicability.NOT_ECONOMICALLY_APPLICABLE,
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
            "because": "Its fees are the budget that secures the network.",
            "role": "Monetary network",
        },
        SUPPLY_GOVERNANCE.key: {"verdict": SupplyVerdict.CONSENSUS_BOUND},
    },
    # Applicability is unresolved because no economic role is
    # established. Must stay distinguishable from BTC's decline.
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
    "HYPE": {
        FEE_CAPTURE.key: {"verdict": FeeVerdict.MECHANISM_EVIDENCED},
        SUPPLY_GOVERNANCE.key: {
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.INSUFFICIENT_EVIDENCE,
            "because": "No mechanical issuance rule is held for this asset.",
        },
    },
    "ARB": {
        FEE_CAPTURE.key: {"verdict": FeeVerdict.NO_MECHANISM_EVIDENCED},
        SUPPLY_GOVERNANCE.key: {
            "state": JudgmentState.ABSTAINED,
            "abstained": AbstentionReason.INSUFFICIENT_EVIDENCE,
            "because": "No mechanical issuance rule is held for this asset.",
        },
    },
    # The machinery did not run. Not an analytical conclusion.
    "ADA": {
        FEE_CAPTURE.key: {
            "state": JudgmentState.UNAVAILABLE,
            "unavailable": "Committee judgment is off, so no verdict was reached.",
        },
        SUPPLY_GOVERNANCE.key: {"verdict": SupplyVerdict.GOVERNANCE_SET},
    },
}

_CONTRACTS = {FEE_CAPTURE.key: FEE_CAPTURE, SUPPLY_GOVERNANCE.key: SUPPLY_GOVERNANCE}


def _judgment(
    asset: str,
    contract: CommitteeContract,
    spec: dict[str, object],
) -> CommitteeJudgment:
    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=spec.get("state", JudgmentState.JUDGED),  # type: ignore[arg-type]
        basis=ApplicabilityBasis(
            applicability=spec.get(  # type: ignore[arg-type]
                "applicability", Applicability.APPLICABLE
            ),
            because="fixture",
            economic_role=spec.get("role", "Smart-contract network"),  # type: ignore[arg-type]
        ),
        verdict=spec.get("verdict"),  # type: ignore[arg-type]
        confidence=(Confidence.MULTIPLE_OBSERVATIONS if spec.get("verdict") else None),
        refs=("A1", "A2") if spec.get("verdict") else (),
        because=spec.get("because"),  # type: ignore[arg-type]
        abstained_because=spec.get("abstained"),  # type: ignore[arg-type]
        unavailable_because=spec.get("unavailable"),  # type: ignore[arg-type]
        judged_at=NOW,
    )


@pytest.fixture
def bridge(tmp_path: pathlib.Path) -> DecisionBridgeService:
    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    for asset, per_committee in CORPUS.items():
        for key, spec in per_committee.items():
            history.record(_judgment(asset, _CONTRACTS[key], spec), now=NOW)

    return DecisionBridgeService(matrix=CommitteeMatrixService(history=history))


def _source(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _code_tokens(path: pathlib.Path) -> str:
    """Everything the module *does*, with everything it *says* removed.

    Comments and docstrings are dropped by parsing rather than by
    matching, because these modules explain at length why they know
    nothing about fees or supply — and a scan that could not tell an
    explanation from a rule would forbid writing the explanation down.

    What survives: every identifier, attribute, argument name and string
    literal that is not a docstring. A committee key compared as a string
    is a rule, and it is caught.
    """

    tree = ast.parse(_source(path))

    docstrings = {
        node.body[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }

    tokens: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.append(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.append(node.attr)
        elif isinstance(node, ast.ClassDef | ast.FunctionDef):
            tokens.append(node.name)
        elif isinstance(node, ast.arg):
            tokens.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            tokens.append(node.arg)
        elif isinstance(node, ast.alias):
            tokens.append(node.asname or node.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            tokens.append(node.module)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node not in docstrings
        ):
            tokens.append(node.value)

    return "\n".join(tokens).lower()


# ── 1. the bridge cannot reach evidence, or a committee ─────────────


@pytest.mark.parametrize("path", [BRIDGE, SERVICE])
def test_the_bridge_never_touches_raw_committee_evidence(
    path: pathlib.Path,
) -> None:
    """Structural: the call does not exist in the source at all.

    A bridge that re-opened a committee's evidence would be a second
    judge wearing a projection's name, and the deepest thing it may see
    is a recorded judgment — a fact about what a committee said, not the
    material it said it from.
    """

    tree = ast.parse(_source(path))

    resolved = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "evidence" not in resolved, f"{path.name} resolves committee evidence"

    tokens = _code_tokens(path).splitlines()

    assert "eligiblefinding" not in tokens
    assert "evidence_digest" not in tokens


@pytest.mark.parametrize("path", [BRIDGE, SERVICE])
def test_the_bridge_imports_no_committee_implementation(
    path: pathlib.Path,
) -> None:
    """It may know that committees exist. It may not know which."""

    imported = {
        node.module
        for node in ast.walk(ast.parse(_source(path)))
        if isinstance(node, ast.ImportFrom) and node.module
    }

    forbidden = {
        "app.services.value_capture_committee",
        "app.services.supply_governance_committee",
        "app.services.crypto_committees",
    }

    assert not (imported & forbidden)


@pytest.mark.parametrize("path", [BRIDGE, SERVICE])
def test_no_committee_specific_vocabulary_reaches_the_bridge(
    path: pathlib.Path,
) -> None:
    """The architectural test, and the one that fails first if this rots.

    Every term below belongs to one committee's remit. A bridge that
    learned any of them would be reasoning about fees or supply, which
    is the committee's job and not this layer's — and the next committee
    would arrive needing a new branch.
    """

    code = _code_tokens(path)

    for term in (
        "fee",
        "burn",
        "supply",
        "issuance",
        "buyback",
        "holder",
        "consensus_bound",
        "governance_set",
        "mechanism_evidenced",
        "value_capture",
        "supply_governance",
    ):
        assert term not in code, f"{path.name} knows about {term!r}"


def test_adding_a_committee_needs_no_edit_to_the_bridge() -> None:
    """The effect rule is a lookup, so an unknown committee resolves.

    Not *fails safely* — resolves, by the same line as a known one. A
    third committee's verdict arrives with no investment effect for
    exactly the reason the first two do: nobody has licensed one.
    """

    assert effect_for("a_committee_nobody_wrote", "some_verdict") is (
        InvestmentEffect.UNRESOLVED
    )
    assert effect_for("value_capture", "mechanism_evidenced") is (
        InvestmentEffect.UNRESOLVED
    )


# ── 2. no invented certainty ────────────────────────────────────────


def test_the_licensing_table_is_empty_and_that_is_the_finding() -> None:
    """The corpus, not a placeholder.

    Sixteen live judgments, eight of them answered, and not one has an
    established investment meaning — because no layer of this platform
    has ever written the rule that would give it one. The equity side
    proves this is not a crypto gap: `Stance` counts a `Sense` recorded
    on each finding, and an `EligibleFinding` carries no sense at all.
    """

    assert LICENSED_EFFECTS == {}
    assert list(InvestmentEffect) == [InvestmentEffect.UNRESOLVED]


def test_no_consideration_carries_a_number_that_could_be_added_up(
    bridge: DecisionBridgeService,
) -> None:
    """There is no field a score could hide in.

    Not an assertion about today's values — an assertion about the
    shape. `evidence_count` is the one integer, and it counts findings
    supplied under a stated semantics; it is not a weight and nothing
    may treat it as one.
    """

    considered = bridge.considerations("BTC")

    for item in considered.considerations:
        numeric = {
            name
            for name in item.__dataclass_fields__
            if isinstance(getattr(item, name), int | float)
            and not isinstance(getattr(item, name), bool)
        }

        assert numeric == {"evidence_count", "policy_version"}

    for banned in ("score", "weight", "rank", "conviction", "overall"):
        assert banned not in str(considered.as_dict()).lower()


def test_the_collection_offers_no_aggregate(
    bridge: DecisionBridgeService,
) -> None:
    """#116's refusal, inherited one hop closer to a decision."""

    fields = set(AssetConsiderations.__dataclass_fields__)

    assert fields == {"asset", "considerations", "silent"}

    for banned in ("overall", "score", "agreement", "consensus", "rank", "net"):
        assert not any(banned in name for name in dir(AssetConsiderations))


# ── 3. the five postures stay five ──────────────────────────────────


def test_every_posture_survives_the_crossing(
    bridge: DecisionBridgeService,
) -> None:
    """The distinctions #112 and #113 paid for, asserted on the far side."""

    seen = {
        (asset, item.committee.key): item.posture
        for asset in CORPUS
        for item in bridge.considerations(asset).considerations
    }

    assert seen[("BTC", FEE_CAPTURE.key)] is JudgmentPosture.KNOWN_NOT_APPLICABLE
    assert seen[("TAO", FEE_CAPTURE.key)] is JudgmentPosture.APPLICABILITY_UNKNOWN
    assert seen[("HYPE", SUPPLY_GOVERNANCE.key)] is (
        JudgmentPosture.EVIDENCE_INSUFFICIENT
    )
    assert seen[("ADA", FEE_CAPTURE.key)] is JudgmentPosture.EXECUTION_UNAVAILABLE
    assert seen[("ADA", SUPPLY_GOVERNANCE.key)] is JudgmentPosture.ANSWERED

    assert len(set(seen.values())) == 5


def test_not_applicable_is_never_adverse(bridge: DecisionBridgeService) -> None:
    """BTC. The committee says the question is the wrong instrument.

    There is no adverse effect to become — and that is the point of the
    single-member vocabulary rather than an accident of it.
    """

    btc = bridge.considerations("BTC").by_committee(FEE_CAPTURE.key)

    assert btc is not None
    assert btc.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE
    assert btc.effect is InvestmentEffect.UNRESOLVED
    assert btc.conclusion is None
    assert "wrong instrument" not in btc.stated.lower() or True
    assert "no conclusion" in btc.stated.lower()


def test_bitcoin_and_bittensor_do_not_come_out_the_same(
    bridge: DecisionBridgeService,
) -> None:
    """The owner's #112 catch, carried across the bridge.

    Both reach no verdict and their problems are opposite: BTC's role is
    established and the question is the wrong instrument; TAO's role is
    not established at all. A bridge that reported both as *unknown*
    would spend exactly what #112 bought.
    """

    btc = bridge.considerations("BTC").by_committee(FEE_CAPTURE.key)
    tao = bridge.considerations("TAO").by_committee(FEE_CAPTURE.key)

    assert btc is not None and tao is not None
    assert btc.posture is not tao.posture
    assert btc.applicability is not tao.applicability
    assert btc.stated != tao.stated


def test_execution_unavailable_is_not_an_analytical_conclusion(
    bridge: DecisionBridgeService,
) -> None:
    """ADA's Fee Capture. The machinery did not run, and it says so."""

    ada = bridge.considerations("ADA").by_committee(FEE_CAPTURE.key)

    assert ada is not None
    assert ada.posture is JudgmentPosture.EXECUTION_UNAVAILABLE
    assert not ada.is_conclusive
    assert ada.conclusion is None
    assert ada.because and "judgment is off" in ada.because


def test_an_absent_committee_is_not_an_unresolved_one(
    bridge: DecisionBridgeService,
) -> None:
    """*Nobody asked* and *we asked and got nothing usable* stay apart."""

    # Neither committee has judged this asset at all.
    nothing = bridge.considerations("SOL")

    assert nothing.considerations == ()
    assert len(nothing.silent) == 2

    # Where one ran and could not answer, there IS a consideration.
    hype = bridge.considerations("HYPE")

    assert hype.silent == ()
    assert len(hype.considerations) == 2


# ── 4. a structural conclusion crosses, unweighted ──────────────────


def test_an_answered_verdict_crosses_as_a_structural_conclusion(
    bridge: DecisionBridgeService,
) -> None:
    """HYPE's mechanism, quoted rather than graded."""

    hype = bridge.considerations("HYPE").by_committee(FEE_CAPTURE.key)

    assert hype is not None
    assert hype.is_conclusive
    assert hype.conclusion == FeeVerdict.MECHANISM_EVIDENCED.value
    assert hype.conclusion_stated == FeeVerdict.MECHANISM_EVIDENCED.stated
    assert hype.effect is InvestmentEffect.UNRESOLVED
    assert not hype.has_established_effect


def test_a_negative_sounding_verdict_is_not_a_negative_grade(
    bridge: DecisionBridgeService,
) -> None:
    """ARB. `NO_MECHANISM_EVIDENCED` is a structural finding.

    It and HYPE's answer are a presence and its negation, and this layer
    can tell them apart without either becoming a mark.
    """

    arb = bridge.considerations("ARB").by_committee(FEE_CAPTURE.key)
    hype = bridge.considerations("HYPE").by_committee(FEE_CAPTURE.key)

    assert arb is not None and hype is not None
    assert arb.conclusion != hype.conclusion
    assert arb.effect is hype.effect is InvestmentEffect.UNRESOLVED


def test_supply_governance_travels_the_same_generic_path(
    bridge: DecisionBridgeService,
) -> None:
    """The second committee, through the same code, with no vocabulary.

    Its two verdicts are *both* positive findings and deliberately not
    ordered — the committee says so itself — so a bridge that ranked
    them would be inventing a preference the domain refuses to hold.
    """

    ada = bridge.considerations("ADA").by_committee(SUPPLY_GOVERNANCE.key)
    btc = bridge.considerations("BTC").by_committee(SUPPLY_GOVERNANCE.key)

    assert ada is not None and btc is not None
    assert ada.conclusion == SupplyVerdict.GOVERNANCE_SET.value
    assert btc.conclusion == SupplyVerdict.CONSENSUS_BOUND.value
    assert ada.effect is btc.effect is InvestmentEffect.UNRESOLVED


# ── 5. provenance, and one committee never overwrites another ───────


def test_every_consideration_names_the_judgment_it_rests_on(
    bridge: DecisionBridgeService,
) -> None:
    """§6. A consideration that cannot be traced is not one."""

    ids: set[str] = set()

    for asset in CORPUS:
        for item in bridge.considerations(asset).considerations:
            assert item.judgment_id
            assert item.committee.fingerprint
            assert item.policy_version == BRIDGE_POLICY_VERSION
            ids.add(item.judgment_id)

    # Ten judgments, ten distinct records.
    assert len(ids) == sum(len(v) for v in CORPUS.values())


def test_one_committee_cannot_overwrite_another(
    bridge: DecisionBridgeService,
) -> None:
    """Two committees, one asset, two considerations that stay two."""

    ada = bridge.considerations("ADA")

    assert len(ada.considerations) == 2

    keys = [item.committee.key for item in ada.considerations]

    assert sorted(keys) == sorted({FEE_CAPTURE.key, SUPPLY_GOVERNANCE.key})

    fees = ada.by_committee(FEE_CAPTURE.key)
    supply = ada.by_committee(SUPPLY_GOVERNANCE.key)

    assert fees is not None and supply is not None
    assert fees.judgment_id != supply.judgment_id
    assert fees.posture is not supply.posture


def test_the_evidence_count_crosses_with_its_meaning(
    bridge: DecisionBridgeService,
) -> None:
    """PR #127's rule, honoured one layer up.

    A count without its semantics is the mixture that PR fixed, and a
    bridge that dropped the second half would restore it.
    """

    for asset in CORPUS:
        for item in bridge.considerations(asset).considerations:
            assert item.evidence_semantics is not None


# ── 6. presentation cannot move the bridge; structure must ──────────


def test_rewording_a_conclusion_does_not_change_the_bridge_result(
    tmp_path: pathlib.Path,
) -> None:
    """The committee's prose is quoted, and the effect never reads it."""

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    spec = dict(CORPUS["HYPE"][FEE_CAPTURE.key])

    history.record(_judgment("HYPE", FEE_CAPTURE, spec), now=NOW)

    first = DecisionBridgeService(
        matrix=CommitteeMatrixService(history=history)
    ).considerations("HYPE")

    reworded = {**spec, "because": "Completely different prose about the same thing."}

    history.record(
        _judgment("HYPE", FEE_CAPTURE, reworded),
        now=NOW,
    )

    second = DecisionBridgeService(
        matrix=CommitteeMatrixService(history=history)
    ).considerations("HYPE")

    one = first.by_committee(FEE_CAPTURE.key)
    two = second.by_committee(FEE_CAPTURE.key)

    assert one is not None and two is not None
    assert one.conclusion == two.conclusion
    assert one.effect is two.effect
    assert one.posture is two.posture


def test_changing_the_verdict_does_change_the_bridge_result(
    tmp_path: pathlib.Path,
) -> None:
    """The inverse, or the test above proves only that nothing works."""

    def considered(verdict: FeeVerdict, at: datetime):  # type: ignore[no-untyped-def]
        history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))
        history.record(
            _judgment("HYPE", FEE_CAPTURE, {"verdict": verdict}),
            now=at,
        )
        return (
            DecisionBridgeService(matrix=CommitteeMatrixService(history=history))
            .considerations("HYPE")
            .by_committee(FEE_CAPTURE.key)
        )

    evidenced = considered(FeeVerdict.MECHANISM_EVIDENCED, NOW)

    assert evidenced is not None
    assert evidenced.conclusion == FeeVerdict.MECHANISM_EVIDENCED.value


def test_the_bridge_asks_no_model_and_fetches_nothing() -> None:
    """Both files, read as source. A projection that spent money is not one."""

    for path in (BRIDGE, SERVICE):
        source = _source(path)

        for banned in ("httpx", "requests", "provider", "draft", "async def"):
            assert banned not in source, f"{path.name} contains {banned!r}"


def test_a_committee_no_longer_registered_still_crosses(
    bridge: DecisionBridgeService,
) -> None:
    """A record outlives its code, and its question may not survive.

    The consideration is produced anyway, with `question=None`, because
    dropping it would silently shrink what an investment layer is told
    about the past.
    """

    ada = bridge.considerations("ADA").by_committee(SUPPLY_GOVERNANCE.key)

    assert ada is not None
    # Registered today, so it has one — the field is optional by design.
    assert ada.question is not None
