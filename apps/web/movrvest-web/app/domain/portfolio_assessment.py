"""Domain models for the MOVRvest portfolio executive assessment.

The assessment represents structured investment reasoning produced by the
backend. Presentation layers should render these models without recreating
portfolio reasoning in the frontend.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AssessmentStatus(StrEnum):
    """Executive status assigned to an assessment item."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    ATTENTION = "attention"
    CRITICAL = "critical"


class AssessmentCategory(StrEnum):
    """Portfolio dimensions evaluated by the Artificial CIO."""

    LIQUIDITY = "liquidity"
    DIVERSIFICATION = "diversification"
    PORTFOLIO_RISK = "portfolio_risk"
    OPPORTUNITY_READINESS = "opportunity_readiness"


class AssessmentItem(BaseModel):
    """A structured conclusion about one portfolio dimension."""

    model_config = ConfigDict(frozen=True)

    category: AssessmentCategory
    status: AssessmentStatus

    title: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    implication: str = Field(min_length=1)

    confidence: float = Field(ge=0.0, le=1.0)
    evidence: tuple[str, ...] = Field(default_factory=tuple)


class PortfolioAssessment(BaseModel):
    """Executive assessment generated from the current portfolio snapshot."""

    model_config = ConfigDict(frozen=True)

    executive_summary: str = Field(min_length=1)

    strengths: tuple[AssessmentItem, ...] = Field(default_factory=tuple)
    concerns: tuple[AssessmentItem, ...] = Field(default_factory=tuple)
    opportunities: tuple[AssessmentItem, ...] = Field(default_factory=tuple)

    confidence: float = Field(ge=0.0, le=1.0)

    @property
    def items(self) -> tuple[AssessmentItem, ...]:
        """Return all assessment items in executive reading order."""

        return self.strengths + self.concerns + self.opportunities
