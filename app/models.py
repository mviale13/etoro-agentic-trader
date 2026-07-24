from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Side(StrEnum):
    buy = "buy"
    sell = "sell"


class TradeProposal(BaseModel):
    symbol: str = Field(min_length=1)
    instrument_id: int | None = None
    side: Side
    amount_usd: float = Field(gt=0)
    leverage: int = Field(default=1, ge=1)
    stop_loss_pct: float = Field(gt=0)
    take_profit_pct: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    strategy: str
    reasons: list[str] = Field(min_length=1)
    approved_by_user: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def normalize_symbol(self):
        self.symbol = self.symbol.upper().strip()
        return self


class PortfolioState(BaseModel):
    equity_usd: float = 2000
    available_cash_usd: float = 2000
    daily_pnl_usd: float = 0
    open_positions: int = 0
    crypto_exposure_usd: float = 0
    trades_today: int = 0


class RiskDecision(BaseModel):
    allowed: bool
    reasons: list[str]
    adjusted_amount_usd: float | None = None


class ExecutionResult(BaseModel):
    status: str
    broker: str
    proposal: TradeProposal
    broker_response: dict = Field(default_factory=dict)
