"""What the filing establishes about how good the business is.

The replacement for a quality score that asked three questions of a
data provider — *is it large, does it earn, does it pay a dividend* —
and gave four completely different companies the identical answer.
Measured: AAPL, PG, DIS and JPM all scored 80, because all four are
large, profitable and dividend-paying. A bank, a consumer staple, a
diversified media company and a hardware compounder, indistinguishable.

This asks instead what the company's own audited statements support,
through the questions the governing financial model already declares.
Nothing here reads a filing, calls a provider or asks a model: it
consumes `QuestionAnswer`s that an existing grounded rule table
produced, and turns them into one banded score.

## What it is not

**It is not a complete measure of business quality**, and it says so in
its own label. Returns on capital, capital allocation, moat, customer
concentration and reinvestment effectiveness are not here — not
because they do not matter, but because this platform has no canonical
measure for any of them, and inventing one would be the estimated
figure invariant 1 forbids. What this measures is **grounded
profitability and growth quality under currently established
evidence**, which is a narrower claim and a true one.

Two dimensions were excluded deliberately rather than for want of a
rule, and both exclusions are carried on the result so a reader can
see them:

- **Cash generation**, because operating and free cash flow are
  established for 0 of the 24 companies whose statements have reached
  quorum. There is nothing to score.
- **Leverage**, because the financial model that governs a company is
  derived from its business playbook, and JPMorgan's playbook is
  `Diversified Business` — so its leverage question is answered with
  the *industrial* threshold and returns `weak`, score 0. The
  liabilities that make a bank look levered are the deposits it exists
  to take. That limitation is known, documented, and out of reach
  until a Prudential Understanding layer exists; promoting it into a
  headline company-quality judgment would publish it as a finding
  about the business.

## Applicability

Taken whole from `AnswerState`, unchanged. A factor enters the
arithmetic only when it is `ANSWERED`. A factor that is not applicable
to this financial model, or that the established facts cannot answer,
stays visible with the reason its own layer worded — and **stays out
of the denominator**. Not knowing something is never a mark against a
company.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_question import (
    AnswerState,
    FinancialQuestionKey,
    QuestionAnswer,
)
from app.domain.finding import Sense
from app.domain.tabular_evidence import ReportedFigure

#: The questions this score is built from, in the order it reads them.
#:
#: Three, and each is here because a grounded rule table already answers
#: it from established figures. The set grows when a measure and its
#: rule table both exist — never because a dimension is conventional.
QUALITY_QUESTIONS: tuple[FinancialQuestionKey, ...] = (
    FinancialQuestionKey.PROFITABILITY,
    FinancialQuestionKey.REVENUE_GROWTH,
    FinancialQuestionKey.EARNINGS_GROWTH,
)


@dataclass(frozen=True, slots=True)
class ExcludedDimension:
    """A quality dimension deliberately kept out of the score.

    Carried on the result rather than left implicit. A reader who knows
    that leverage matters is owed the reason it is not here — otherwise
    the omission reads as an oversight, or worse, as the platform
    having found nothing to say.
    """

    name: str
    because: str


#: Why the two obvious absences are absent. Both are statements about
#: this platform's evidence, never about any company.
EXCLUDED: tuple[ExcludedDimension, ...] = (
    ExcludedDimension(
        name="Cash generation",
        because=(
            "Operating and free cash flow are established for none of the "
            "companies whose statements have reached quorum, so there is "
            "nothing to score. The figures are asked for and reported as "
            "absent; no company is marked down for it."
        ),
    ),
    ExcludedDimension(
        name="Leverage",
        because=(
            "A company's financial model follows its business playbook, so "
            "a bank whose playbook reads Diversified is asked the "
            "industrial leverage question — and the liabilities that make "
            "it look levered are the deposits it exists to take. That "
            "limitation is known and cannot be repaired without a "
            "prudential evidence layer this platform does not have, so it "
            "is kept out of company quality rather than published as a "
            "finding about the business."
        ),
    ),
)


class QualityBand(StrEnum):
    """How good the established figures say the business is."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    #: Too few questions were answered to band anything. Never `LOW`:
    #: one answered factor is a gap in the reading, and reporting it as
    #: a weak business would be exactly the substitution this platform
    #: exists to refuse.
    UNKNOWN = "UNKNOWN"


#: How many answered factors a band needs. One is never enough — a
#: single reading is as easily a gap as a verdict.
MINIMUM_ANSWERED = 2

#: The band thresholds, as the share of answered factors that came back
#: favourable. Written as integer ratios rather than floats so a
#: reader can check them and no company lands on a rounding edge:
#: `favourable * 3 >= answered * 2` is two-thirds, exactly.
HIGH_NUMERATOR, HIGH_DENOMINATOR = 2, 3
MEDIUM_NUMERATOR, MEDIUM_DENOMINATOR = 1, 3

#: What each band is worth on the dossier's 0-100 scale. Unchanged from
#: the score this replaces, so a number moving is a change in evidence
#: rather than a change in ruler.
BAND_SCORES: dict[QualityBand, int] = {
    QualityBand.HIGH: 80,
    QualityBand.MEDIUM: 62,
    QualityBand.LOW: 40,
}

#: The rule tables' own verdict words, mapped to a contribution once.
#:
#: Declared here and nowhere else. The mapping is deliberately coarse —
#: a point or no point — because this platform measures no weights, and
#: a `+18` beside a verdict the analyst worded as "strong" would be a
#: number nobody computed.
FAVOURABLE_VERDICTS = frozenset({"excellent", "strong"})
NEUTRAL_VERDICTS = frozenset({"moderate"})
UNFAVOURABLE_VERDICTS = frozenset({"weak", "declining"})


def sense_of(verdict: str | None) -> Sense:
    """How a verdict reads, where the mapping declares it.

    Neutral and unfavourable both earn nothing and must stay visibly
    different: *moderate* is a business performing adequately, *weak*
    is one performing badly, and a column of bare zeroes cannot tell an
    investor which they are looking at.

    A verdict this mapping does not know is neutral rather than
    unfavourable — an unrecognised word is this platform's gap, and
    gaps are never scored against a company.
    """

    word = (verdict or "").strip().lower()

    if word in FAVOURABLE_VERDICTS:
        return Sense.FAVOURABLE

    if word in UNFAVOURABLE_VERDICTS:
        return Sense.ADVERSE

    return Sense.NEUTRAL


@dataclass(frozen=True, slots=True)
class QualityFactor:
    """One candidate factor, scored or explicitly not.

    Present for every question in `QUALITY_QUESTIONS`, always — a
    factor that was not applicable and a factor nobody could answer are
    different states, and a reader must never have to infer which a
    blank space was.
    """

    question: FinancialQuestionKey

    #: The question in words, from the contract that owns it.
    asks: str

    state: AnswerState

    #: The rule table's own verdict word, where one ran.
    verdict: str | None

    #: What it contributed. Zero for everything that is not favourable,
    #: and never negative: this score has no penalties.
    points: int

    sense: Sense

    #: How the answer is evidenced, one line per measure consumed, and
    #: the checked cells beneath it — both carried from the canonical
    #: facts rather than restated.
    evidence: tuple[str, ...] = ()
    basis: tuple[ReportedFigure, ...] = ()

    #: Measures the question consults that are not established.
    gaps: tuple[str, ...] = ()

    #: Why there is no answer: the consensus's wording for an evidence
    #: gap, the model's wording for a question it declined.
    because: str | None = None

    #: What evidence would answer a declined question.
    needs: tuple[str, ...] = ()

    @property
    def is_answered(self) -> bool:
        return self.state is AnswerState.ANSWERED

    @property
    def counts(self) -> bool:
        """Whether this factor enters the arithmetic at all."""

        return self.is_answered

    @property
    def status(self) -> str:
        """What a surface shows where there is no contribution."""

        if self.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK:
            return "not applicable"

        if self.state is AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS:
            return "unavailable"

        return "not earned" if self.sense is Sense.ADVERSE else "neutral"


@dataclass(frozen=True, slots=True)
class BusinessQuality:
    """The grounded quality assessment, and the arithmetic that reached it.

    The score, the band and every worded part come from this one
    object, produced by one execution. Nothing downstream re-derives a
    verdict or authors an explanation beside a number it did not
    compute.
    """

    symbol: str

    factors: tuple[QualityFactor, ...]
    excluded: tuple[ExcludedDimension, ...]

    favourable: int
    answered: int

    band: QualityBand

    #: Where the facts came from, carried for the surface that shows it.
    source: str

    @property
    def score(self) -> int | None:
        """The 0-100 figure, or nothing where the band is UNKNOWN."""

        return BAND_SCORES.get(self.band)

    @property
    def share(self) -> float | None:
        """The favourable share of answered factors."""

        if not self.answered:
            return None

        return self.favourable / self.answered

    @property
    def label(self) -> str:
        """What this measures, stated so it cannot be over-read."""

        return "grounded profitability and growth quality"

    def stated(self) -> str:
        """The whole arithmetic as one checkable line."""

        if self.band is QualityBand.UNKNOWN:
            return (
                f"{self.answered} of {len(self.factors)} factors answered — "
                f"fewer than {MINIMUM_ANSWERED}, so no band is claimed. That "
                "is a limit of the established evidence, not a finding about "
                "the company."
            )

        share = self.share or 0.0

        return (
            f"{self.favourable} favourable of {self.answered} answered "
            f"→ {share:.0%} → {self.band.value} → {self.score}."
        )


def band_for(favourable: int, answered: int) -> QualityBand:
    """The band these counts reach, by integer arithmetic only.

    Share thresholds rather than absolute counts, because applicability
    varies: a company whose growth could not be read has two answered
    factors, and an absolute rule would band it below one with three
    for a reason that is nothing to do with the business. That was the
    defect the score decomposition made visible the moment it shipped.
    """

    if answered < MINIMUM_ANSWERED:
        return QualityBand.UNKNOWN

    if favourable * HIGH_DENOMINATOR >= answered * HIGH_NUMERATOR:
        return QualityBand.HIGH

    if favourable * MEDIUM_DENOMINATOR >= answered * MEDIUM_NUMERATOR:
        return QualityBand.MEDIUM

    return QualityBand.LOW


def assess(
    symbol: str,
    answers: tuple[QuestionAnswer, ...],
    source: str,
) -> BusinessQuality:
    """Band the established figures, from answers another layer produced.

    Deterministic and total: the same answers produce the same
    assessment, and every factor in `QUALITY_QUESTIONS` appears in the
    result whether or not it was answerable.
    """

    by_key = {answer.question: answer for answer in answers}

    factors = tuple(_factor(key, by_key.get(key)) for key in QUALITY_QUESTIONS)

    counted = [factor for factor in factors if factor.counts]

    favourable = sum(factor.points for factor in counted)

    return BusinessQuality(
        symbol=symbol.upper().strip(),
        factors=factors,
        excluded=EXCLUDED,
        favourable=favourable,
        answered=len(counted),
        band=band_for(favourable, len(counted)),
        source=source,
    )


def _factor(
    key: FinancialQuestionKey,
    answer: QuestionAnswer | None,
) -> QualityFactor:
    """One candidate factor, from its answer or from its absence."""

    from app.domain.financial_question import QUESTIONS

    asks = QUESTIONS[key].asks

    if answer is None:
        # The governing model does not ask this question at all, which
        # is applicability rather than a gap in evidence.
        return QualityFactor(
            question=key,
            asks=asks,
            state=AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK,
            verdict=None,
            points=0,
            sense=Sense.NEUTRAL,
            because=(
                "The financial model governing this company does not ask this question."
            ),
        )

    sense = sense_of(answer.verdict) if answer.is_answered else Sense.NEUTRAL

    return QualityFactor(
        question=key,
        asks=asks,
        state=answer.state,
        verdict=answer.verdict,
        points=1 if (answer.is_answered and sense is Sense.FAVOURABLE) else 0,
        sense=sense,
        evidence=answer.evidence,
        basis=answer.basis,
        gaps=answer.gaps,
        because=answer.because,
        needs=answer.needs,
    )
