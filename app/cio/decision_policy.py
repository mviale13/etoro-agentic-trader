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

    #: The risk score above which a security's own price record is
    #: judged severe.
    #:
    #: **It no longer gates a decision.** The owner's ruling of
    #: 2026-08-21 removed `risk_score > maximum_acceptable_risk →
    #: REJECT` from the Artificial CIO's cascade, so nothing here
    #: refuses a thesis. What the constant still anchors is the
    #: `risk-severity` rule's argument: `RiskSignal.SEVERITIES` places
    #: SEVERE *above* this number deliberately, and that placement is
    #: what the Capital Action Envelope's tightest security-risk
    #: ceiling keys on. Deleting it would silently unmoor that
    #: argument, so it is kept and its remaining referent is named.
    maximum_acceptable_risk: int = Field(
        default=70,
        ge=0,
        le=100,
    )
