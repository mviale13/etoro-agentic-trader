"""The first committee: bounded judgment over grounded evidence.

Ten acceptance demonstrations, plus the four boundaries the owner named
mid-slice — because the dangerous failures here are not crashes, they
are plausible answers:

- **Bitcoin must not be adverse** for lacking mechanics it was never
  meant to have, and its abstention must not look like Bittensor's,
  whose problem is entirely different;
- **`mechanism_evidenced` is not "favourable"**, and nothing may read it
  as a grade;
- **no threshold is encoded** — 64%, 18% and 9% are contrast, not bands;
- and **confidence must not decide the verdict**, which is guaranteed by
  having different things produce them.

No test asserts that a particular asset is *good*. Where an expected
verdict appears it is asserted from the evidence shape that produces it,
never from a remembered answer.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import pytest

from app.domain.committee_judgment import (
    ELIGIBLE_CLAIM_TYPES,
    AbstentionReason,
    Applicability,
    Confidence,
    EligibleFinding,
    JudgmentState,
    Remit,
    Verdict,
    confidence_from,
    is_eligible,
)
from app.domain.crypto_intelligence import ClaimType
from app.domain.protocol_fundamentals import ProtocolMetric
from app.domain.provenance import Provenance
from app.providers.defillama_provider import ProtocolClaimSet, ProtocolMetricClaim
from app.providers.narrative_provider import Draft, DraftRequest, NarrativeDeclined
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
from app.services.value_capture_committee import (
    OUT_OF_REMIT,
    JudgmentRejected,
    ValueCaptureCommittee,
    judgment_schema,
)
from tests.reachability import reachable

# ── recorded evidence ───────────────────────────────────────────────
#
# The protocol readings as they stood on 2026-08-10, supplied as a
# fixture rather than read from the live store. The store is gitignored,
# so tests that read it pass here and fail on a clean checkout — the
# trap that caught four tests in S3 and one in slice 1, and that
# `git archive HEAD` in isolation is what catches.

_READ = datetime(2026, 8, 10, 10, 20, tzinfo=UTC)

_PROTOCOL: dict[str, ProtocolClaimSet] = {
    "ethereum-chain": ProtocolClaimSet(
        entity_key="ethereum-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=_READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 175_154.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                32_159.0,
                "24 hours",
                methodology="Amount of ETH burned — base fees plus blob fees",
            ),
        ),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.HOLDER_REVENUE}),
    ),
    "hyperliquid-protocol": ProtocolClaimSet(
        entity_key="hyperliquid-protocol",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=_READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 842_720.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                534_851.0,
                "24 hours",
                methodology=(
                    "Hyperliquid Perps: 99% of fees go to Assistance Fund "
                    "for buying HYPE tokens"
                ),
            ),
        ),
        defines=frozenset(ProtocolMetric),
    ),
    "solana-chain": ProtocolClaimSet(
        entity_key="solana-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=_READ),
        claims=(
            ProtocolMetricClaim(ProtocolMetric.FEES, 650_664.0, "24 hours"),
            ProtocolMetricClaim(
                ProtocolMetric.HOLDER_REVENUE,
                59_296.0,
                "24 hours",
                methodology="Transaction base fees paid by users were burned.",
            ),
        ),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.HOLDER_REVENUE}),
    ),
    # Fees measured, and the holder-revenue sibling *defined and empty* —
    # which is the shape that makes an absence evidence.
    "arbitrum-chain": ProtocolClaimSet(
        entity_key="arbitrum-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=_READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.FEES, 6_853.0, "24 hours"),),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.HOLDER_REVENUE}),
    ),
    "bitcoin-chain": ProtocolClaimSet(
        entity_key="bitcoin-chain",
        source="DefiLlama",
        read=Provenance(source="DefiLlama", observed_at=_READ),
        claims=(ProtocolMetricClaim(ProtocolMetric.FEES, 139_032.0, "24 hours"),),
        defines=frozenset({ProtocolMetric.FEES, ProtocolMetric.HOLDER_REVENUE}),
    ),
}


class _Claims:
    @staticmethod
    def claim_set(entity_key: str) -> ProtocolClaimSet | None:
        return _PROTOCOL.get(entity_key)


class _NoJournal:
    """No recorded history. The journal store is gitignored too."""

    @staticmethod
    def history(asset: str, now: object = None, limit: int = 12) -> tuple[()]:
        return ()


class _Judge:
    """A provider returning a prepared judgment."""

    name = "Test"
    model = "test-model"

    def __init__(self, payload: object = None, error: Exception | None = None) -> None:
        self._payload = payload
        self._error = error

    async def draft(self, request: DraftRequest) -> Draft:
        if self._error is not None:
            raise self._error

        text = (
            self._payload
            if isinstance(self._payload, str)
            else json.dumps(self._payload)
        )

        return Draft(text=text, model=self.model, usage=None)


def _committee(payload: object = None, error: Exception | None = None):  # type: ignore[no-untyped-def]
    return ValueCaptureCommittee(
        protocol=ProtocolFundamentalsService(sources=(_Claims(),)),
        journal=_NoJournal(),  # type: ignore[arg-type]
        provider=_Judge(payload, error),
    )


def _judge(symbol: str, payload: object = None, error: Exception | None = None):  # type: ignore[no-untyped-def]
    return asyncio.run(_committee(payload, error).judge(symbol))


@pytest.fixture(autouse=True)
def _on(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("MOVRVEST_COMMITTEE_JUDGMENT", "on")


# ── 1 and 2: supported judgments, both directions ───────────────────


def test_a_mechanism_backed_asset_is_judged_from_its_own_evidence() -> None:
    """Acceptance 1, asserted from the evidence rather than remembered.

    The assertion is not *"ETH is favourable"*. It is that where the
    evidence carries a fee reading, a holder-revenue reading and a
    stated mechanism, the committee can answer its question — and that
    the answer cites those findings.
    """

    committee = _committee()

    evidence = committee.evidence("ETH")

    refs = {finding.ref for finding in evidence}

    assert any(ref.startswith("F.") for ref in refs), "needs a fee reading"
    assert any(ref.startswith("H.") for ref in refs), "needs a capture reading"

    judgment = _judge(
        "ETH",
        {
            "verdict": "mechanism_evidenced",
            "refs": [r for r in refs if r.startswith(("F.", "H.", "S."))][:3],
            "because": "Users paid fees and a stated mechanism returned some.",
        },
    )

    assert judgment.state is JudgmentState.JUDGED
    assert judgment.verdict is Verdict.MECHANISM_EVIDENCED
    assert judgment.grounded_in(refs)


def test_an_asset_whose_source_establishes_no_mechanism_is_judged_so() -> None:
    """Acceptance 2, and the four conditions the owner required.

    `no_mechanism_evidenced` is only supportable where the question
    applies, the source *establishes* the absence rather than omitting
    it, and the verdict does not assert that the absence is bad.
    """

    committee = _committee()

    evidence = {finding.ref: finding for finding in committee.evidence("ARB")}

    # The sibling rule fired: absence of evidence would produce nothing.
    sibling = [ref for ref in evidence if ref.startswith("N.")]

    assert sibling, "the source must establish the absence, not omit it"

    assert "evidence that no such mechanism exists rather than a missing" in (
        evidence[sibling[0]].stated
    )

    judgment = _judge(
        "ARB",
        {
            "verdict": "no_mechanism_evidenced",
            "refs": sibling,
            "because": "The source publishes no holder figure here.",
        },
    )

    assert judgment.verdict is Verdict.NO_MECHANISM_EVIDENCED


def test_neither_verdict_is_a_grade() -> None:
    """The owner's boundary, made structural.

    `mechanism_evidenced` must not be readable as *favourable*. Nothing
    in the enumeration, its wording, or the schema expresses approval.
    """

    words = " ".join(v.value + " " + v.stated for v in Verdict).lower()

    for forbidden in (
        "favourable",
        "favorable",
        "adverse",
        "positive",
        "negative",
        "strong",
        "weak",
        "good",
        "poor",
        "healthy",
    ):
        assert forbidden not in words, forbidden


def test_no_threshold_is_encoded_anywhere() -> None:
    """64%, 18% and 9% are contrast, not bands.

    Six observations do not establish a floor, and the committee reports
    the share as evidence rather than banding it.

    Tested behaviourally rather than by searching for the word: the
    module *explains* that it establishes no threshold, so a text search
    for "threshold" finds the sentence refusing one. That trap is
    documented in `tests/reachability.py` and has caught this codebase
    five times.
    """

    committee = _committee()

    shares = {}

    for asset in ("HYPE", "ETH", "SOL"):
        for finding in committee.evidence(asset):
            if finding.ref.startswith("S."):
                shares[asset] = finding.stated

    assert len(shares) >= 2, "needs two assets with very different shares"

    # Every share sentence has the identical shape. Only the number
    # differs — no label, no band, no comparison is attached to it.
    for stated in shares.values():
        assert "of the fees paid over the same day" in stated

        for banding in (
            "material",
            "meaningful",
            "significant",
            "substantial",
            "high",
            "low",
            "sufficient",
            "insufficient",
        ):
            assert banding not in stated.lower(), (stated, banding)


# ── 3: three abstentions, never collapsed ───────────────────────────


def test_an_asset_the_question_does_not_suit_is_not_judged_adversely() -> None:
    """Acceptance 3, and the owner's sharpest point.

    Bitcoin has fees and no holder mechanism. A committee that answered
    anyway would report *no mechanism evidenced* — true, and a category
    error, because a monetary asset's fees are the budget that secures
    it. So the question is left unanswered, with the economics stated.
    """

    committee = _committee()

    applies, because = committee.applicability("BTC")

    assert applies is Applicability.NOT_ECONOMICALLY_APPLICABLE
    assert "security" in because or "secures" in because

    judgment = _judge("BTC")

    assert judgment.state is JudgmentState.ABSTAINED
    assert judgment.abstained_because is (AbstentionReason.NOT_ECONOMICALLY_APPLICABLE)
    assert judgment.verdict is None

    # And it says so in words a surface can print without implying fault.
    assert "rather than answered adversely" in (
        judgment.abstained_because.stated + (judgment.because or "")
    )


def test_an_unestablished_asset_abstains_differently_from_an_inapplicable_one() -> None:
    """The distinction the owner asked to be preserved.

    Bittensor's problem is not that the question is the wrong
    instrument — it is that this platform cannot establish which
    instrument is right. Collapsing the two would report *we know this
    does not apply* when the truth is *we do not know*.
    """

    unknown = _judge("TAO")
    monetary = _judge("BTC")

    assert unknown.state is monetary.state is JudgmentState.ABSTAINED

    assert unknown.abstained_because is AbstentionReason.APPLICABILITY_UNESTABLISHED
    assert monetary.abstained_because is AbstentionReason.NOT_ECONOMICALLY_APPLICABLE

    assert unknown.abstained_because is not monetary.abstained_because


def test_applicability_evidence_and_judgment_are_three_separate_steps() -> None:
    """§1–3 of the mid-slice ruling, structurally.

    Applicability is decided before any evidence is read, so a rich
    evidence set cannot make an inapplicable question applicable — the
    failure mode where a figure quietly decides what a question means.
    """

    committee = _committee()

    # Bitcoin has eligible evidence and is still not asked.
    assert committee.evidence("BTC")

    assert not committee.applicability("BTC")[0].is_applicable


def test_the_committee_owns_its_applicability_rule() -> None:
    """It reads the archetype as evidence and does not delegate.

    A committee that forwarded to `applicability_for` would inherit a
    taxonomy built to decide which questions an Asset Quality layer
    asks, and would change meaning silently the next time that taxonomy
    moved for another purpose.
    """

    code = reachable("app/services/value_capture_committee.py")

    assert "applicability_for" not in code
    assert "crypto_questions" not in code

    # It states its own reason, in economic terms.
    _, because = _committee().applicability("BTC")

    assert len(because.split()) > 15


# ── 4: removing the decisive finding ────────────────────────────────


def test_removing_the_decisive_finding_cannot_be_recovered_by_the_model() -> None:
    """Acceptance 4.

    Strip the capture reading and the verdict that rested on it can no
    longer be cited — the validator refuses the reference rather than
    the model reconstructing the fact from what it knows about Ethereum.
    """

    committee = _committee(
        {
            "verdict": "mechanism_evidenced",
            "refs": ["H.ethereum-chain"],
            "because": "A stated mechanism returned some fees to holders.",
        }
    )

    full = {finding.ref for finding in committee.evidence("ETH")}

    assert "H.ethereum-chain" in full

    starved = tuple(
        finding
        for finding in committee.evidence("ETH")
        if not finding.ref.startswith("H.")
    )

    with pytest.raises(JudgmentRejected, match="not supplied"):
        committee._validated(  # noqa: SLF001
            "ETH",
            {
                "verdict": "mechanism_evidenced",
                "refs": ["H.ethereum-chain"],
                "because": "A stated mechanism returned some fees to holders.",
            },
            starved,
            "test-model",
        )


# ── 5 and 6: eligibility is structural ──────────────────────────────


def test_an_attributed_claim_cannot_be_constructed_as_evidence() -> None:
    """Acceptance 5. The tempting sentence is refused by the type, not
    by a reviewer noticing it."""

    with pytest.raises(ValueError, match="cannot reach a committee"):
        EligibleFinding(
            ref="A1",
            stated=(
                "CoinGecko states: sustained institutional demand is "
                "supporting price discovery."
            ),
            claim_type=ClaimType.ATTRIBUTED,
            established_by="Attributed interpretation",
        )


def test_an_inferred_claim_cannot_be_constructed_as_evidence() -> None:
    with pytest.raises(ValueError, match="cannot reach a committee"):
        EligibleFinding(
            ref="I1",
            stated="Identifiable balance sheets hold a material share.",
            claim_type=ClaimType.INFERRED,
            established_by="MOVRvest reading",
        )


def test_only_measured_and_reported_are_eligible() -> None:
    assert ELIGIBLE_CLAIM_TYPES == {ClaimType.MEASURED, ClaimType.REPORTED}

    assert is_eligible(ClaimType.MEASURED)
    assert is_eligible(ClaimType.REPORTED)

    for excluded in (ClaimType.ATTRIBUTED, ClaimType.INFERRED, ClaimType.UNRESOLVED):
        assert not is_eligible(excluded)


def test_synthesis_prose_cannot_reach_the_committee() -> None:
    """Acceptance 6. *The synthesis is communication, not evidence* —
    asserted over the parse tree rather than promised."""

    for module in (
        "app/domain/committee_judgment.py",
        "app/services/value_capture_committee.py",
    ):
        code = reachable(module)

        for forbidden in (
            "IntelligenceSynthesis",
            "SynthesisItem",
            "IntelligenceSynthesisService",
            "IntelligenceSynthesist",
            "synthesise",
        ):
            assert forbidden not in code, (module, forbidden)


def test_live_evidence_carries_only_eligible_claim_types() -> None:
    """Acceptance 9, over the real corpus."""

    committee = _committee()

    for asset in ("ETH", "HYPE", "ARB", "BTC"):
        for finding in committee.evidence(asset):
            assert is_eligible(finding.claim_type), (asset, finding.ref)


# ── 7: confidence and verdict are independent ───────────────────────


def test_more_evidence_raises_confidence_without_moving_the_verdict() -> None:
    """Acceptance 7, and §7 of the original ruling.

    The same verdict, cited against one finding and then against two,
    produces the same answer with more confidence. It is structural:
    `confidence_from` never sees the verdict and the judge never sees
    the count.
    """

    committee = _committee()

    refs = [
        finding.ref
        for finding in committee.evidence("ETH")
        if finding.ref.startswith(("F.", "H.", "S."))
    ]

    assert len(refs) >= 2

    def verdict_with(cited: list[str]):  # type: ignore[no-untyped-def]
        return committee._validated(  # noqa: SLF001
            "ETH",
            {
                "verdict": "mechanism_evidenced",
                "refs": cited,
                "because": "A stated mechanism returned some fees to holders.",
            },
            committee.evidence("ETH"),
            "test-model",
        )

    thin = verdict_with(refs[:1])
    thick = verdict_with(refs[:2])

    assert thin.verdict is thick.verdict is Verdict.MECHANISM_EVIDENCED

    assert thin.confidence is Confidence.SINGLE_OBSERVATION
    assert thick.confidence is Confidence.MULTIPLE_OBSERVATIONS


def test_confidence_cannot_see_the_verdict() -> None:
    """The guarantee behind the previous test: the function that sets
    confidence takes counts and nothing else."""

    assert confidence_from(supporting=1, across_captures=False) is (
        Confidence.SINGLE_OBSERVATION
    )
    assert confidence_from(supporting=3, across_captures=False) is (
        Confidence.MULTIPLE_OBSERVATIONS
    )
    assert confidence_from(supporting=1, across_captures=True) is (
        Confidence.OBSERVED_OVER_TIME
    )


def test_confidence_is_categorical_rather_than_a_score() -> None:
    """§5: a categorical judgment beats fake precision. Three readings
    are three readings, not 73% confident."""

    for level in Confidence:
        assert not any(character.isdigit() for character in level.value)


# ── 8: nothing can express an action ────────────────────────────────


def test_the_schema_has_nowhere_to_put_a_recommendation() -> None:
    """Acceptance 8. The fence is the schema, not the prompt."""

    schema = judgment_schema()

    assert set(schema["properties"]) == {"verdict", "refs", "because"}

    assert schema["properties"]["verdict"]["enum"] == [
        "mechanism_evidenced",
        "no_mechanism_evidenced",
        "abstain",
    ]

    # No score, no conviction, no stance, no recommendation.
    for forbidden in ("score", "confidence", "recommendation", "conviction", "stance"):
        assert forbidden not in schema["properties"]


def test_an_out_of_remit_verdict_is_refused() -> None:
    committee = _committee()

    with pytest.raises(JudgmentRejected, match="not an answer to its question"):
        committee._validated(  # noqa: SLF001
            "ETH",
            {"verdict": "buy", "refs": ["F.ethereum-chain"], "because": "x"},
            committee.evidence("ETH"),
            "test-model",
        )


def test_reasoning_that_leaves_the_remit_is_refused() -> None:
    committee = _committee()

    evidence = committee.evidence("ETH")

    for sentence in (
        "This makes the asset attractive at current levels.",
        "The portfolio should hold this.",
        "Fundamentals look bullish.",
    ):
        with pytest.raises(JudgmentRejected, match="outside this committee"):
            committee._validated(  # noqa: SLF001
                "ETH",
                {
                    "verdict": "mechanism_evidenced",
                    "refs": ["F.ethereum-chain"],
                    "because": sentence,
                },
                evidence,
                "test-model",
            )


def test_the_out_of_remit_list_names_the_actual_risk() -> None:
    for word in ("buy", "sell", "portfolio", "conviction", "bullish"):
        assert word in OUT_OF_REMIT


def test_an_invented_figure_is_refused() -> None:
    """§8: the committee interprets established facts and never becomes
    another calculator."""

    committee = _committee()

    with pytest.raises(JudgmentRejected, match="appears in no supplied fact"):
        committee._validated(  # noqa: SLF001
            "ETH",
            {
                "verdict": "mechanism_evidenced",
                "refs": ["F.ethereum-chain"],
                "because": "Holders received $999k over the day.",
            },
            committee.evidence("ETH"),
            "test-model",
        )


def test_a_verdict_citing_nothing_is_refused() -> None:
    committee = _committee()

    with pytest.raises(JudgmentRejected, match="cited no evidence"):
        committee._validated(  # noqa: SLF001
            "ETH",
            {"verdict": "mechanism_evidenced", "refs": [], "because": "Because."},
            committee.evidence("ETH"),
            "test-model",
        )


# ── 10: failure is not abstention ───────────────────────────────────


def test_a_provider_failure_is_visibly_different_from_an_abstention() -> None:
    """Acceptance 10, and §6. Collapsing them would make a broken
    provider look like intellectual honesty."""

    broken = _judge("ETH", error=RuntimeError("no route to host"))

    assert broken.state is JudgmentState.UNAVAILABLE
    assert broken.abstained_because is None
    assert broken.unavailable_because

    abstained = _judge("BTC")

    assert abstained.state is JudgmentState.ABSTAINED
    assert abstained.unavailable_because is None

    assert broken.state is not abstained.state


def test_a_declined_or_unparseable_judgment_is_unavailable() -> None:
    assert (
        _judge("ETH", error=NarrativeDeclined("declined")).state
        is JudgmentState.UNAVAILABLE
    )

    assert _judge("ETH", payload="not json").state is JudgmentState.UNAVAILABLE


def test_the_judge_may_abstain_and_that_is_not_a_failure() -> None:
    """A judge that says it cannot answer is the committee working."""

    judgment = _judge(
        "ETH",
        {"verdict": "abstain", "refs": [], "because": "Not answerable."},
    )

    assert judgment.state is JudgmentState.ABSTAINED
    assert judgment.abstained_because is AbstentionReason.INSUFFICIENT_EVIDENCE


def test_with_the_flag_off_there_is_no_judgment_and_the_evidence_stands() -> None:
    """The deterministic floor: no verdict, and a worded reason."""

    import os

    os.environ.pop("MOVRVEST_COMMITTEE_JUDGMENT", None)

    committee = _committee()

    judgment = asyncio.run(committee.judge("ETH"))

    assert judgment.state is JudgmentState.UNAVAILABLE
    assert "off" in (judgment.unavailable_because or "")

    # The evidence is unaffected by the flag.
    assert committee.evidence("ETH")


# ── §9: no portfolio context ────────────────────────────────────────


def test_the_committee_cannot_see_the_portfolio_or_any_decision() -> None:
    """§9. Grounded evidence becoming bounded judgment is what is under
    test; portfolio state is not allowed near it yet."""

    for module in (
        "app/domain/committee_judgment.py",
        "app/services/value_capture_committee.py",
    ):
        code = reachable(module)

        for forbidden in (
            "PortfolioSnapshot",
            "Portfolio",
            "ExecutiveDecision",
            "InvestmentDecision",
            "Recommendation",
            "DecisionSynthesis",
            "CommitteeOpinion",
            "InvestmentPolicy",
            "position",
            "cash",
        ):
            assert forbidden not in code, (module, forbidden)


def test_the_committee_cannot_reach_asset_quality() -> None:
    for module in (
        "app/domain/committee_judgment.py",
        "app/services/value_capture_committee.py",
    ):
        code = reachable(module)

        for forbidden in ("crypto_quality", "asset_quality", "quality_signal"):
            assert forbidden not in code, (module, forbidden)


def test_there_is_exactly_one_committee() -> None:
    """§2: not a taxonomy. One remit, earned by measurement."""

    assert len(list(Remit)) == 1
    assert Remit.VALUE_CAPTURE.question
