from fastapi import APIRouter, Depends

from app.api.dependencies import get_brain_snapshot_service
from app.application.brain.brain_snapshot_service import (
    BrainSnapshotService,
)
from app.application.brain.reasoning.models.capacity_assessment import (
    CapacityAssessment,
)
from app.application.brain.reasoning.models.risk_assessment import RiskAssessment
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_snapshot import PortfolioSnapshot

router = APIRouter(
    prefix="/brain",
    tags=["brain"],
)


def _drawdown(
    drawdown: PortfolioDrawdown | None,
) -> dict[str, object] | None:
    """
    The account's worst fall, or null.

    Null is served rather than a zero. A dashboard cannot tell a portfolio
    that never fell from one whose history nobody could read, and the page
    is the one place where that difference reaches the investor.
    """

    if drawdown is None:
        return None

    return {
        "depth_pct": round(drawdown.depth * 100, 2),
        "current_depth_pct": round(drawdown.current_depth * 100, 2),
        "recovered": drawdown.recovered,
        "peak_on": drawdown.peak_on.isoformat(),
        "peak_value_usd": drawdown.peak_value_usd,
        "trough_on": drawdown.trough_on.isoformat(),
        "trough_value_usd": drawdown.trough_value_usd,
        "starts_on": drawdown.starts_on.isoformat(),
        "ends_on": drawdown.ends_on.isoformat(),
        "observations": drawdown.observations,
        "reading": drawdown.reading.stated(),
    }


def _risk(
    risk: RiskAssessment | None,
) -> dict[str, object] | None:
    """
    The four ways this account can lose money, each measured or null.

    Served as scores and statements, not as the five-segment bars the page
    draws. What a score means visually is presentation; what it is worth
    is measurement, and the page had been deciding both.
    """

    if risk is None:
        return None

    return {
        "overall": risk.overall_risk_score,
        "level": risk.risk_level.value if risk.risk_level is not None else None,
        "market": risk.market_risk_score,
        "concentration": risk.concentration_risk_score,
        "liquidity": risk.liquidity_risk_score,
        "drawdown": risk.drawdown_risk_score,
        "factors": list(risk.risk_factors),
        "mitigants": list(risk.mitigants),
        "evidence": [
            {"statement": item.description, "source": item.source}
            for item in risk.evidence
        ],
        "unmeasured": list(risk.unmeasured),
    }


def _capacity(
    capacity: CapacityAssessment | None,
) -> dict[str, object] | None:
    """
    The account's room to act, each term measured or null.

    Headroom figures pass through signed: a largest position over its
    limit arrives as a negative number, which is a measured breach the
    page must state, not a zero.
    """

    if capacity is None:
        return None

    return {
        "cash_actual_pct": capacity.cash_actual_pct,
        "cash_target_pct": capacity.cash_target_pct,
        "funding_room_pct": capacity.funding_room_pct,
        "funding_room_usd": capacity.funding_room_usd,
        "single_position_limit_pct": capacity.single_position_limit_pct,
        "largest_position": capacity.largest_position,
        "largest_position_pct": capacity.largest_position_pct,
        "single_position_headroom_pct": capacity.single_position_headroom_pct,
        "crypto_limit_pct": capacity.crypto_limit_pct,
        "crypto_actual_pct": capacity.crypto_actual_pct,
        "crypto_headroom_pct": capacity.crypto_headroom_pct,
        "unmeasured": list(capacity.unmeasured),
    }


def _holdings(portfolio: PortfolioSnapshot) -> list[dict[str, object]]:
    """
    The positions the broker actually reported, one row per holding.

    Facts only — the weight is the snapshot's own measurement, and an
    unresolved holding keeps its placeholder identity rather than being
    dropped, because a row the broker reported is a row the investor owns.
    """

    return [
        {
            "symbol": holding.symbol,
            "resolved": holding.is_resolved,
            "asset_class": holding.asset_class,
            "invested_usd": holding.invested_usd,
            "market_value_usd": holding.market_value_usd,
            "unrealized_pnl_usd": holding.unrealized_pnl_usd,
            "weight_pct": portfolio.weight_pct(holding),
        }
        for holding in portfolio.holdings
    ]


@router.get("/")
async def get_brain(
    service: BrainSnapshotService = Depends(get_brain_snapshot_service),
) -> dict[str, object]:
    brain = await service.build()

    executive_brief: dict[str, object] | None = None

    if brain.brief is not None:
        executive_brief = {
            "headline": brain.brief.headline,
            "why": brain.brief.why,
            "action": brain.brief.action,
            "confidence": brain.brief.confidence,
        }

    return {
        "summary": brain.summary,
        "focus": brain.focus,
        "executive_brief": executive_brief,
        "portfolio": {
            "total_value": brain.portfolio.total_value,
            "total_value_eur": brain.portfolio.total_value_eur,
            "available_cash_usd": brain.portfolio.available_cash_usd,
            "available_cash_eur": brain.portfolio.available_cash_eur,
            "invested_usd": brain.portfolio.invested_usd,
            "invested_eur": brain.portfolio.invested_eur,
            "liquidity_pct": brain.portfolio.liquidity_pct,
            "positions": brain.portfolio.positions,
            "pending_orders": brain.portfolio.pending_orders,
            "unrealized_pnl_usd": brain.portfolio.unrealized_pnl_usd,
            "largest_position": brain.portfolio.largest_position,
            "largest_position_pct": brain.portfolio.largest_position_pct,
            "cash_allocation": brain.portfolio.allocation.cash,
            "last_sync": brain.portfolio.last_sync,
            "drawdown": _drawdown(brain.portfolio.drawdown),
            "holdings": _holdings(brain.portfolio),
        },
        "risk": _risk(brain.risk),
        "capacity": _capacity(brain.capacity),
        "observation": {
            "title": brain.observation.title,
            "message": brain.observation.message,
        },
        "investor_dna": {
            "confidence": brain.investor_dna.confidence,
            "message": (
                "Learning your investment style..."
                if brain.investor_dna.confidence < 50
                else "Strong understanding of your investing style."
            ),
        },
        "recommendation": {
            "symbol": brain.recommendation.symbol,
            "action": brain.recommendation.decision.recommendation,
            "confidence": brain.recommendation.decision.confidence,
        },
    }
