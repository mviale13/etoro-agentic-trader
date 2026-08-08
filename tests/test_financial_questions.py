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
    FinancialQuestionKey,
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


def answer(playbook: PlaybookKind, key: FinancialQuestionKey, **values: float | None):
    found = [
        given
        for given in answer_questions(playbook, understanding(**values))
        if given.question is key
    ]

    assert len(found) == 1

    return found[0]


# ── what BANK declines ───────────────────────────────────────────────


def test_bank_declines_the_industrial_leverage_question() -> None:
    """11.21x must never meet a threshold written for debt/equity."""

    given = answer(PlaybookKind.BANK, FinancialQuestionKey.LEVERAGE)

    assert given.state is AnswerState.NOT_APPLICABLE_FOR_PLAYBOOK
    assert given.verdict is None
    assert given.score is None
    assert given.because is not None
    assert "deposit-taking bank" in given.because


def test_bank_declines_the_cash_flow_sign_question() -> None:
    given = answer(PlaybookKind.BANK, FinancialQuestionKey.CASH_GENERATION)

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

    answers = answer_questions(PlaybookKind.BANK, understanding())

    assert len(answers) == len(questions_for(PlaybookKind.BANK).asks)
    assert {given.question for given in inapplicable(answers)} == {
        FinancialQuestionKey.LEVERAGE,
        FinancialQuestionKey.CASH_GENERATION,
    }


# ── what a non-bank still does ───────────────────────────────────────


def test_a_non_bank_playbook_still_uses_the_industrial_rule() -> None:
    """The same facts, the generic questions, the legacy behaviour."""

    leverage = answer(PlaybookKind.INDUSTRIAL, FinancialQuestionKey.LEVERAGE)
    cash = answer(PlaybookKind.INDUSTRIAL, FinancialQuestionKey.CASH_GENERATION)

    assert leverage.state is AnswerState.ANSWERED
    assert leverage.verdict == "weak"
    assert cash.state is AnswerState.ANSWERED
    assert cash.verdict == "weak"


def test_every_playbook_without_its_own_questions_asks_the_generic_set() -> None:
    for kind in PlaybookKind:
        if kind in OWNED:
            continue

        assert questions_for(kind).asks == tuple(FinancialQuestionKey)
        assert questions_for(kind).declines == ()


# ── what BANK answers, without copying a threshold ───────────────────


def test_bank_reuses_a_shared_question_without_copying_its_thresholds() -> None:
    growth = answer(PlaybookKind.BANK, FinancialQuestionKey.REVENUE_GROWTH)
    industrial = answer(PlaybookKind.INDUSTRIAL, FinancialQuestionKey.REVENUE_GROWTH)

    assert growth.state is AnswerState.ANSWERED
    assert growth.verdict == industrial.verdict
    assert growth.score == industrial.score

    # The threshold lives with the analyst that owns it, and the BANK
    # playbook declares no numbers of its own.
    assert not hasattr(questions_for(PlaybookKind.BANK), "thresholds")


def test_bank_profitability_is_about_what_a_bank_actually_prints() -> None:
    """Narrowed to net margin: a bank's statement has no gross profit line."""

    given = answer(PlaybookKind.BANK, FinancialQuestionKey.PROFITABILITY)
    industrial = answer(PlaybookKind.INDUSTRIAL, FinancialQuestionKey.PROFITABILITY)

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
    answers = answer_questions(PlaybookKind.BANK, understanding(earnings_growth=None))

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
    given = answer(PlaybookKind.BANK, FinancialQuestionKey.PROFITABILITY)

    assert given.basis
    assert all(isinstance(cell, ReportedFigure) for cell in given.basis)
    assert given.basis[0].cell.stated() == "table 0, row 26, column 3"
    assert any("Total liabilities (a)" in line for line in given.evidence)


def test_an_answered_question_carries_the_playbook_that_asked_it() -> None:
    for given in answer_questions(PlaybookKind.BANK, understanding()):
        assert given.playbook is PlaybookKind.BANK
        assert given.asks == QUESTIONS[given.question].asks


def test_a_declined_question_yields_nothing_a_consumer_could_score_from() -> None:
    """The executive layer must not be able to recreate the refusal's score.

    The refusal has to be load-bearing rather than presentational: an
    answer that carried the figure and left the verdict blank would let
    any consumer downstream apply the industrial table itself and undo
    the playbook's decision one layer up.
    """

    answers = answer_questions(PlaybookKind.BANK, understanding())

    for given in inapplicable(answers):
        assert given.verdict is None
        assert given.score is None
        assert given.confidence is None
        assert given.evidence == ()
        assert given.basis == ()
        assert given.gaps == ()


def test_the_bank_can_state_all_three_things_it_knows() -> None:
    """The stopping point: answered, not yet answerable, not applicable."""

    answers = answer_questions(PlaybookKind.BANK, understanding(earnings_growth=None))

    assert answered(answers)
    assert unanswerable(answers)
    assert inapplicable(answers)

    assert len(answered(answers)) + len(unanswerable(answers)) + len(
        inapplicable(answers)
    ) == len(answers)
