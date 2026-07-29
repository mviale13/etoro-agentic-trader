from app.domain.research_plan import AnalystKey
from app.services.research_strategy import CorporateResearchStrategy


def test_corporate_strategy_creates_default_research_plan() -> None:
    strategy = CorporateResearchStrategy()

    plan = strategy.create_plan()

    assert plan.objective == "Evaluate long-term investment attractiveness."

    assert plan.questions == (
        "Can earnings continue growing?",
        "Is the company consistently profitable?",
        "Is the balance sheet resilient?",
        "Does the company generate durable cash flow?",
    )

    assert plan.analyst_keys == (
        AnalystKey.GROWTH,
        AnalystKey.PROFITABILITY,
        AnalystKey.BALANCE_SHEET,
        AnalystKey.CASH_FLOW,
    )
