"""The strongest useful statement, and the things it refuses to invent.

The slice's acceptance surface. Every test builds its own evidence and
its own judgment records — **nothing reads the acquired stores**, which
is the fourth time this repository has had to say so.

The layer's whole job is to be as strong as the evidence and no
stronger, in both directions: it must not manufacture a canonical figure
to make a disagreement go away, and it must not refuse to speak because
one part of what it holds is unresolved.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
)
from app.domain.crypto_archetype import (
    ArchetypeAssignment,
    ArchetypeConfidence,
    TokenArchetype,
)
from app.domain.crypto_questions import QUESTIONS
from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.investor_assessment import (
    InvestorAssessment,
    InvestorStatement,
    StatementShape,
)
from app.domain.supply_semantics import (
    SupplyConcept,
    SupplyFact,
    SupplyMethodology,
    SupplyPicture,
)
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.investor_assessment_service import InvestorAssessmentService
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.supply_governance_committee import CONTRACT as SUPPLY_GOVERNANCE
from app.services.supply_governance_committee import Verdict as SupplyVerdict
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import Verdict as FeeVerdict
from tests.reachability import reachable

NOW = datetime(2026, 8, 11, tzinfo=UTC)

_UNDISCLOSED = SupplyMethodology(
    key="undisclosed",
    defined_by="vendor",
    stated="publishes a figure and not the balances it excludes",
    disclosed=False,
)


def _fact(concept: SupplyConcept, value: float, source: str) -> SupplyFact:
    return SupplyFact(
        concept=concept,
        methodology=_UNDISCLOSED,
        value=value,
        unit="tokens",
        authority=EvidenceAuthority.SECONDARY_AGGREGATE,
        standing=EvidenceStanding.CLAIMED,
        source=source,
        observed_at=NOW,
        reported_as=concept.value,
    )


class _Supply:
    """A stored supply door that returns whatever it was handed."""

    def __init__(self, facts: tuple[SupplyFact, ...] = ()) -> None:
        self._picture = (
            SupplyPicture(symbol="XYZ", facts=facts, comparisons=(), unresolved=())
            if facts
            else None
        )

    def established(self, symbol: str, asset_class: object) -> SupplyPicture | None:
        return self._picture


def _service(  # type: ignore[no-untyped-def]
    tmp_path,
    facts: tuple[SupplyFact, ...] = (),
    judgments: tuple[CommitteeJudgment, ...] = (),
):
    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    for judgment in judgments:
        history.record(judgment, now=NOW)

    return InvestorAssessmentService(
        supply=_Supply(facts),  # type: ignore[arg-type]
        matrix=CommitteeMatrixService(history=history),
    )


def _judgment(  # type: ignore[no-untyped-def]
    contract=FEE_CAPTURE,
    *,
    asset: str = "XYZ",
    state: JudgmentState = JudgmentState.JUDGED,
    verdict: object = None,
    applicability: Applicability = Applicability.APPLICABLE,
    abstained: AbstentionReason | None = None,
    because: str | None = None,
    unavailable: str | None = None,
    wording_refused: str | None = None,
) -> CommitteeJudgment:
    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=state,
        basis=ApplicabilityBasis(applicability, "fixture", "Smart-contract network"),
        verdict=verdict,  # type: ignore[arg-type]
        confidence=Confidence.MULTIPLE_OBSERVATIONS if verdict else None,
        refs=("F.1",) if verdict else (),
        because=because,
        abstained_because=abstained,
        unavailable_because=unavailable,
        wording_refused=wording_refused,
        judged_at=NOW,
    )


# ── 1 & 2. differing numbers become a bound, never an invention ─────


def test_two_differing_observations_produce_a_range(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The ruling's own example, run against the layer.

    Two credible estimates 9.9% apart bound the answer. The useful
    statement is the bound.
    """

    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 8_644_817, "TokenInsight"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 9_597_491, "CoinGecko"),
        ),
    )

    statement = service.for_asset("XYZ").about("Circulating supply")

    assert statement is not None
    assert statement.shape is StatementShape.RANGE
    assert "8.64 million to 9.60 million" in statement.stated
    assert "approximately" in statement.stated

    # Both readings survive, with their sources.
    assert {value.source for value in statement.observed} == {
        "TokenInsight",
        "CoinGecko",
    }


def test_no_canonical_figure_is_ever_invented(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A midpoint is a number nobody published. Invariant 1, restated."""

    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 480_000_000, "A"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 530_000_000, "B"),
        ),
    )

    statement = service.for_asset("XYZ").about("Circulating supply")

    assert statement is not None
    assert statement.shape is StatementShape.RANGE

    # The midpoint appears nowhere — not in the sentence, not in the
    # readings, not anywhere a surface could pick it up.
    for forbidden in ("505", "505,000,000", "505.00"):
        assert forbidden not in statement.stated

    assert {value.value for value in statement.observed} == {
        480_000_000.0,
        530_000_000.0,
    }

    # And the layer offers no way to compute one.
    for name in dir(InvestorStatement):
        assert "mean" not in name.lower()
        assert "average" not in name.lower()
        assert "midpoint" not in name.lower()


def test_a_material_spread_is_uncertain_rather_than_a_bound(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A difference becomes investor-relevant when it changes what can be said.

    Hyperliquid's estimates span 78% and one exceeds the maximum. A
    range there would imply the answer lies inside it, which this
    platform cannot establish.
    """

    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 336_685_219, "TokenInsight"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 1_500_000_000, "Yahoo Finance"),
        ),
    )

    statement = service.for_asset("XYZ").about("Circulating supply")

    assert statement is not None
    assert statement.shape is StatementShape.UNCERTAIN
    assert statement.uncertainty
    assert "cannot be stated as a single figure" in statement.stated

    # The readings are still carried in full.
    assert len(statement.observed) == 2


def test_agreeing_observations_are_stated_precisely(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Three sources at 0.00% apart are one answer, not three."""

    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 120_682_057.5739018, "A"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 120_682_057.5739018, "B"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 120_682_072.0, "C"),
        ),
    )

    statement = service.for_asset("XYZ").about("Circulating supply")

    assert statement is not None
    assert statement.shape is StatementShape.PRECISE
    assert "agreed by 3 sources" in statement.stated


# ── 3 & 6. useful statements survive an unresolved committee ────────


def test_a_useful_statement_survives_an_unresolved_committee(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The ETH case. `evidence_insufficient` is not the whole answer.

    A committee that cannot answer its own question does not stop this
    platform stating what it does hold — and the specific thing that is
    open is named rather than generalised into silence.
    """

    service = _service(
        tmp_path,
        facts=(_fact(SupplyConcept.CIRCULATING_ESTIMATE, 120_682_057, "CoinGecko"),),
        judgments=(
            _judgment(
                SUPPLY_GOVERNANCE,
                state=JudgmentState.ABSTAINED,
                abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
                because="No mechanical issuance rule is held for this asset.",
            ),
            _judgment(FEE_CAPTURE, verdict=FeeVerdict.MECHANISM_EVIDENCED),
        ),
    )

    assessment = service.for_asset("XYZ")

    # Something established, something structural, something open — all
    # three coexisting, which is the point.
    assert assessment.about("Circulating supply").shape is StatementShape.PRECISE  # type: ignore[union-attr]
    assert assessment.about("Value Capture").shape is StatementShape.STRUCTURAL  # type: ignore[union-attr]

    open_question = assessment.about("Supply Governance")

    assert open_question is not None
    assert open_question.shape is StatementShape.INSUFFICIENT
    assert open_question.uncertainty == (
        "No mechanical issuance rule is held for this asset."
    )

    # The useful statements are reachable without the unresolved one.
    assert len(assessment.useful) == 2


def test_two_assets_abstaining_alike_remain_distinguishable(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ETH and ARB both read `insufficient_evidence` and are not the same.

    The committee's own sentence is what separates them, which is why
    PR #116 had to persist it.
    """

    reasons = {
        "ETH": "The reward side is not read and the burn is not primary.",
        "ARB": "Its whole supply was minted at genesis; there is no rule.",
    }

    said = {}

    for asset, reason in reasons.items():
        service = _service(
            tmp_path / asset,
            judgments=(
                _judgment(
                    SUPPLY_GOVERNANCE,
                    asset=asset,
                    state=JudgmentState.ABSTAINED,
                    abstained=AbstentionReason.INSUFFICIENT_EVIDENCE,
                    because=reason,
                ),
            ),
        )

        statement = service.for_asset(asset).about("Supply Governance")

        assert statement is not None

        said[asset] = statement

    assert said["ETH"].shape is said["ARB"].shape
    assert said["ETH"].uncertainty != said["ARB"].uncertainty


def test_a_question_that_does_not_apply_is_a_structural_statement(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """*The question is the wrong instrument* is useful, not a gap."""

    service = _service(
        tmp_path,
        judgments=(
            _judgment(
                FEE_CAPTURE,
                state=JudgmentState.ABSTAINED,
                applicability=Applicability.NOT_ECONOMICALLY_APPLICABLE,
                abstained=AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
                because="Its fees are the budget that secures the network.",
            ),
        ),
    )

    statement = service.for_asset("XYZ").about("Value Capture")

    assert statement is not None
    assert statement.shape is StatementShape.STRUCTURAL
    assert statement.is_useful
    assert "wrong instrument" in statement.stated


# ── 4 & 5. a refused sentence does not erase an answer ──────────────


def test_a_refused_wording_leaves_the_answer_standing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The HYPE case. A presentation failure is not an analytical one."""

    service = _service(
        tmp_path,
        judgments=(
            _judgment(
                FEE_CAPTURE,
                verdict=FeeVerdict.MECHANISM_EVIDENCED,
                because="The committee found that a mechanism is evidenced.",
                wording_refused="the reasoning used 'buy'",
            ),
        ),
    )

    statement = service.for_asset("XYZ").about("Value Capture")

    assert statement is not None

    # The answer survives, and the refusal is what qualifies it.
    assert statement.shape is StatementShape.QUALIFIED
    assert statement.is_useful
    assert FeeVerdict.MECHANISM_EVIDENCED.stated.lower() in statement.stated.lower()
    assert "drafted explanation was refused" in (statement.qualification or "")


def test_the_narrative_validator_is_not_weakened() -> None:
    """The fix is separation, not permission.

    Every out-of-remit word is still refused, and the refused sentence
    still reaches no reader — it is replaced by the committee's own
    account rather than printed with a warning.
    """

    import pytest

    from app.services.value_capture_committee import (
        OUT_OF_REMIT,
        JudgmentRejected,
        _check_sentence,
    )

    findings = ()

    for phrase in ("buy", "bullish", "portfolio"):
        assert phrase in OUT_OF_REMIT

        with pytest.raises(JudgmentRejected):
            _check_sentence(f"This is a {phrase} case.", findings)

    # And the validator is still reached on every draft — asserted
    # behaviourally, because a judgment whose wording was refused is the
    # only thing that can prove the check ran.
    #
    # The evidence is a fixture rather than the committee's stored door:
    # reading the acquired store here passed locally and failed on a
    # clean checkout, which is the fifth outing of that trap.
    from app.domain.crypto_intelligence import ClaimType
    from app.services.value_capture_committee import ValueCaptureCommittee

    supplied = (
        EligibleFinding(
            ref="F.venue",
            stated="Users paid fees over a day.",
            claim_type=ClaimType.REPORTED,
            established_by="test fixture",
        ),
    )

    judgment = ValueCaptureCommittee()._validated(  # noqa: SLF001
        "ETH",
        {
            "verdict": "mechanism_evidenced",
            "refs": ["F.venue"],
            "because": "This is a bullish case.",
        },
        supplied,
        "test-model",
        ApplicabilityBasis(Applicability.APPLICABLE, "fixture"),
    )

    assert judgment.wording_refused
    assert "bullish" not in (judgment.because or "")


# ── 7–10. provenance, no verdicts, coexistence, stable schema ───────


def test_provenance_survives_into_every_statement(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.MAX_SUPPLY, 21_000_000, "CoinGecko"),
            _fact(SupplyConcept.MAX_SUPPLY, 21_000_000, "TokenInsight"),
        ),
        judgments=(
            _judgment(SUPPLY_GOVERNANCE, verdict=SupplyVerdict.CONSENSUS_BOUND),
        ),
    )

    assessment = service.for_asset("XYZ")

    quantity = assessment.about("Maximum supply")

    assert quantity is not None
    assert quantity.refs == ("CoinGecko", "TokenInsight")
    assert all(value.observed_at is not None for value in quantity.observed)

    judged = assessment.about("Supply Governance")

    assert judged is not None
    assert SUPPLY_GOVERNANCE.key in judged.refs


#: What an investor assessment must never carry.
FORBIDDEN = (
    "recommend",
    "recommendation",
    "rank",
    "ranking",
    "score",
    "scored",
    "aggregate",
    "agreement",
    "consensus",
    "overall",
    "weight",
    "favourable",
    "favorable",
    "adverse",
    "positive",
    "negative",
    "bullish",
    "bearish",
    "buy",
    "sell",
    "good",
    "bad",
    "strength",
    "conviction",
)


def test_the_assessment_carries_no_verdict_about_the_asset() -> None:
    """A negative architectural test over the surface and its source."""

    import re

    for surface in (InvestorAssessment, InvestorStatement, StatementShape):
        for name in dir(surface):
            for forbidden in FORBIDDEN:
                assert forbidden not in name.lower(), (surface.__name__, forbidden)

    for module in (
        "app/domain/investor_assessment.py",
        "app/services/investor_assessment_service.py",
    ):
        code = reachable(module)

        for name in re.findall(r"^\s*(?:def|class)\s+(\w+)", code, re.M):
            for forbidden in FORBIDDEN:
                assert forbidden not in name.lower(), (module, name)


def test_the_shapes_are_not_ordered() -> None:
    """`PRECISE` is not better than `UNCERTAIN`. Nothing may sort them."""

    for name in dir(StatementShape):
        assert "rank" not in name.lower()
        assert "order" not in name.lower()
        assert "level" not in name.lower()


def test_uncertainty_and_established_information_coexist(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """One unresolved subject must not suppress the resolved ones."""

    service = _service(
        tmp_path,
        facts=(
            _fact(SupplyConcept.MAX_SUPPLY, 21_000_000, "CoinGecko"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 300_000_000, "A"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 1_500_000_000, "B"),
        ),
    )

    assessment = service.for_asset("XYZ")

    shapes = {item.subject: item.shape for item in assessment.statements}

    assert shapes["Maximum supply"] is StatementShape.PRECISE
    assert shapes["Circulating supply"] is StatementShape.UNCERTAIN


def test_a_further_observation_does_not_change_the_schema(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Values differ; the type does not move."""

    two = _service(
        tmp_path / "two",
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 100.0, "A"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 110.0, "B"),
        ),
    ).for_asset("XYZ")

    three = _service(
        tmp_path / "three",
        facts=(
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 100.0, "A"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 110.0, "B"),
            _fact(SupplyConcept.CIRCULATING_ESTIMATE, 105.0, "C"),
        ),
    ).for_asset("XYZ")

    assert set(two.as_dict()) == set(three.as_dict())

    left = two.about("Circulating supply")
    right = three.about("Circulating supply")

    assert left is not None and right is not None
    assert set(left.as_dict()) == set(right.as_dict())
    assert len(right.observed) == len(left.observed) + 1


def test_a_missing_subject_is_named_rather_than_omitted(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """An investor who cannot see what is missing cannot judge the dossier."""

    assessment = _service(
        tmp_path,
        facts=(_fact(SupplyConcept.CIRCULATING_ESTIMATE, 100.0, "A"),),
    ).for_asset("XYZ")

    assert "Maximum supply" in assessment.silent_about
    assert "Tokens in existence" in assessment.silent_about


def test_a_vendor_total_equal_to_the_maximum_is_qualified(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Faithful to the evidence is not the same as responsible.

    S5 measured that a vendor's total *is* the cap for 83 of 145 capped
    assets. Printing "21 million tokens exist" beside "the maximum is 21
    million" vouches for a substitution this platform cannot rule out.
    """

    statement = (
        _service(
            tmp_path,
            facts=(
                _fact(SupplyConcept.MAX_SUPPLY, 21_000_000, "CoinGecko"),
                _fact(SupplyConcept.EMITTED_SUPPLY, 21_000_000, "CoinGecko"),
            ),
        )
        .for_asset("XYZ")
        .about("Tokens in existence")
    )

    assert statement is not None
    assert statement.shape is StatementShape.QUALIFIED
    assert "restating the cap" in (statement.qualification or "")


def test_reading_an_assessment_convenes_nothing() -> None:
    """Deterministic and read-only: no model, no fetch, no judging."""

    code = reachable("app/services/investor_assessment_service.py")

    for forbidden in ("judge(", "provider", "acquire", "draft", "await"):
        assert forbidden not in code, forbidden


# ── Zero Fake Meaning (PR #119) ─────────────────────────────────────


def _assignment(archetype: TokenArchetype) -> ArchetypeAssignment:
    """A synthetic assignment against a declared archetype.

    Deliberately *not* a corpus entry. The forcing case for this layer
    is a stablecoin, and proving that a supply figure cannot become
    dilution framing must not require putting a stablecoin in front of
    an investor — the reserve, redemption and peg questions its
    archetype names as unmodelled are unbuilt on purpose.
    """

    return ArchetypeAssignment(
        symbol="XYZ",
        archetype=archetype,
        confidence=ArchetypeConfidence.STRUCTURAL,
        because="a synthetic assignment, for the boundary rather than a corpus case",
        rests_on=("declared in ARCHETYPES",),
    )


_SUPPLY = (
    _fact(SupplyConcept.MAX_SUPPLY, 100_000_000_000.0, "TokenInsight"),
    _fact(SupplyConcept.EMITTED_SUPPLY, 64_000_000_000.0, "CoinGecko"),
    _fact(SupplyConcept.CIRCULATING_ESTIMATE, 64_000_000_000.0, "CoinGecko"),
)


def _as(tmp_path, archetype: TokenArchetype):  # type: ignore[no-untyped-def]
    return InvestorAssessmentService(
        supply=_Supply(_SUPPLY),  # type: ignore[arg-type]
        matrix=CommitteeMatrixService(
            history=JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path)),
        ),
        archetype=lambda symbol: _assignment(archetype),
    ).for_asset("XYZ")


def test_a_supply_figure_is_not_authority_to_say_dilution(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The forcing case, and the acceptance criterion of the slice.

    A stablecoin with a maximum supply, an emitted total and a
    circulating estimate — every number this platform holds about any
    other token. Under the old rule that was sufficient to print *"it
    bounds how far the holder's share can be diluted"*, because the
    sentence was keyed by quantity and no asset could reach it.

    It is false here, and not merely unsupported: a stablecoin holder's
    position is a claim on a reserve at par, so supply expanding is the
    instrument working rather than the holder being diluted. The
    measurements survive; the interpretation does not travel with them.
    """

    assessment = _as(tmp_path, TokenArchetype.STABLECOIN)

    said = " ".join(
        " ".join([item.stated] + [why.stated for why in item.why_it_matters])
        for item in assessment.statements
    ).lower()

    assert "dilut" not in said
    assert "scarcit" not in said

    # The abstention is stated, not silent — and the figures stand.
    for subject in ("Maximum supply", "Tokens in existence", "Circulating supply"):
        statement = assessment.about(subject)

        assert statement is not None
        assert statement.why_it_matters == ()
        assert "claim on a reserve" in (statement.interpretation_withheld or "")
        assert statement.observed


def test_the_same_figures_keep_their_meaning_where_a_contract_licenses_it(  # type: ignore[no-untyped-def]
    tmp_path,
) -> None:
    """The positive half, and the one this slice must not solve by deleting.

    Byte-identical evidence, read as a monetary network: now the
    maximum supply carries *two* licensed readings, because two
    questions demand `max_supply` by name and the archetype asks both.
    The second — monetary scarcity — was invisible before, and its own
    sentence is stronger than the one it replaces: it warns that a
    stated cap is not the claim.
    """

    monetary = _as(tmp_path, TokenArchetype.MONETARY_NETWORK).about("Maximum supply")
    stable = _as(tmp_path, TokenArchetype.STABLECOIN).about("Maximum supply")

    assert monetary is not None and stable is not None
    assert monetary.stated == stable.stated
    assert monetary.observed == stable.observed

    questions = [meaning.question for meaning in monetary.why_it_matters]

    assert questions == ["Supply and dilution", "Monetary scarcity"]
    assert monetary.interpretation_withheld is None

    # An application protocol asks one of the two and not the other, so
    # the answer is neither the monetary network's nor the stablecoin's.
    application = _as(tmp_path, TokenArchetype.APPLICATION_PROTOCOL).about(
        "Maximum supply"
    )

    assert application is not None
    assert [meaning.question for meaning in application.why_it_matters] == [
        "Supply and dilution"
    ]


def test_no_meaning_is_authored_by_this_layer(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Every reader-facing interpretation is a quotation, checked as one.

    The guard that survives a refactor. A future contributor who adds a
    fourth quantity and writes it a nice sentence fails here, because
    the sentence will not be found in any contract that owns a
    question — which is the whole of this layer's economic authority.
    """

    licensed = {question.matters_because for question in QUESTIONS.values()}

    for archetype in TokenArchetype:
        for statement in _as(tmp_path, archetype).statements:
            for meaning in statement.why_it_matters:
                assert meaning.stated in licensed, meaning.stated
                assert meaning.licensed_by


def test_a_committee_licenses_its_own_question(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The half that needed no repair, and why saying so matters.

    A committee owns its question, decides in its own economic terms
    whether that question applies, and records the role it read that
    from. The licence was always there and was printed as an
    unattributed sentence; now it names itself. PR #114's ruling is
    untouched — the committee's words are quoted, never interpreted.
    """

    statement = (
        _service(
            tmp_path,
            judgments=(
                _judgment(
                    verdict=FeeVerdict.MECHANISM_EVIDENCED,
                    because="a mechanism names the token",
                ),
            ),
        )
        .for_asset("XYZ")
        .about("Value Capture")
    )

    assert statement is not None

    meaning = statement.why_it_matters[0]

    assert meaning.stated == FEE_CAPTURE.question
    assert "Value Capture Committee owns this question" in meaning.licensed_by
    assert "applicable" in meaning.licensed_by


def test_an_unclassified_asset_is_read_as_the_traded_asset_it_is(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The residual, asserted rather than hidden.

    `UNKNOWN` composes the market lens alone *by declaration* — an
    unclassified security "is read only as a traded asset" — so supply
    and dilution genuinely applies to it and TAO keeps its reading.

    The limit that follows is real and stated here so nobody discovers
    it later: **a stablecoin this platform failed to classify would
    receive dilution framing.** The gate is the archetype, so an asset
    with no archetype has no gate. Closing it means classifying the
    asset, not weakening the rule.
    """

    statement = _as(tmp_path, TokenArchetype.UNKNOWN).about("Maximum supply")

    assert statement is not None
    assert [meaning.question for meaning in statement.why_it_matters] == [
        "Supply and dilution"
    ]
