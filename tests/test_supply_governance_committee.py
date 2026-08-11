"""The second committee: who can change the rule you are holding.

Committee #2 was **selected by measurement**, and the measurement is
part of the test surface: the corpus must actually produce more than one
answer state, or the committee is a taxonomy with one occupant.

No test asserts that a consensus-bound rule is better than a
governance-set one. The two verdicts are both positive findings and the
committee has no view on which an investor should prefer — S5.3 measured
that the protocol-fixed asset expands least *and* parked magnitude
outside quality, so the ranking a reader might expect is exactly the one
this platform has refused twice.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    JudgmentState,
)
from app.domain.committee_protocol import Committee
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.mechanical_issuance import (
    IssuanceMechanism,
    IssuanceState,
    MechanicalIssuance,
    ProjectedIssuance,
    RuleMutability,
    RuleParameter,
)
from app.domain.supply_semantics import PrimaryProvenance
from app.services.supply_governance_committee import (
    CONTRACT,
    SupplyGovernanceCommittee,
    Verdict,
    _cannot_answer,
)
from tests.reachability import reachable

NOW = datetime(2026, 8, 11, tzinfo=UTC)

CORPUS = ("BTC", "ETH", "SOL", "ADA", "HYPE", "ARB", "1INCH", "TAO")


# ── fixtures ────────────────────────────────────────────────────────


def _rule(
    *,
    symbol: str = "ADA",
    mutability: RuleMutability = RuleMutability.GOVERNANCE_PARAMETER,
    authority: EvidenceAuthority = EvidenceAuthority.PRIMARY_DERIVED,
    parameters: tuple[RuleParameter, ...] | None = None,
    canonical: bool = True,
    rule_version: str = "ada-reserve-draw/1",
    projectable: bool = True,
) -> MechanicalIssuance:
    return MechanicalIssuance(
        symbol=symbol,
        mechanism=IssuanceMechanism.RESERVE_DRAW,
        state=IssuanceState(unit="ADA", position="epoch 500", observed_at=NOW),
        formula="reserves * rho each epoch",
        parameters=parameters
        if parameters is not None
        else (
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
            surface_is_canonical=canonical,
            identity_because="the chain endpoint is the asset",
            rule_version=rule_version,
            formula="reserves * rho",
        ),
        authority=authority,
        standing=EvidenceStanding.CLAIMED,
        source="Cardano ledger",
        path=(
            ProjectedIssuance(
                horizon="1 year",
                issuance=1_000.0,
                unit="ADA",
                share_of_emitted=0.01,
                rule_version=rule_version,
            ),
        )
        if projectable
        else (),
    )


class _Issuance:
    """A stored issuance door that returns whatever it was handed."""

    def __init__(self, rules: dict[str, MechanicalIssuance] | None = None) -> None:
        self._rules = rules or {}

    def rule(self, symbol: str) -> MechanicalIssuance | None:
        return self._rules.get(symbol.upper().strip())


def _committee(rules: dict[str, MechanicalIssuance] | None = None):  # type: ignore[no-untyped-def]
    return SupplyGovernanceCommittee(issuance=_Issuance(rules))  # type: ignore[arg-type]


# ── the protocol ────────────────────────────────────────────────────


def test_the_committee_satisfies_the_protocol() -> None:
    assert isinstance(_committee(), Committee)
    assert CONTRACT.key == "supply_governance"
    assert CONTRACT.verdicts == tuple(verdict.value for verdict in Verdict)


def test_the_verdicts_are_this_committees_own_and_not_fee_captures() -> None:
    """Similar-looking binaries are not a reason to share a vocabulary.

    Fee Capture answers a presence and its negation. These two are both
    presences — every asset reaching a verdict here *has* a rule — so
    reusing that vocabulary would have said something false about what
    the answer means.
    """

    from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE

    assert not set(CONTRACT.verdicts) & set(FEE_CAPTURE.verdicts)
    assert CONTRACT.fingerprint != FEE_CAPTURE.fingerprint

    # Neither verdict is ordered against the other, and nothing offers a
    # way to ask which is better.
    for name in ("rank", "score", "polarity", "is_favourable", "weight"):
        assert not hasattr(Verdict.CONSENSUS_BOUND, name), name


# ── applicability, and the cross with Fee Capture ───────────────────


def test_applicability_splits_the_corpus_differently_from_fee_capture() -> None:
    """The independence test that matters, run against the live corpus.

    Fee Capture declines BTC and asks 1INCH; this committee asks BTC and
    declines 1INCH. If the two split the corpus the same way, the second
    committee would be a second view of the first wearing new words.
    """

    from app.services.value_capture_committee import ValueCaptureCommittee

    mine = _committee()
    theirs = ValueCaptureCommittee()

    assert mine.basis("BTC").applicability is Applicability.APPLICABLE
    assert theirs.basis("BTC").applicability is (
        Applicability.NOT_ECONOMICALLY_APPLICABLE
    )

    assert mine.basis("1INCH").applicability is (
        Applicability.NOT_ECONOMICALLY_APPLICABLE
    )
    assert theirs.basis("1INCH").applicability is Applicability.APPLICABLE

    # And an unestablished role is unestablished for both — the one
    # place they agree, because neither can invent a role.
    assert mine.basis("TAO").applicability is Applicability.UNESTABLISHED
    assert theirs.basis("TAO").applicability is Applicability.UNESTABLISHED


def test_an_asset_that_is_several_things_is_asked_if_any_of_them_issues() -> None:
    """Hyperliquid runs its own chain, so it is asked despite being a venue."""

    basis = _committee().basis("HYPE")

    assert basis.applicability is Applicability.APPLICABLE
    assert basis.economic_role


def test_a_declined_asset_is_not_judged_adversely() -> None:
    """1INCH is not answered, and the wording refuses the reading."""

    judgment = asyncio.run(_committee().judge("1INCH"))

    assert judgment.state is JudgmentState.ABSTAINED
    assert judgment.abstained_because is (AbstentionReason.NOT_ECONOMICALLY_APPLICABLE)
    assert judgment.verdict is None
    assert "rather than answered adversely" in (judgment.because or "")


# ── the verdicts ────────────────────────────────────────────────────


def test_a_protocol_fixed_rule_is_consensus_bound() -> None:
    rule = _rule(symbol="BTC", mutability=RuleMutability.PROTOCOL_FIXED)

    judgment = asyncio.run(_committee({"BTC": rule}).judge("BTC"))

    assert judgment.state is JudgmentState.JUDGED
    assert judgment.verdict is Verdict.CONSENSUS_BOUND
    assert judgment.refs


def test_a_governance_parameter_rule_is_governance_set() -> None:
    judgment = asyncio.run(_committee({"ADA": _rule()}).judge("ADA"))

    assert judgment.state is JudgmentState.JUDGED
    assert judgment.verdict is Verdict.GOVERNANCE_SET


def test_more_evidence_cannot_move_the_verdict() -> None:
    """The verdict is a function of mutability alone. §7, restated here.

    It also records a limitation found by measurement rather than
    designed for: **the inherited `Confidence` vocabulary saturates for
    this committee.** Every answered asset emits at least a mechanism, a
    formula, a parameter, a mutability and a projection, so all three of
    BTC's 8, SOL's 9 and ADA's 11 findings land on
    `MULTIPLE_OBSERVATIONS`. The count is honest and the band is blind
    to it — a framework vocabulary calibrated on Fee Capture's evidence
    shape, carried unchanged onto a committee whose evidence has a
    different shape. Reported as a finding; not repaired here, because
    repairing it means deciding what a second band would *mean* and no
    committee has earned that.
    """

    thin = _rule()
    thick = _rule(
        parameters=(
            *thin.parameters,
            RuleParameter(
                name="tau",
                value=0.2,
                unit="proportion",
                read_from="cardano ledger /genesis",
                means="the treasury share",
            ),
            RuleParameter(
                name="epoch",
                value=432_000,
                unit="seconds",
                read_from="cardano ledger /tip",
                means="the epoch length",
            ),
        )
    )

    lean = asyncio.run(_committee({"ADA": thin}).judge("ADA"))
    full = asyncio.run(_committee({"ADA": thick}).judge("ADA"))

    assert lean.verdict is full.verdict
    assert len(full.refs) > len(lean.refs)

    # The measured limitation: three times the evidence, same band.
    assert lean.confidence is full.confidence


# ── the eligibility rule ────────────────────────────────────────────


def test_every_clause_of_the_eligibility_rule_refuses_its_own_failure() -> None:
    """Each clause names one way an answer would outrun its evidence."""

    assert _cannot_answer(_rule()) is None

    refusals = {
        "primary surface": _rule(authority=EvidenceAuthority.SECONDARY_AGGREGATE),
        "only its operator computed": _rule(canonical=False),
        "nothing to re-run": _rule(parameters=()),
        "names no surface": _rule(
            parameters=(
                RuleParameter(
                    name="rho", value=0.003, unit="p", read_from="", means="x"
                ),
            )
        ),
        "names no rule version": _rule(rule_version=""),
        "does not re-run": _rule(projectable=False),
        "what it would take to change it is not established": _rule(
            mutability=RuleMutability.UNKNOWN
        ),
    }

    for expected, rule in refusals.items():
        refusal = _cannot_answer(rule)

        assert refusal is not None, expected
        assert expected in refusal, (expected, refusal)


def test_the_eligibility_rule_does_not_read_evidence_standing() -> None:
    """The measured finding, guarded so it cannot be quietly reinstated.

    Every issuance rule on this platform stands at `CLAIMED`, because
    S1's corroboration vocabulary was built for vendor claims and a
    chain's own parameters have no second source. Requiring
    `ESTABLISHED` here made the committee silent about all three of its
    answerable assets — so the gate is Model C's, on the authority axis,
    and this test is why it cannot drift back.
    """

    claimed = _rule()

    assert claimed.standing is EvidenceStanding.CLAIMED
    assert _cannot_answer(claimed) is None

    code = reachable("app/services/supply_governance_committee.py")

    assert "EvidenceStanding" not in code


def test_no_mechanical_rule_held_is_an_abstention_not_a_verdict() -> None:
    """An absence is never an answer, and it names what it is about."""

    judgment = asyncio.run(_committee().judge("ADA"))

    assert judgment.state is JudgmentState.ABSTAINED
    assert judgment.abstained_because is AbstentionReason.INSUFFICIENT_EVIDENCE
    assert "not about what the protocol does" in (judgment.because or "")


# ── independence from Fee Capture ───────────────────────────────────


def test_neither_committee_can_see_the_others_verdict() -> None:
    """Independence is structural: neither module reaches the other."""

    mine = reachable("app/services/supply_governance_committee.py")
    theirs = reachable("app/services/value_capture_committee.py")

    assert "value_capture_committee" not in mine
    assert "supply_governance_committee" not in theirs

    # And neither can name the other's answers.
    from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE

    for token in FEE_CAPTURE.verdicts:
        assert token not in mine, token

    for token in CONTRACT.verdicts:
        assert token not in theirs, token


def test_this_committee_never_reads_a_vendor_supply_figure() -> None:
    """Measured exclusion, not a stylistic one.

    A vendor's `total_supply` is the protocol maximum for 83 of 145
    capped assets (S5), which puts Cardano at 100% emitted where its own
    ledger says 86.2%. A committee reasoning from that would be
    confidently wrong about the quantity it exists to describe.
    """

    code = reachable("app/services/supply_governance_committee.py")

    for forbidden in ("supply_semantics_service", "SupplyConcept", "coingecko"):
        assert forbidden not in code, forbidden


# ── the corpus actually produces contrast ───────────────────────────


def test_the_corpus_shape_produces_more_than_one_answer_state() -> None:
    """The selection criterion, asserted from the corpus's real shapes.

    A committee whose corpus yields one answer is a taxonomy with one
    occupant, so this is the criterion that chose the question and it is
    checked rather than claimed.

    **Built from fixtures reproducing the live readings, not from the
    cache.** The first draft read the acquired issuance store and passed
    here while failing on a clean checkout — the S3 trap, on its fourth
    outing. What the corpus holds is measured in the architecture note
    and is data; what the committee does with those shapes is code, and
    only the second belongs in a test.
    """

    committee = _committee(
        {
            # The three rules the corpus actually carries, in their real
            # mutabilities.
            "BTC": _rule(symbol="BTC", mutability=RuleMutability.PROTOCOL_FIXED),
            "ADA": _rule(symbol="ADA"),
            "SOL": _rule(symbol="SOL"),
        }
    )

    outcomes = {asset: asyncio.run(committee.judge(asset)) for asset in CORPUS}

    verdicts = {judgment.verdict for judgment in outcomes.values() if judgment.verdict}

    assert verdicts == {Verdict.CONSENSUS_BOUND, Verdict.GOVERNANCE_SET}

    # And the abstentions are differentiated rather than one silence:
    # the question does not apply, the role is unestablished, and the
    # evidence cannot answer are three different findings.
    reasons = {
        judgment.abstained_because
        for judgment in outcomes.values()
        if judgment.abstained_because
    }

    assert reasons == {
        AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
        AbstentionReason.APPLICABILITY_UNESTABLISHED,
        AbstentionReason.INSUFFICIENT_EVIDENCE,
    }
