"""What the risk analyst can say about the account, and what it cannot."""

from dataclasses import replace
from datetime import UTC, date, datetime

from app.application.brain.reasoning.risk_analyst import RiskAnalyst
from app.brain import Brain, BrainBuilder
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.provenance import Provenance
from tests.test_brain_context import make_market, make_policy, make_portfolio


def make_drawdown(
    depth: float = 0.25,
    current_depth: float = 0.10,
) -> PortfolioDrawdown:
    return PortfolioDrawdown(
        depth=depth,
        peak_on=date(2026, 7, 1),
        peak_value_usd=52_000.0,
        trough_on=date(2026, 7, 21),
        trough_value_usd=39_000.0,
        current_depth=current_depth,
        starts_on=date(2026, 7, 1),
        ends_on=date(2026, 8, 3),
        observations=34,
        reading=Provenance(
            source="eToro",
            observed_at=datetime.now(UTC),
        ),
    )


def make_brain(
    drawdown: PortfolioDrawdown | None = None,
    policy: InvestmentPolicy | None = None,
) -> Brain:
    return BrainBuilder(
        portfolio=replace(make_portfolio(), drawdown=drawdown),
        market=make_market(),
        investment_policy=policy or make_policy(),
    ).build()


def tolerant(pct: float) -> InvestmentPolicy:
    policy = make_policy()

    return replace(
        policy,
        constraints=replace(policy.constraints, max_drawdown=pct),
    )


def test_risk_analyst_exists() -> None:
    assert RiskAnalyst() is not None


def test_drawdown_is_scored_off_the_accounts_own_history() -> None:
    """The component that was a hardcoded 0.50 is now a measurement."""

    assessment = RiskAnalyst().assess(
        make_brain(drawdown=make_drawdown(depth=0.25), policy=tolerant(50.0)),
    )

    assert assessment.drawdown_risk_score == 0.5
    assert not any("Drawdown" in item for item in assessment.unmeasured)


def test_the_measured_fall_reaches_the_investor_with_its_window() -> None:
    """
    A depth on its own is not evidence. Which peak, which low, over how
    many days, and where the account stands now are what make it one.
    """

    assessment = RiskAnalyst().assess(make_brain(drawdown=make_drawdown()))

    stated = next(
        item.description for item in assessment.evidence if "fell" in item.description
    )

    assert "25.0%" in stated
    assert "01 Jul 2026" in stated
    assert "21 Jul 2026" in stated
    assert "34 daily balances" in stated
    assert "still 10.0% below that peak" in stated


def test_a_recovered_fall_says_so_rather_than_reporting_a_bare_depth() -> None:
    assessment = RiskAnalyst().assess(
        make_brain(drawdown=make_drawdown(current_depth=0.0)),
    )

    assert any(
        "recovered to a new high" in item.description for item in assessment.evidence
    )


def test_breaching_the_stated_tolerance_is_named_as_a_risk_factor() -> None:
    assessment = RiskAnalyst().assess(
        make_brain(drawdown=make_drawdown(depth=0.25), policy=tolerant(20.0)),
    )

    assert assessment.drawdown_risk_score == 1.0
    assert assessment.risk_factors[0] == (
        "Drawdown has reached the 20% the investor said they could accept"
    )


def test_a_breach_of_the_default_limit_does_not_claim_the_investor_set_it() -> None:
    """
    A default the platform chose and a figure the investor gave are not
    the same claim, and the risk factor says which one it is.
    """

    assessment = RiskAnalyst().assess(
        make_brain(drawdown=make_drawdown(depth=0.9)),
    )

    assert assessment.drawdown_risk_score == 1.0
    assert "the investor has stated no limit" in assessment.risk_factors[0]


def test_an_account_with_no_history_reports_drawdown_as_unmeasured() -> None:
    assessment = RiskAnalyst().assess(make_brain(drawdown=None))

    assert assessment.drawdown_risk_score is None
    assert any("Drawdown" in item for item in assessment.unmeasured)

    assert not any("fell" in item.description for item in assessment.evidence)


def test_overall_risk_stays_absent_while_market_risk_is_unmeasured() -> None:
    """
    Measuring one of the two missing components does not complete the
    picture, and averaging what is measured would report a low overall
    risk for an account whose market exposure nobody has looked at.
    """

    assessment = RiskAnalyst().assess(make_brain(drawdown=make_drawdown()))

    assert assessment.overall_risk_score is None
    assert assessment.market_risk_score is None
    assert any("Market risk" in item for item in assessment.unmeasured)
