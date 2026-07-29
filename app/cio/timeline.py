from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState


class InvestmentCaseEventType(StrEnum):
    CASE_CREATED = "CASE_CREATED"
    DECISION_CHANGED = "DECISION_CHANGED"
    DECISION_REAFFIRMED = "DECISION_REAFFIRMED"
    CATALYST_TRIGGERED = "CATALYST_TRIGGERED"
    RISK_CHANGED = "RISK_CHANGED"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"


class InvestmentCaseEvent(BaseModel):
    """Immutable historical event for an investment case."""

    model_config = ConfigDict(frozen=True)

    event_type: InvestmentCaseEventType

    previous_state: DecisionState | None = None
    new_state: DecisionState | None = None

    rationale: str
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
