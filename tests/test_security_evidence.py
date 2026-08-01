"""Per-security evidence and its effect on executive decisions."""

import pytest

from app.application.brain.perception.security_perception import (
    SecurityPerception,
)
from app.application.brain.reasoning import ReasoningService
from app.application.committees.committee_service import CommitteeService
from app.application.executive.decision_evidence_builder import (
    DecisionEvidenceBuilder,
)
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.brain import Brain, BrainBuilder
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.momentum_signal import MomentumSignal
from app.domain.portfolio_position import PortfolioPosition
from app.domain.quality_signal import QualitySignal
from app.domain.value_signal import ValueSignal
from app.domain.watchlist_item import WatchlistItem
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)


def make_company(
    symbol: str,
    recommendation: str = "HOLD",
    confidence: int = 60,
    quality: str = "HIGH",
    valuation: str = "CHEAP",
    trend: str = "BULLISH",
) -> CompanyRecommendation:
    return CompanyRecommendation(
        symbol=symbol,
        recommendation=recommendation,
        confidence=confidence,
        summary=f"{recommendation}: {symbol}",
        signals=CompanySignals(
            value=ValueSignal(
                valuation=valuation,
                confidence=confidence,
                evidence=(f"{symbol} looks {valuation.lower()}.",),
            ),
            quality=QualitySignal(
                quality=quality,
                confidence=confidence,
                evidence=(),
            ),
            momentum=MomentumSignal(
                trend=trend,
                strength="STRONG",
                confidence=confidence,
                evidence=(),
            ),
        ),
        evidence=(f"{symbol} evidence.",),
    )


def make_brain(
    evidence: dict[str, tuple[object, ...]] | None = None,
    holdings: tuple[PortfolioPosition, ...] = (),
) -> Brain:
    from dataclasses import replace

    portfolio = replace(make_portfolio(), holdings=holdings)

    return BrainBuilder(
        portfolio=portfolio,
        market=make_market(),
        investment_policy=make_policy(),
        evidence=evidence or {},
    ).build()


def make_holding(symbol: str, market_value_usd: float = 100.0) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=market_value_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=0.0,
        instrument_id=abs(hash(symbol)) % 10_000,
    )


def build_evidence(brain: Brain, symbol: str):
    reasoning = ReasoningService().reason(brain)
    opinions = CommitteeService().review(brain, reasoning)

    return DecisionEvidenceBuilder().build(
        symbol,
        brain,
        reasoning,
        opinions,
    )


def test_security_evidence_distinguishes_two_holdings() -> None:
    brain = make_brain(
        evidence={
            "GOOD": (make_company("GOOD", quality="HIGH", valuation="CHEAP"),),
            "POOR": (make_company("POOR", quality="LOW", valuation="EXPENSIVE"),),
        }
    )

    good = build_evidence(brain, "GOOD")
    poor = build_evidence(brain, "POOR")

    assert good.quality_score > poor.quality_score
    assert good.valuation_score > poor.valuation_score


def test_a_sell_opinion_vetoes_the_case() -> None:
    brain = make_brain(
        evidence={"SELLME": (make_company("SELLME", recommendation="SELL"),)},
    )

    assert build_evidence(brain, "SELLME").analyst_veto is True


def test_a_hold_opinion_does_not_veto_the_case() -> None:
    brain = make_brain(
        evidence={"HOLDME": (make_company("HOLDME", recommendation="HOLD"),)},
    )

    assert build_evidence(brain, "HOLDME").analyst_veto is False


def test_low_quality_stays_above_the_rejection_floor() -> None:
    """The CIO must not reject what its own security committee holds."""

    from app.cio.decision_policy import DecisionPolicy

    brain = make_brain(
        evidence={"WEAK": (make_company("WEAK", quality="LOW"),)},
    )

    evidence = build_evidence(brain, "WEAK")

    assert evidence.quality_score >= DecisionPolicy().minimum_watchlist_quality


def test_missing_security_evidence_is_reported_not_invented() -> None:
    brain = make_brain()

    evidence = build_evidence(brain, "UNKNOWN")

    assert evidence.missing_evidence
    assert "UNKNOWN" in evidence.missing_evidence[0]


def test_unavailable_signals_are_reported_as_missing() -> None:
    brain = make_brain(
        evidence={
            "PARTIAL": (
                make_company("PARTIAL", quality="UNKNOWN", valuation="UNKNOWN"),
            )
        },
    )

    missing = build_evidence(brain, "PARTIAL").missing_evidence

    assert any("Valuation" in item for item in missing)
    assert any("Quality" in item for item in missing)


def test_portfolio_briefing_ranks_holdings_by_conviction() -> None:
    brain = make_brain(
        evidence={
            "STRONG": (make_company("STRONG", quality="HIGH", valuation="CHEAP"),),
            "WEAK": (
                make_company(
                    "WEAK",
                    recommendation="SELL",
                    quality="LOW",
                    valuation="EXPENSIVE",
                ),
            ),
        },
        holdings=(make_holding("WEAK"), make_holding("STRONG")),
    )

    briefing = PortfolioBriefingService().build(brain)

    assert briefing is not None

    symbols = [workspace.symbol for workspace in briefing.workspaces]

    # Ranked by conviction, not by the order the broker reported them.
    assert symbols == ["STRONG", "WEAK"]

    convictions = [
        workspace.decision.conviction
        for workspace in briefing.workspaces
        if workspace.decision
    ]
    assert convictions == sorted(convictions, reverse=True)


def test_portfolio_briefing_is_none_without_holdings() -> None:
    assert PortfolioBriefingService().build(make_brain()) is None


def test_portfolio_brief_counts_every_holding() -> None:
    brain = make_brain(
        evidence={"A": (make_company("A"),), "B": (make_company("B"),)},
        holdings=(make_holding("A"), make_holding("B")),
    )

    briefing = PortfolioBriefingService().build(brain)

    assert briefing is not None
    assert "2 positions reviewed" in briefing.brief.headline
    assert len(briefing.brief.investment_cases) == 2


@pytest.mark.anyio
async def test_security_perception_skips_unresolved_holdings() -> None:
    """An unnamed instrument produces no evidence rather than a guess."""

    class ResolverStub:
        async def items(self) -> dict[int, WatchlistItem]:
            return {}

    from dataclasses import replace

    portfolio = replace(
        make_portfolio(),
        holdings=(
            PortfolioPosition(
                symbol="#1238",
                quantity=1.0,
                invested_usd=10.0,
                market_value_usd=10.0,
                unrealized_pnl_usd=0.0,
                instrument_id=1238,
            ),
        ),
    )

    perception = SecurityPerception(symbol_resolver=ResolverStub())  # type: ignore[arg-type]

    assert await perception.execute(portfolio) == {}
