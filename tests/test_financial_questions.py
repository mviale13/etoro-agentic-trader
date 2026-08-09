"""Playbook-owned financial questions: what BANK asks, and what it refuses.

The slice's whole claim in one file. A bank is not a highly levered
industrial, so the fix is not a threshold that knows about banks — it is
the playbook deciding which questions are meaningful, and the analyst
executing what it is handed.
"""

from datetime import UTC, datetime

import pytest

from app.domain.agreement import agreement
from app.domain.financial_question import (
    OWNED,
    QUESTIONS,
    AnswerState,
    FinancialModel,
    FinancialQuestionKey,
    model_for,
    questions_for,
)
from app.domain.financial_statements import StatementKind
from app.domain.financial_understanding import (
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
)
from app.domain.playbook import PlaybookKind
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.services.financial_questions import (
    answer_questions,
    answered,
    inapplicable,
    unanswerable,
)

#: JPMorgan's established facts, as the canonical layer produced them.
JPM = {
    FinancialMeasure.NET_MARGIN: 0.3127,
    FinancialMeasure.REVENUE_GROWTH: 0.0275,
    FinancialMeasure.EARNINGS_GROWTH: -0.0243,
    FinancialMeasure.LIABILITIES_TO_EQUITY: 11.21,
    FinancialMeasure.OPERATING_CASH_FLOW: -147782.0,
}


def figure(label: str = "Total liabilities (a)", value: float = 4062462.0):
    return ReportedFigure(
        label=label,
        column_header="2025",
        printed=f"{value:,.0f}",
        value=value,
        cell=CellReference(table=0, row=26, column=3),
        caption="Consolidated balance sheets",
    )


def established(name: FinancialMeasure, value: float | None) -> EstablishedMeasure:
    if value is None:
        return EstablishedMeasure(
            measure=name,
            value=None,
            absent_because=f"{name.value} is not established: no such line.",
        )

    return EstablishedMeasure(
        measure=name,
        value=value,
        basis=(figure(),),
        stated='"Total liabilities (a)" 4,062,462 over "Total stockholders\' equity"',
        support=agreement("where it prints", ["found"] * 5),
    )


def understanding(**values: float | None) -> FinancialUnderstanding:
    """Established facts, JPMorgan's unless overridden."""

    facts = dict(JPM)
    facts.update(
        {FinancialMeasure(name): value for name, value in values.items()}  # type: ignore[misc]
    )

    return FinancialUnderstanding(
        symbol="JPM",
        source="10-K, via SEC EDGAR",
        reading=Provenance(
            source="computed by this platform",
            observed_at=datetime(2026, 2, 14, tzinfo=UTC),
        ),
        quorate=True,
        observation_count=5,
        quorum=5,
        statements=tuple(StatementKind),
        measures=tuple(
            established(measure, facts.get(measure)) for measure in FinancialMeasure
        ),
    )


def answer(model: FinancialModel, key: FinancialQuestionKey, **values: float | None):
    found = [
        given
        for given in answer_questions(model, understanding(**values))
        if given.question is key
    ]

    assert len(found) == 1

    return found[0]


# ── what BANK declines ───────────────────────────────────────────────


def test_bank_declines_the_industrial_leverage_question() -> None:
    """11.21x must never meet a threshold written for debt/equity."""

    given = answer(FinancialModel.BANK, FinancialQuestionKey.LEVERAGE)

    assert given.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert given.verdict is None
    assert given.score is None
    assert given.because is not None
    assert "deposit-taking bank" in given.because


def test_bank_declines_the_cash_flow_sign_question() -> None:
    given = answer(FinancialModel.BANK, FinancialQuestionKey.CASH_GENERATION)

    assert given.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert given.verdict is None
    assert given.because is not None
    assert "deposit and lending flows" in given.because


def test_a_declined_question_is_refused_before_its_facts_are_read() -> None:
    """A present fact must not quietly override the playbook's refusal."""

    given = answer(
        PlaybookKind.BANK,
        FinancialQuestionKey.LEVERAGE,
        liabilities_to_equity=0.25,
    )

    assert given.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert given.basis == ()


def test_the_decline_is_part_of_the_result_not_an_omission() -> None:
    """Every question the playbook asks is present, whatever became of it."""

    answers = answer_questions(FinancialModel.BANK, understanding())

    assert len(answers) == len(questions_for(FinancialModel.BANK).asks)
    assert {given.question for given in inapplicable(answers)} == {
        FinancialQuestionKey.LEVERAGE,
        FinancialQuestionKey.CASH_GENERATION,
    }


# ── what a non-bank still does ───────────────────────────────────────


def test_a_non_bank_playbook_still_uses_the_industrial_rule() -> None:
    """The same facts, the generic questions, the legacy behaviour."""

    leverage = answer(FinancialModel.GENERIC, FinancialQuestionKey.LEVERAGE)
    cash = answer(FinancialModel.GENERIC, FinancialQuestionKey.CASH_GENERATION)

    assert leverage.state is AnswerState.ANSWERED
    assert leverage.verdict == "weak"
    assert cash.state is AnswerState.ANSWERED
    assert cash.verdict == "weak"


def test_every_model_without_its_own_questions_asks_the_generic_set() -> None:
    for model in FinancialModel:
        if model in OWNED:
            continue

        assert questions_for(model).asks == tuple(FinancialQuestionKey)
        assert questions_for(model).declines == ()


# ── the two classifications are separate ─────────────────────────────


def test_every_business_playbook_but_one_implies_the_generic_model() -> None:
    """The coupling is a default, and it is stated as one."""

    for kind in PlaybookKind:
        selection = model_for(kind)

        assert selection.from_playbook is kind
        assert selection.diverged is False

        if kind is PlaybookKind.BANK:
            assert selection.model is FinancialModel.BANK
        else:
            assert selection.model is FinancialModel.GENERIC


def test_a_diversified_business_is_not_given_a_banks_questions() -> None:
    """JPMorgan's case, and the override this slice refuses to make.

    Its archetype is Diversified because its own filing says its lending,
    services and transaction engines lead together. That the bank
    financial model reads its statements better is a different claim,
    and promoting it here would be reasoning backwards from the answer.
    """

    selection = model_for(PlaybookKind.DIVERSIFIED)

    assert selection.model is FinancialModel.GENERIC

    leverage = answer(selection.model, FinancialQuestionKey.LEVERAGE)

    assert leverage.state is AnswerState.ANSWERED


def test_a_declined_question_names_what_would_answer_it() -> None:
    """An acquisition demand, not a missing threshold."""

    leverage = answer(FinancialModel.BANK, FinancialQuestionKey.LEVERAGE)

    assert leverage.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert "Common Equity Tier 1 ratio" in leverage.needs
    assert "the regulatory leverage ratio" in leverage.needs


def test_a_demand_names_the_facts_beneath_a_judgment_not_the_judgment() -> None:
    """Cash generation asks for deposits and their share, never their quality.

    "deposit funding quality" stood in this tuple until a corpus
    established that no filer prints it. A decline exists because a
    question cannot be answered yet, so a demand phrased as a conclusion
    asks to be handed the answer and can never be satisfied by evidence.
    """

    cash = answer(FinancialModel.BANK, FinancialQuestionKey.CASH_GENERATION)

    assert cash.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert "customer deposits" in cash.needs
    assert "their share of total liabilities" in cash.needs
    assert "the liquidity coverage ratio" in cash.needs


#: Words that name a conclusion rather than a figure. One-directional:
#: a demand containing one is wrong, and a demand containing none is not
#: thereby proved right — the list guards against the mistake already
#: made, and is not a definition of evidence.
JUDGMENT_WORDS = (
    "quality",
    "strength",
    "strong",
    "weak",
    "adequacy",
    "adequate",
    "health",
    "healthy",
    "sustainable",
    "attractive",
)


def test_no_model_demands_a_judgment_as_evidence() -> None:
    """The contract's evidence field holds facts, across every model."""

    for model, questions in OWNED.items():
        for decline in questions.declines:
            for demand in decline.needs:
                for word in JUDGMENT_WORDS:
                    assert word not in demand.casefold(), (
                        f"{model.value} asks for {demand!r} to answer "
                        f"{decline.question.value}, which names a conclusion "
                        "rather than a fact this platform could establish."
                    )


# ── what BANK answers, without copying a threshold ───────────────────


def test_bank_reuses_a_shared_question_without_copying_its_thresholds() -> None:
    growth = answer(FinancialModel.BANK, FinancialQuestionKey.REVENUE_GROWTH)
    industrial = answer(FinancialModel.GENERIC, FinancialQuestionKey.REVENUE_GROWTH)

    assert growth.state is AnswerState.ANSWERED
    assert growth.verdict == industrial.verdict
    assert growth.score == industrial.score

    # The threshold lives with the analyst that owns it, and the BANK
    # playbook declares no numbers of its own.
    assert not hasattr(questions_for(FinancialModel.BANK), "thresholds")


def test_bank_profitability_is_about_what_a_bank_actually_prints() -> None:
    """Narrowed to net margin: a bank's statement has no gross profit line."""

    given = answer(FinancialModel.BANK, FinancialQuestionKey.PROFITABILITY)
    industrial = answer(FinancialModel.GENERIC, FinancialQuestionKey.PROFITABILITY)

    assert given.state is AnswerState.ANSWERED
    assert given.confidence == pytest.approx(1.0)
    assert given.gaps == ()

    # The industrial question consults three margins and JPM prints one,
    # so it answers partially — the behaviour the analysts always had.
    assert industrial.state is AnswerState.ANSWERED
    assert industrial.confidence == pytest.approx(1 / 3)
    assert len(industrial.gaps) == 2


# ── evidence gaps, and what they are not ─────────────────────────────


def test_a_meaningful_question_with_no_established_fact_is_an_evidence_gap() -> None:
    """Not a refusal: the question is right, the fact is missing."""

    given = answer(
        PlaybookKind.BANK,
        FinancialQuestionKey.EARNINGS_GROWTH,
        earnings_growth=None,
    )

    assert given.state is AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS
    assert given.because is not None
    assert "not established" in given.because


def test_an_evidence_gap_and_an_inapplicable_question_are_never_one_state() -> None:
    answers = answer_questions(FinancialModel.BANK, understanding(earnings_growth=None))

    assert {given.question for given in unanswerable(answers)} == {
        FinancialQuestionKey.EARNINGS_GROWTH
    }
    assert {given.question for given in inapplicable(answers)} == {
        FinancialQuestionKey.LEVERAGE,
        FinancialQuestionKey.CASH_GENERATION,
    }


def test_a_missing_fact_is_never_filled_from_a_provider() -> None:
    """The two routes do not blend, one layer further up."""

    given = answer(
        PlaybookKind.BANK,
        FinancialQuestionKey.REVENUE_GROWTH,
        revenue_growth=None,
    )

    assert given.state is AnswerState.NOT_ANSWERABLE_FROM_ESTABLISHED_FACTS
    assert given.verdict is None
    assert given.score is None
    assert given.evidence == ()
    assert given.basis == ()


# ── provenance survives the layer ────────────────────────────────────


def test_evidence_references_survive_from_the_facts_into_the_answer() -> None:
    given = answer(FinancialModel.BANK, FinancialQuestionKey.PROFITABILITY)

    assert given.basis
    assert all(isinstance(cell, ReportedFigure) for cell in given.basis)
    assert given.basis[0].cell.stated() == "table 0, row 26, column 3"
    assert any("Total liabilities (a)" in line for line in given.evidence)


def test_an_answered_question_carries_the_model_that_asked_it() -> None:
    for given in answer_questions(FinancialModel.BANK, understanding()):
        assert given.model is FinancialModel.BANK
        assert given.asks == QUESTIONS[given.question].asks


def test_a_declined_question_yields_nothing_a_consumer_could_score_from() -> None:
    """The executive layer must not be able to recreate the refusal's score.

    The refusal has to be load-bearing rather than presentational: an
    answer that carried the figure and left the verdict blank would let
    any consumer downstream apply the industrial table itself and undo
    the playbook's decision one layer up.
    """

    answers = answer_questions(FinancialModel.BANK, understanding())

    for given in inapplicable(answers):
        assert given.verdict is None
        assert given.score is None
        assert given.confidence is None
        assert given.evidence == ()
        assert given.basis == ()
        assert given.gaps == ()


def test_the_bank_can_state_all_three_things_it_knows() -> None:
    """The stopping point: answered, not yet answerable, not applicable."""

    answers = answer_questions(FinancialModel.BANK, understanding(earnings_growth=None))

    assert answered(answers)
    assert unanswerable(answers)
    assert inapplicable(answers)

    assert len(answered(answers)) + len(unanswerable(answers)) + len(
        inapplicable(answers)
    ) == len(answers)
