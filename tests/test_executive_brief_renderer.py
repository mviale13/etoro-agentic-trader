from app.application.brief.executive_brief_builder import (
    ExecutiveBriefBuilder,
)
from app.application.executive.executive_service import (
    ExecutiveService,
)
from app.brain import BrainBuilder
from app.renderers import ExecutiveBriefRenderer
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def test_render_executive_brief():

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    evaluation = ExecutiveService().evaluate(
        symbol="MSFT",
        brain=brain,
    )

    brief = ExecutiveBriefBuilder().build(
        evaluation,
    )

    view = ExecutiveBriefRenderer().render(
        brief,
    )

    assert view.headline
    assert view.summary
    assert len(view.priorities) == 1
    assert len(view.investment_cases) == 1
