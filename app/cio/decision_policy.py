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

    # The policy carried a risk ceiling here — 70, the threshold of the
    # `decision-gates@2` transition that rejected a thesis on its own
    # price record — until the owner's ruling of 2026-08-21 removed
    # that transition and, with it, the field. Nothing consumes such a
    # threshold now: the security-risk envelope reads the risk band and
    # the three explicit CapitalPolicy ceilings, and a dead policy
    # value kept "for the record" would read as a live rule.
