"""
Brain context shared across all executive reasoners.
"""

from app.domain.market import MarketSnapshot
from app.domain.portfolio import PortfolioSnapshot
from app.domain.portfolio_assessment import PortfolioAssessment
from pydantic import BaseModel, ConfigDict


class BrainContext(BaseModel):
    """Complete context consumed by the MOVRvest Brain."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    portfolio: PortfolioSnapshot
    market: MarketSnapshot | None = None

    # NEW
    portfolio_assessment: PortfolioAssessment | None = None
