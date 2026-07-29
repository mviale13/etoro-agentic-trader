from app.brain import Brain, BrainBuilder
from app.cio.investment_case import InvestmentCase
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def test_brain_builder_assembles_complete_brain() -> None:
    investment_case = InvestmentCase(
        symbol="MSFT",
        company_name="Microsoft",
    )

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        investment_cases={"MSFT": investment_case},
        evidence={"MSFT": ("High return on capital",)},
        committee_opinions={"MSFT": ("Quality committee approves",)},
        memory={"last_review": "2026-07-29"},
        alerts=("Technology concentration approaching limit.",),
    ).build()

    assert isinstance(brain, Brain)
    assert brain.investment_case("MSFT") == investment_case
    assert brain.evidence_for("MSFT") == ("High return on capital",)
    assert brain.opinions_for("MSFT") == ("Quality committee approves",)
    assert brain.memory == {"last_review": "2026-07-29"}
    assert brain.alerts == ("Technology concentration approaching limit.",)


def test_brain_builder_uses_empty_optional_context_by_default() -> None:
    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    assert brain.investment_cases == {}
    assert brain.memory == {}
    assert brain.alerts == ()
    assert brain.evidence_for("MSFT") == ()
    assert brain.opinions_for("MSFT") == ()
    assert brain.investment_case("MSFT") is None


def test_brain_builder_detaches_brain_from_mutable_inputs() -> None:
    memory: dict[str, object] = {"cycle": 1}
    evidence: dict[str, tuple[object, ...]] = {
        "MSFT": ("Strong margins",),
    }

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        memory=memory,
        evidence=evidence,
    ).build()

    memory["cycle"] = 2
    evidence["MSFT"] = ("Margins deteriorating",)

    assert brain.memory == {"cycle": 1}
    assert brain.evidence_for("MSFT") == ("Strong margins",)
