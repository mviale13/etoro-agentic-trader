"""Run a playbook's financial questions against established facts.

The analyst's whole job in the new shape, and the boundaries are the
design. It **executes** a question the playbook chose, against facts the
canonical layer established, with a rule table the analyst package owns.
It selects nothing, extracts nothing, and substitutes nothing.

What it may not do is the more useful list. It never reads a filing —
the facts arrive established or not at all. It never reaches for
provider data when a fact is missing; a missing fact is an answer.
And it never scores a question its playbook declined, which is what
keeps a refusal from being undone one layer down.
"""

from __future__ import annotations

from typing import Any

from app.analysts.analyst import Analyst
from app.analysts.balance_sheet_analyst import BalanceSheetAnalyst
from app.analysts.cash_flow_analyst import CashFlowAnalyst
from app.analysts.filing_analysts import stated_value
from app.analysts.growth_analyst import GrowthAnalyst
from app.analysts.profitability_analyst import ProfitabilityAnalyst
from app.domain.analyst_observation import AnalystObservation
from app.domain.company_facts import CompanyFacts
from app.domain.financial_question import (
    QUESTIONS,
    AnswerState,
    FinancialModel,
    FinancialQuestion,
    FinancialQuestionKey,
    QuestionAnswer,
    questions_for,
)
from app.domain.financial_understanding import FinancialUnderstanding
from app.domain.opinion import Opinion
from app.domain.research_plan import AnalystKey
from app.domain.tabular_evidence import ReportedFigure

#: Which analyst owns each rule table. The thresholds stay where they
#: have always lived; this only says who to ask.
RULES: dict[AnalystKey, Analyst[CompanyFacts, Any]] = {
    AnalystKey.PROFITABILITY: ProfitabilityAnalyst(),
    AnalystKey.GROWTH: GrowthAnalyst(),
    AnalystKey.BALANCE_SHEET: BalanceSheetAnalyst(),
    AnalystKey.CASH_FLOW: CashFlowAnalyst(),
}


def answer_questions(
    model: FinancialModel,
    understanding: FinancialUnderstanding,
) -> tuple[QuestionAnswer, ...]:
    """Every question this financial model asks, answered or explicitly not.

    One entry per question the model asks, always. A question the model
    declined is present as a decline, and a question whose facts are
    missing is present as an evidence gap — so a reader never has to
    infer which of the two a blank space was.

    Note what is *not* a parameter: the business playbook. Which company
    this is has already been decided elsewhere, and what governs here is
    only which financial language reads it.
    """

    owned = questions_for(model)

    return tuple(_answer(QUESTIONS[key], model, understanding) for key in owned.asks)


def _answer(
    question: FinancialQuestion,
    model: FinancialModel,
    understanding: FinancialUnderstanding,
) -> QuestionAnswer:
    """One question: declined, unanswerable, or run through its rule."""

    declined = questions_for(model).declined(question.key)

    if declined is not None:
        # Checked before the facts are even gathered. A declined
        # question is not a question this platform failed to answer,
        # and looking at the facts first would invite exactly that
        # confusion — worse, it would let a present fact quietly
        # override the playbook's refusal.
        return QuestionAnswer(
            question=question.key,
            model=model,
            state=AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK,
            because=declined.reason,
            needs=declined.needs,
        )

    consulted = questions_for(model).consults(question)

    observations: list[AnalystObservation] = []
    basis: list[ReportedFigure] = []
    gaps: list[str] = []

    for measure in consulted:
        established = understanding.of(measure)

        if established is None or not established.is_established:
            gaps.append(
                established.absent_because
                if established is not None and established.absent_because
                else f"{measure.value} was not measured."
            )
            continue

        assert established.value is not None

        observations.append(
            AnalystObservation(
                key=question.rule_key(measure),
                label=established.label,
                value=established.value,
                stated=(
                    f"{established.label} is {stated_value(established)} — "
                    f"{established.stated}."
                ),
            )
        )
        basis.extend(established.basis)

    if not observations:
        # Nothing established answers this question. Not a refusal — a
        # meaningful question this platform cannot yet reach, and the
        # gaps below name exactly which facts would reach it.
        return QuestionAnswer(
            question=question.key,
            model=model,
            state=AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS,
            gaps=tuple(gaps),
            because=(
                gaps[0]
                if gaps
                else "This playbook consults no measure for this question."
            ),
        )

    return _scored(
        question,
        model,
        tuple(observations),
        tuple(basis),
        tuple(gaps),
        consulted=len(consulted),
    )


def _scored(
    question: FinancialQuestion,
    model: FinancialModel,
    observations: tuple[AnalystObservation, ...],
    basis: tuple[ReportedFigure, ...],
    gaps: tuple[str, ...],
    consulted: int,
) -> QuestionAnswer:
    """The owning rule table applied to established facts, and nothing else.

    Confidence is the share of the question's own inputs that were
    established — the arithmetic the analysts have always used, so a
    question answered from one of three margins reads exactly as it
    always did rather than as a complete answer.
    """

    rules = RULES[question.interpreted_by]

    score = round(
        sum(rules.score_observation(observed) for observed in observations)
        / len(observations)
    )

    opinion: Opinion[Any] = rules.build_opinion(
        score=score,
        confidence=len(observations) / consulted,
        evidence=tuple(observed.stated for observed in observations),
        uncertainty=gaps,
    )

    return QuestionAnswer(
        question=question.key,
        model=model,
        state=AnswerState.ANSWERED,
        verdict=str(opinion.verdict.value),
        score=opinion.score,
        confidence=opinion.confidence,
        evidence=opinion.evidence,
        basis=basis,
        gaps=gaps,
    )


def answered(answers: tuple[QuestionAnswer, ...]) -> tuple[QuestionAnswer, ...]:
    """The questions this playbook asked and the facts could answer."""

    return tuple(answer for answer in answers if answer.is_answered)


def unanswerable(answers: tuple[QuestionAnswer, ...]) -> tuple[QuestionAnswer, ...]:
    """Meaningful questions whose filing-grade fact is not established.

    The roadmap, not a failure list: each of these names a fact worth
    acquiring, and the next slice is earned by what appears here.
    """

    return tuple(
        answer
        for answer in answers
        if answer.state is AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS
    )


def inapplicable(answers: tuple[QuestionAnswer, ...]) -> tuple[QuestionAnswer, ...]:
    """Generic questions this playbook holds to be the wrong questions."""

    return tuple(
        answer
        for answer in answers
        if answer.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    )


def declined_keys(model: FinancialModel) -> frozenset[FinancialQuestionKey]:
    """What this model refuses, without needing any facts to say so."""

    return frozenset(decline.question for decline in questions_for(model).declines)
