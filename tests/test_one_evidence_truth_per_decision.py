"""One rendered decision may hold one truth about quality, and one only.

DV2. The measured defect: the quality *score* was read from the grounded
assessment while every sentence *about* quality was read from the provider
signal, so AAPL printed "Quality data is unavailable" beside its own
grounded MEDIUM 62 and DIS beside a HIGH 80. Two readings of one subject on
one page, disagreeing.

Three invariants are pinned here, and none of them is pinned by naming the
six companies that showed them:

1. **A page cannot contradict itself about quality.** Wherever a quality
   score exists, nothing in the same evidence claims quality is
   unavailable — over the whole cross-product of provider band and
   grounded band, not over the specimens that happened to fail.
2. **The three quality states stay three.** Assessed-and-banded,
   assessed-and-inconclusive, and genuinely-unavailable produce three
   distinct outcomes, and an inconclusive reading is never worded as an
   absent one. JPM, HON and KO are the controls: their statements were
   read and could not conclude, which is not the same as never read.
3. **A conviction requires something to be convinced by.** No supporting
   reason, no number — and never a zero in its place, because zero is the
   bottom of the scale rather than the absence of a position on it.
"""

from __future__ import annotations

import pytest

from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.cio.artificial_cio import ArtificialCIO
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import DecisionEvidence
from app.domain.asset_class import AssetClass
from app.domain.business_quality import (
    BusinessQuality,
    ExcludedDimension,
    QualityBand,
    QualityFactor,
)
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.financial_question import AnswerState, FinancialQuestionKey
from app.domain.finding import Sense
from app.domain.momentum_signal import MomentumSignal
from app.domain.quality_signal import QualitySignal
from app.domain.value_signal import ValueSignal

PROVIDER_BANDS = ("HIGH", "MEDIUM", "LOW", "UNKNOWN")

GROUNDED_BANDS = (
    QualityBand.HIGH,
    QualityBand.MEDIUM,
    QualityBand.LOW,
    QualityBand.UNKNOWN,
)

#: The claim this slice exists to make unproducible, in the form the
#: product printed it.
UNAVAILABLE = "Quality data is unavailable"


def make_company(quality: str = "HIGH") -> CompanyRecommendation:
    """A provider-fed analysis carrying one quality band."""

    return CompanyRecommendation(
        symbol="TEST",
        recommendation="HOLD",
        confidence=60,
        summary="HOLD: TEST",
        signals=CompanySignals(
            value=ValueSignal(valuation="FAIR", confidence=60, evidence=()),
            quality=QualitySignal(quality=quality, confidence=60, evidence=()),
            momentum=MomentumSignal(
                trend="NEUTRAL",
                strength="WEAK",
                confidence=60,
                evidence=(),
            ),
        ),
        evidence=(),
    )


def make_grounded(
    band: QualityBand,
    answered: int = 3,
    favourable: int = 2,
) -> BusinessQuality:
    """A grounded assessment banded as the caller says.

    Built directly rather than through `assess` so a band can be paired
    with a provider band that contradicts it — which is the whole point:
    the invariant must hold for combinations the corpus has never shown.
    """

    factors = tuple(
        QualityFactor(
            question=key,
            asks=f"Question {index}",
            state=(
                AnswerState.ANSWERED
                if index < answered
                else AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS
            ),
            verdict="strong" if index < favourable else "weak",
            points=1 if index < favourable else 0,
            sense=Sense.FAVOURABLE if index < favourable else Sense.ADVERSE,
            because=None if index < answered else "the figures are not established",
        )
        for index, key in enumerate(
            (
                FinancialQuestionKey.PROFITABILITY,
                FinancialQuestionKey.REVENUE_GROWTH,
                FinancialQuestionKey.EARNINGS_GROWTH,
            )
        )
    )

    return BusinessQuality(
        symbol="TEST",
        factors=factors,
        excluded=(ExcludedDimension(name="Leverage", because="out of reach"),),
        favourable=favourable,
        answered=answered,
        band=band,
        source="10-K 0000000000-00-000000",
    )


def missing_for(
    provider: str | None,
    grounded: QualityBand | None,
) -> tuple[str, ...]:
    """What the builder says this case is short of."""

    return DecisionEvidenceBuilder._missing_evidence(
        make_company(provider) if provider is not None else None,
        "TEST",
        AssetClass.STOCK,
        make_grounded(grounded) if grounded is not None else None,
    )


def quality_score_for(
    provider: str | None,
    grounded: QualityBand | None,
) -> int | None:
    """The score the same two inputs produce, by the same precedence."""

    return DecisionEvidenceBuilder._quality_value(
        make_company(provider) if provider is not None else None,
        make_grounded(grounded) if grounded is not None else None,
    )


# ── 1. one page, one truth ──────────────────────────────────────────


@pytest.mark.parametrize("provider", [*PROVIDER_BANDS, None])
@pytest.mark.parametrize("grounded", [*GROUNDED_BANDS, None])
def test_a_scored_quality_is_never_also_reported_unavailable(
    provider: str | None,
    grounded: QualityBand | None,
) -> None:
    """The invariant, over every combination rather than the two specimens.

    AAPL and DIS are one cell of this table each. Pinning them by name
    would leave the other twenty-three free to contradict themselves.
    """

    score = quality_score_for(provider, grounded)

    if score is None:
        return

    for sentence in missing_for(provider, grounded):
        assert UNAVAILABLE not in sentence


def test_the_defect_specimen_is_the_cell_this_table_covers() -> None:
    """Provider UNKNOWN beside a grounded band: AAPL's and DIS's shape.

    Named so the table above cannot silently stop covering the case that
    earned it — a parametrisation that drifted to fewer bands would still
    pass every assertion it made.
    """

    assert quality_score_for("UNKNOWN", QualityBand.MEDIUM) == 62
    assert quality_score_for("UNKNOWN", QualityBand.HIGH) == 80

    # Nothing about quality is short — the other clauses (this fixture
    # carries no price history) are untouched and stay.
    for band in (QualityBand.MEDIUM, QualityBand.HIGH):
        assert all(
            "quality" not in line.lower() for line in missing_for("UNKNOWN", band)
        )


def test_the_provider_still_speaks_where_no_grounded_reading_exists() -> None:
    """Nothing was solved by silencing the older route.

    Where the statements support no assessment at all, an UNKNOWN provider
    band is a genuine absence and is still reported as one.
    """

    assert f"{UNAVAILABLE} for TEST." in missing_for("UNKNOWN", None)


# ── 2. three states, still three ────────────────────────────────────


def test_assessed_and_inconclusive_is_not_worded_as_unavailable() -> None:
    """JPM, HON and KO: read, and unable to conclude.

    The distinction is the point. "Unavailable" sends the investor to
    acquire what is already held, and denies a reading the same page shows.
    """

    stated = missing_for(None, QualityBand.UNKNOWN)

    quality = [line for line in stated if "quality" in line.lower()]

    assert quality
    assert all(UNAVAILABLE not in line for line in quality)
    assert any("could not be concluded" in line for line in quality)


def test_the_three_quality_states_produce_three_different_outcomes() -> None:
    """Banded, inconclusive, and never read — none collapses into another."""

    banded = missing_for(None, QualityBand.MEDIUM)
    inconclusive = missing_for(None, QualityBand.UNKNOWN)
    unread = missing_for("UNKNOWN", None)

    assert len({banded, inconclusive, unread}) == 3

    assert any("could not be concluded" in line for line in inconclusive)
    assert any(UNAVAILABLE in line for line in unread)

    # And the strongest of the three says nothing is missing about quality.
    assert all("quality" not in line.lower() for line in banded)


def test_a_grounded_reading_is_security_level_evidence() -> None:
    """UNP's defect: a quorate 10-K reading, reported as nothing at all.

    The rationale said "there is nothing to base a decision on" on the page
    printing the band. Whether the reading concluded or not, it happened.
    """

    for band in GROUNDED_BANDS:
        assert missing_for(None, band)[0].startswith("No market analysis")

    # And where there is genuinely nothing, the older sentence stands.
    assert missing_for(None, None) == (
        "No security-level analysis is available for TEST.",
    )


def test_an_inconclusive_reading_is_not_restated_word_for_word() -> None:
    """The rationale explains; this names what a later cycle could supply.

    Both belong on the page, and printing one sentence under two headings
    is the repetition the presentation-ownership audit measured six times.
    """

    grounded = make_grounded(QualityBand.UNKNOWN)

    rationale = ArtificialCIO()._unassessable_quality(
        DecisionEvidence(
            symbol="TEST",
            evidence_score=50,
            grounded_quality=grounded,
        )
    )

    review = [
        line for line in missing_for(None, QualityBand.UNKNOWN) if "quality" in line
    ]

    assert review
    assert all(line != rationale for line in review)
    assert grounded.stated() in rationale
    assert all(grounded.stated() not in line for line in review)


# ── 3. a number needs a reason ──────────────────────────────────────


def evidence_for(
    strengths: tuple[str, ...],
    quality_score: int | None = 62,
) -> DecisionEvidence:
    return DecisionEvidence(
        symbol="TEST",
        quality_score=quality_score,
        evidence_score=51,
        portfolio_fit_score=78,
        strengths=strengths,
    )


def test_no_supporting_reason_means_no_conviction() -> None:
    """UNP, JPM, HON and KO each printed 64 beside an empty `because`."""

    decision = ArtificialCIO().decide(evidence_for(()))

    assert decision.conviction is None


def test_a_withheld_conviction_is_never_a_zero() -> None:
    """Zero is the lowest judgment on the scale; this is the absence of one.

    Spelt as an identity check rather than an inequality, because `0` and
    `None` compare unequal while `not conviction` is true of both — and
    that conflation is exactly what the journal was doing on read.
    """

    decision = ArtificialCIO().decide(evidence_for(()))

    assert decision.conviction is None


def test_a_supported_case_keeps_the_existing_arithmetic() -> None:
    """The arithmetic is untouched. Only its licence to speak changed."""

    supported = evidence_for(("Dividend-paying business.",))

    decision = ArtificialCIO().decide(supported)

    measured = [
        score
        for score in (
            supported.quality_score,
            supported.evidence_score,
            supported.valuation_score,
            supported.portfolio_fit_score,
            supported.safety_score,
        )
        if score is not None
    ]

    assert decision.conviction == round(sum(measured) / len(measured))


def test_a_conviction_is_never_labelled_where_it_was_withheld() -> None:
    """ "Low Conviction" is a judgment, and none was made."""

    from app.renderers.brief_language import conviction_label

    assert conviction_label(None) is None
    assert conviction_label(0) == "Low Conviction"


# ── 4. evidence, never an instruction to be bullish ─────────────────


@pytest.mark.parametrize("band", GROUNDED_BANDS)
def test_a_grounded_reading_alone_never_reaches_an_actionable_state(
    band: QualityBand,
) -> None:
    """Convergence supplies evidence; it does not supply permission.

    A company known only through its filings has no valuation, no risk and
    no execution trigger, so knowing its quality — at any band — cannot
    carry it past research. The gates decide that, unchanged.
    """

    grounded = make_grounded(band)

    decision = ArtificialCIO().decide(
        DecisionEvidence(
            symbol="TEST",
            quality_score=grounded.score,
            evidence_score=51,
            portfolio_fit_score=78,
            security_evidenced=True,
            grounded_quality=grounded,
        )
    )

    assert decision.state is DecisionState.INVESTIGATE


def test_a_low_grounded_band_supports_caution_and_not_a_recommendation() -> None:
    """The one direction a quality reading may move a case on its own."""

    poor = ArtificialCIO().decide(
        DecisionEvidence(
            symbol="TEST",
            quality_score=30,
            evidence_score=85,
            valuation_score=85,
            risk_score=20,
            portfolio_fit_score=85,
            actionable_now=True,
            strengths=("Cheap.",),
        )
    )

    assert poor.state is DecisionState.REJECT
