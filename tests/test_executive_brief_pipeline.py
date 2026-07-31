from app.application.executive.executive_service import (
    ExecutiveService,
)
from app.application.workspace.executive_pipeline import (
    ExecutivePipeline,
)
from app.brain import BrainBuilder
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def make_brain():
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()


def test_pipeline_populates_the_executive_brief():
    workspace = ExecutivePipeline().execute(
        symbol="AAPL",
        brain=make_brain(),
    )

    assert workspace.brief is not None


def test_executive_brief_explains_the_decision():
    brain = make_brain()

    decision = ExecutiveService().decide(
        symbol="AAPL",
        brain=brain,
    )

    brief = ExecutiveService().brief(
        symbol="AAPL",
        brain=brain,
    )

    assert brief.headline.startswith("AAPL")
    assert decision.state.value.upper() in brief.headline

    assert brief.summary == decision.rationale
    assert brief.summary

    assert 0.0 <= brief.confidence <= 1.0
    assert 0.0 <= brief.portfolio_health <= 1.0


def test_executive_brief_carries_the_investment_case():
    brief = ExecutiveService().brief(
        symbol="AAPL",
        brain=make_brain(),
    )

    assert len(brief.investment_cases) == 1
    assert brief.investment_cases[0].symbol == "AAPL"

    assert len(brief.priorities) == 1
    assert brief.priorities[0].title == "AAPL"
