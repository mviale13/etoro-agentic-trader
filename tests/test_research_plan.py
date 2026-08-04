import pytest

from app.domain.research_plan import AnalystKey, ResearchPlan


def test_research_plan_defines_objective_questions_and_analysts() -> None:
    plan = ResearchPlan(
        objective="Evaluate long-term investment attractiveness.",
        questions=(
            "Can earnings continue growing?",
            "Is the balance sheet resilient?",
            "Does the company generate durable cash flow?",
        ),
        analyst_keys=(
            AnalystKey.GROWTH,
            AnalystKey.BALANCE_SHEET,
            AnalystKey.CASH_FLOW,
        ),
    )

    assert plan.objective == "Evaluate long-term investment attractiveness."
    assert plan.questions == (
        "Can earnings continue growing?",
        "Is the balance sheet resilient?",
        "Does the company generate durable cash flow?",
    )
    assert plan.analyst_keys == (
        AnalystKey.GROWTH,
        AnalystKey.BALANCE_SHEET,
        AnalystKey.CASH_FLOW,
    )


def test_research_plan_requires_at_least_one_question() -> None:
    with pytest.raises(
        ValueError,
        match="Research plan must contain at least one question",
    ):
        ResearchPlan(
            objective="Evaluate the company.",
            questions=(),
            analyst_keys=(AnalystKey.GROWTH,),
        )


def test_research_plan_requires_at_least_one_analyst() -> None:
    with pytest.raises(
        ValueError,
        match="Research plan must assign at least one analyst",
    ):
        ResearchPlan(
            objective="Evaluate the company.",
            questions=("Can the company grow?",),
            analyst_keys=(),
        )
