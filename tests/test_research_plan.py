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


def test_a_plan_may_ask_for_no_analyst_at_all() -> None:
    """
    A digital asset and a fund publish no accounts to analyse.

    This used to raise: a plan was required to name at least one analyst,
    so a security with nothing to analyse could not be described and was
    skipped instead — which left its dossier quietly thinner than a
    company's, with no explanation for the difference.
    """

    plan = ResearchPlan(
        objective="Evaluated as a digital asset.",
        questions=("Network scale and supply",),
        analyst_keys=(),
    )

    assert plan.analyst_keys == ()
