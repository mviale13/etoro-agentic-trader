"""What the executive brief attributes to the security, and what it does not."""

from datetime import UTC, datetime

import pytest

from app.domain.executive.executive_brief import ExecutiveBrief
from app.domain.thesis import InvestmentThesis
from app.renderers.executive_brief_console_renderer import (
    ExecutiveBriefConsoleRenderer,
)


def make_brief() -> ExecutiveBrief:
    return ExecutiveBrief(
        headline="UUUU: INVESTIGATE",
        summary="Business quality has not been measured.",
        confidence=0.32,
        portfolio_health=0.77,
        priorities=(),
        investment_cases=(
            InvestmentThesis(
                symbol="UUUU",
                recommendation="INVESTIGATE",
                confidence=0.32,
                conviction=81,
                summary="Business quality has not been measured.",
                strengths=("Positive earnings.",),
                risks=("Annualised volatility is 94.0% over the past year.",),
                catalysts=(),
                invalidation_conditions=(),
                expected_holding_period="3-5 years",
                created_at=datetime(2026, 8, 3, tzinfo=UTC),
                evidence_weighed=(
                    "Positive earnings.",
                    "Annualised volatility is 94.0% over the past year.",
                ),
                context_strengths=("Healthy liquidity",),
                context_risks=("Cash concentration",),
            ),
        ),
    )


@pytest.fixture
def rendered(capsys: pytest.CaptureFixture[str]) -> str:
    ExecutiveBriefConsoleRenderer.render(make_brief())

    return capsys.readouterr().out


def test_both_numbers_are_reported_under_their_own_names(rendered: str) -> None:
    """
    They answer different questions and used to be conflated.

    The brief carried only the committees' agreement, printed as
    "Conviction", so a RECOMMEND could read "Conviction: 32%" while the
    Artificial CIO held the decision at 81. Both are now stated, and the
    one labelled conviction is the decision's own.
    """

    assert "Committee agreement: 32%" in rendered
    assert "Conviction: 81%" in rendered


def test_conviction_belongs_to_the_case_not_the_brief(rendered: str) -> None:
    """
    Conviction is held in a decision about a security.

    A portfolio brief covers several, so the number sits inside each case
    rather than in the header, where one of them would stand for all.
    """

    header, case = rendered.split("UUUU — INVESTIGATE")

    assert "Conviction:" not in header
    assert "Conviction:" in case


def test_the_case_reports_what_was_read_about_the_security(rendered: str) -> None:
    assert "Evidence weighed" in rendered
    assert "94.0%" in rendered


def test_the_accounts_liquidity_is_not_presented_as_the_securitys_strength(
    rendered: str,
) -> None:
    """
    "Healthy liquidity" describes the investor's cash, not UUUU.

    Printed under a bare "Strengths" heading beneath a ticker, it reads as
    a property of the security — a portfolio fact borrowed to make a case
    for something it says nothing about.
    """

    security, context = rendered.split("Portfolio and market strengths")

    assert "Healthy liquidity" not in security
    assert "Healthy liquidity" in context
    assert "Portfolio and market risks" in context


def test_the_case_states_the_securitys_own_strengths_and_risks(
    rendered: str,
) -> None:
    """A case that lists neither says nothing about the security."""

    strengths, rest = rendered.split("Risks", 1)

    assert "Positive earnings." in strengths
    assert "94.0%" in rest.split("Evidence weighed")[0]
