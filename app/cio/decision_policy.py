from pydantic import BaseModel, ConfigDict, Field


class DecisionPolicy(BaseModel):
    """Explicit gates applied by the Artificial CIO."""

    model_config = ConfigDict(frozen=True)

    minimum_watchlist_quality: int = Field(default=35, ge=0, le=100)
    minimum_investigation_evidence: int = Field(default=30, ge=0, le=100)

    minimum_prepare_quality: int = Field(default=60, ge=0, le=100)
    minimum_prepare_evidence: int = Field(default=60, ge=0, le=100)

    minimum_recommendation_quality: int = Field(
        default=75,
        ge=0,
        le=100,
    )
    minimum_recommendation_evidence: int = Field(
        default=75,
        ge=0,
        le=100,
    )
    minimum_recommendation_valuation: int = Field(
        default=60,
        ge=0,
        le=100,
    )
    minimum_portfolio_fit: int = Field(
        default=60,
        ge=0,
        le=100,
    )

    maximum_acceptable_risk: int = Field(
        default=70,
        ge=0,
        le=100,
    )
