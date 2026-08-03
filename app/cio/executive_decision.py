from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState


class DecisionEvidence(BaseModel):
    """
    Normalized evidence consumed by the Artificial CIO.

    A score of None means the platform did not measure it. It never means
    zero, and it is never filled in from something else: a gate that was not
    measured cannot be cleared, so the investment case simply does not
    progress past the point where that measurement is required.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1)

    quality_score: int | None = Field(default=None, ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    valuation_score: int | None = Field(default=None, ge=0, le=100)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    portfolio_fit_score: int = Field(ge=0, le=100)

    actionable_now: bool = False
    hard_reject: bool = False
    analyst_veto: bool = False

    strengths: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()

    next_trigger: str | None = None


class ExecutiveDecision(BaseModel):
    """Final explainable decision produced by the Artificial CIO."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    state: DecisionState
    conviction: int = Field(ge=0, le=100)

    rationale: str
    key_strengths: tuple[str, ...] = ()
    key_risks: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()

    next_trigger: str | None = None

    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def belongs_to_watchlist(self) -> bool:
        return self.state.belongs_to_watchlist
