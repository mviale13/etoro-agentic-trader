from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.cio.decision_state import DecisionState
from app.cio.executive_decision import ExecutiveDecision
from app.cio.timeline import InvestmentCaseEvent


class InvestmentCase(BaseModel):
    """Aggregate root for company research and CIO decisions."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1)
    company_name: str | None = None

    executive_decision: ExecutiveDecision | None = None
    timeline: tuple[InvestmentCaseEvent, ...] = ()

    portfolio_owned: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @property
    def state(self) -> DecisionState | None:
        if self.executive_decision is None:
            return None

        return self.executive_decision.state

    @property
    def belongs_to_watchlist(self) -> bool:
        if self.executive_decision is None:
            return False

        return self.executive_decision.belongs_to_watchlist

    def with_decision(
        self,
        decision: ExecutiveDecision,
        event: InvestmentCaseEvent,
    ) -> "InvestmentCase":
        if decision.symbol != self.symbol:
            raise ValueError(
                "Executive decision symbol must match investment case symbol.",
            )

        return self.model_copy(
            update={
                "executive_decision": decision,
                "timeline": (*self.timeline, event),
                "updated_at": datetime.now(UTC),
            },
        )
