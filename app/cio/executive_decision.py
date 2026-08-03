from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState
from app.domain.asset_class import AssetClass


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

    #: What kind of asset this is. The Artificial CIO needs it to tell a
    #: measurement that has not arrived from a question that does not
    #: apply: a token has no business quality, and never will.
    asset_class: AssetClass | None = None

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

    #: The findings that argue for this security, and only those. The name
    #: is safe to use again: the signals now state the sense they read each
    #: finding with, so this is a selection rather than the whole list
    #: wearing a flattering label.
    strengths: tuple[str, ...] = ()

    #: The findings that argue against this security.
    risks: tuple[str, ...] = ()

    #: Risks belonging to the account and the market rather than to the
    #: security, plus the behavioural risks of acting against policy.
    #: Identical under every symbol, and kept apart for that reason.
    context_risks: tuple[str, ...] = ()

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
    key_strengths: tuple[str, ...] = ()
    key_risks: tuple[str, ...] = ()
    context_risks: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    catalysts: tuple[str, ...] = ()

    next_trigger: str | None = None

    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def belongs_to_watchlist(self) -> bool:
        return self.state.belongs_to_watchlist
