"""Business quality, from the filing rather than from three provider proxies.

The score this replaces asked whether a company was large, profitable
and dividend-paying, and gave AAPL, PG, DIS and JPM the identical
answer of 80 — a hardware compounder, a consumer staple, a diversified
media company and a bank, indistinguishable.

What is tested here is mostly what the new score *refuses* to do:
score an unanswered question, penalise a company for evidence this
platform could not read, or claim to measure business quality entire.
"""

import pytest

from app.domain.business_quality import (
    MINIMUM_ANSWERED,
    QualityBand,
    assess,
    band_for,
    sense_of,
)
from app.domain.financial_question import (
    AnswerState,
    FinancialModel,
    FinancialQuestionKey,
    QuestionAnswer,
)
from app.domain.finding import Sense

PROFIT = FinancialQuestionKey.PROFITABILITY
REVENUE = FinancialQuestionKey.REVENUE_GROWTH
EARNINGS = FinancialQuestionKey.EARNINGS_GROWTH


def answered(question: FinancialQuestionKey, verdict: str) -> QuestionAnswer:
    return QuestionAnswer(
        question=question,
        model=FinancialModel.GENERIC,
        state=AnswerState.ANSWERED,
        verdict=verdict,
        evidence=(f"{question.value} reads {verdict}.",),
    )


def unavailable(question: FinancialQuestionKey) -> QuestionAnswer:
    return QuestionAnswer(
        question=question,
        model=FinancialModel.GENERIC,
        state=AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS,
        because="No figure for it is established in this filing.",
    )


def declined(question: FinancialQuestionKey) -> QuestionAnswer:
    return QuestionAnswer(
        question=question,
        model=FinancialModel.BANK,
        state=AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK,
        because="This model does not ask it.",
        needs=("regulatory capital",),
    )


def quality(*answers: QuestionAnswer):
    return assess("EXA", answers, source="a 10-K")


# ── the verdict mapping ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("verdict", "expected"),
    [
        ("excellent", Sense.FAVOURABLE),
        ("strong", Sense.FAVOURABLE),
        ("moderate", Sense.NEUTRAL),
        ("weak", Sense.ADVERSE),
        ("declining", Sense.ADVERSE),
    ],
)
def test_the_verdict_mapping_is_declared_once(verdict: str, expected: Sense) -> None:
    assert sense_of(verdict) is expected


def test_neutral_and_unfavourable_stay_visibly_different() -> None:
    """
    Neither earns a point, and they are not the same finding.

    *Moderate* is a business performing adequately; *weak* is one
    performing badly. A column of bare zeroes cannot tell an investor
    which they are reading, so the sense travels.
    """

    assessed = quality(
        answered(PROFIT, "excellent"),
        answered(REVENUE, "moderate"),
        answered(EARNINGS, "weak"),
    )

    by_question = {factor.question: factor for factor in assessed.factors}

    assert by_question[REVENUE].points == 0
    assert by_question[EARNINGS].points == 0

    assert by_question[REVENUE].sense is Sense.NEUTRAL
    assert by_question[EARNINGS].sense is Sense.ADVERSE

    assert by_question[REVENUE].status == "neutral"
    assert by_question[EARNINGS].status == "not earned"


def test_an_unrecognised_verdict_is_neutral_never_adverse() -> None:
    """An unknown word is this platform's gap, and gaps are not penalties."""

    assert sense_of("sideways") is Sense.NEUTRAL
    assert sense_of(None) is Sense.NEUTRAL


def test_nothing_ever_subtracts() -> None:
    assessed = quality(
        answered(PROFIT, "weak"),
        answered(REVENUE, "declining"),
        answered(EARNINGS, "weak"),
    )

    assert all(factor.points >= 0 for factor in assessed.factors)
    assert assessed.favourable == 0
    assert assessed.band is QualityBand.LOW


# ── applicability: only answered factors count ──────────────────────


def test_an_unavailable_factor_stays_out_of_the_denominator() -> None:
    """
    The rule this score exists to keep: not knowing is never a mark against.

    Two answered factors, both favourable, and a third nobody could
    read. The share is 2 of 2, not 2 of 3.
    """

    assessed = quality(
        answered(PROFIT, "excellent"),
        answered(EARNINGS, "strong"),
        unavailable(REVENUE),
    )

    assert assessed.answered == 2
    assert assessed.favourable == 2
    assert assessed.band is QualityBand.HIGH


def test_an_inapplicable_factor_stays_out_of_the_denominator() -> None:
    assessed = quality(
        answered(PROFIT, "excellent"),
        answered(EARNINGS, "strong"),
        declined(REVENUE),
    )

    assert assessed.answered == 2
    assert assessed.band is QualityBand.HIGH


def test_unavailable_and_inapplicable_are_different_states() -> None:
    """A reader must never have to infer which a blank space was."""

    assessed = quality(
        answered(PROFIT, "strong"),
        unavailable(REVENUE),
        declined(EARNINGS),
    )

    by_question = {factor.question: factor for factor in assessed.factors}

    assert by_question[REVENUE].status == "unavailable"
    assert by_question[EARNINGS].status == "not applicable"

    # And each keeps the wording of the layer that found it.
    assert by_question[REVENUE].because
    assert by_question[EARNINGS].because


def test_every_candidate_factor_appears_whatever_became_of_it() -> None:
    assessed = quality(answered(PROFIT, "strong"))

    assert len(assessed.factors) == 3


# ── the minimum evidence rule ───────────────────────────────────────


def test_one_answered_factor_is_never_enough_to_band() -> None:
    """
    TSLA's case. A single reading is as easily a gap as a verdict.

    Crucially it is UNKNOWN and not LOW: reporting a company as weak
    because this platform could read one number is the substitution
    every honesty rule here exists to refuse.
    """

    excellent = quality(answered(PROFIT, "excellent"), unavailable(REVENUE))
    weak = quality(answered(PROFIT, "weak"), unavailable(REVENUE))

    assert excellent.band is QualityBand.UNKNOWN
    assert weak.band is QualityBand.UNKNOWN

    assert excellent.score is None
    assert weak.score is None

    assert "not a finding about the company" in weak.stated()


def test_no_answered_factor_is_unknown_not_low() -> None:
    assessed = quality(unavailable(PROFIT), unavailable(REVENUE))

    assert assessed.band is QualityBand.UNKNOWN
    assert assessed.answered == 0


# ── the bands ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("favourable", "answered_count", "expected"),
    [
        # Regression-pinned. Share thresholds, not absolute counts:
        # two thirds for HIGH, one third for MEDIUM.
        (3, 3, QualityBand.HIGH),
        (2, 3, QualityBand.HIGH),
        (1, 3, QualityBand.MEDIUM),
        (0, 3, QualityBand.LOW),
        (2, 2, QualityBand.HIGH),
        (1, 2, QualityBand.MEDIUM),
        (0, 2, QualityBand.LOW),
        # Below the minimum, whatever the share.
        (1, 1, QualityBand.UNKNOWN),
        (0, 1, QualityBand.UNKNOWN),
        (0, 0, QualityBand.UNKNOWN),
    ],
)
def test_the_bands_are_pinned(
    favourable: int,
    answered_count: int,
    expected: QualityBand,
) -> None:
    assert band_for(favourable, answered_count) is expected


def test_a_company_with_fewer_readable_factors_is_not_banded_lower() -> None:
    """
    The defect the score decomposition exposed the moment it shipped.

    Under absolute counts, two favourable of two answered banded below
    three of three — punishing a company for a figure this platform
    could not read. Share thresholds are why that cannot happen.
    """

    three = quality(
        answered(PROFIT, "strong"),
        answered(REVENUE, "strong"),
        answered(EARNINGS, "strong"),
    )

    two = quality(
        answered(PROFIT, "strong"),
        answered(EARNINGS, "strong"),
        unavailable(REVENUE),
    )

    assert three.band is two.band is QualityBand.HIGH
    assert three.score == two.score


def test_the_minimum_is_stated_rather_than_hidden() -> None:
    assert MINIMUM_ANSWERED == 2


# ── what it claims to be ────────────────────────────────────────────


def test_the_arithmetic_is_shown_whole() -> None:
    assessed = quality(
        answered(PROFIT, "strong"),
        answered(REVENUE, "weak"),
        answered(EARNINGS, "strong"),
    )

    assert assessed.stated() == "2 favourable of 3 answered → 67% → HIGH → 80."


def test_the_excluded_dimensions_are_carried_with_their_reasons() -> None:
    """
    A reader who knows leverage matters is owed the reason it is absent.

    Otherwise the omission reads as an oversight — or worse, as the
    platform having found nothing to say about it.
    """

    assessed = quality(answered(PROFIT, "strong"), answered(REVENUE, "strong"))

    excluded = {item.name: item.because for item in assessed.excluded}

    assert set(excluded) == {"Cash generation", "Leverage"}

    # Both are statements about this platform's evidence, never about a
    # company — and the leverage one names why it cannot be repaired here.
    assert "none of the companies" in excluded["Cash generation"]
    assert "deposits it exists to take" in excluded["Leverage"]


def test_leverage_never_reaches_the_score() -> None:
    """
    JPM's case. Its generic leverage answer is `weak`, score 0, because
    a bank's playbook reads Diversified and it is asked the industrial
    question. That must not become a judgment about the business.
    """

    with_leverage = quality(
        answered(PROFIT, "excellent"),
        answered(REVENUE, "weak"),
        answered(EARNINGS, "declining"),
        answered(FinancialQuestionKey.LEVERAGE, "weak"),
    )

    assert with_leverage.answered == 3
    assert all(
        factor.question is not FinancialQuestionKey.LEVERAGE
        for factor in with_leverage.factors
    )
    assert with_leverage.band is QualityBand.MEDIUM


def test_it_says_what_it_measures_and_not_more() -> None:
    assessed = quality(answered(PROFIT, "strong"), answered(REVENUE, "strong"))

    assert assessed.label == "grounded profitability and growth quality"
