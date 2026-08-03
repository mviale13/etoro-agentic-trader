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
                summary="Business quality has not been measured.",
                strengths=("Healthy liquidity",),
                risks=("Cash concentration",),
                catalysts=(),
                invalidation_conditions=(),
                expected_holding_period="3-5 years",
                created_at=datetime(2026, 8, 3, tzinfo=UTC),
                evidence_weighed=(
                    "Annualised volatility is 94.0% over the past year.",
                ),
            ),
        ),
    )


@pytest.fixture
def rendered(capsys: pytest.CaptureFixture[str]) -> str:
    ExecutiveBriefConsoleRenderer.render(make_brief())

    return capsys.readouterr().out


def test_committee_agreement_is_not_presented_as_conviction(rendered: str) -> None:
    """
    The brief carries the committees' agreement, not the CIO's conviction.

    Labelled "Conviction", a RECOMMEND read "Conviction: 32%" — the
    decision's own conviction never reaches this brief, so the number
    shown was answering a different question than the one asked.
    """

    assert "Committee agreement:" in rendered
    assert "Conviction:" not in rendered


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

    assert "Portfolio and market strengths" in rendered
    assert "Portfolio and market risks" in rendered
