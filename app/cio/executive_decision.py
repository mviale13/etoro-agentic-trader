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

    # An unrecognised field is an error, not something to drop quietly.
    # While this model accepted extras, `strengths=(...)` went on being
    # passed after the field was renamed and simply vanished — evidence
    # that was gathered, handed over, and silently reported as absent.
    model_config = ConfigDict(frozen=True, extra="forbid")

    symbol: str = Field(min_length=1)

    quality_score: int | None = Field(default=None, ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    valuation_score: int | None = Field(default=None, ge=0, le=100)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    #: How much room the portfolio has for this security, under the
    #: investor's own policy. None when the policy states no limit this
    #: could be measured against.
    portfolio_fit_score: int | None = Field(default=None, ge=0, le=100)

    actionable_now: bool = False
    hard_reject: bool = False
    analyst_veto: bool = False

    #: Every finding read about this security, favourable or not.
    #:
    #: This was called `strengths`, and it never was. It carries whatever
    #: the signals measured — "Large-cap company." sits beside "Negative
    #: earnings." and "Insufficient quality data." — so anything that
    #: presented it as a list of strengths would be reporting an absent
    #: measurement as a reason to invest.
    evidence_weighed: tuple[str, ...] = ()
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
    evidence_weighed: tuple[str, ...] = ()
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
