from app.config import Settings
from app.models import PortfolioState, RiskDecision, Side, TradeProposal


class RiskEngine:
    def __init__(self, settings: Settings):
        self.s = settings

    def evaluate(self, proposal: TradeProposal, state: PortfolioState) -> RiskDecision:
        reasons: list[str] = []
        symbol = proposal.symbol.upper()

        if symbol not in self.s.allowed_symbols:
            reasons.append(f"{symbol} is outside the allowlist")
        if symbol in self.s.crypto_symbols and not self.s.allow_crypto:
            reasons.append("crypto trading is disabled")
        if proposal.side == Side.sell and not self.s.allow_shorts:
            reasons.append("short or sell-to-open trades are disabled")
        if proposal.leverage > self.s.max_leverage:
            reasons.append(f"leverage exceeds maximum {self.s.max_leverage}")
        if not self.s.min_stop_loss_pct <= proposal.stop_loss_pct <= self.s.max_stop_loss_pct:
            reasons.append("stop-loss percentage is outside configured bounds")
        if proposal.take_profit_pct < self.s.min_take_profit_pct:
            reasons.append("take-profit percentage is below configured minimum")
        if state.open_positions >= self.s.max_open_positions:
            reasons.append("maximum number of open positions reached")
        if state.trades_today >= self.s.max_trades_per_day:
            reasons.append("maximum trades per day reached")
        if state.daily_pnl_usd <= -(state.equity_usd * self.s.max_daily_loss_pct):
            reasons.append("daily loss circuit breaker triggered")

        amount = min(
            proposal.amount_usd,
            self.s.max_order_usd,
            state.equity_usd * self.s.max_position_pct,
            state.available_cash_usd,
        )

        if symbol in self.s.crypto_symbols:
            remaining = max(
                0,
                state.equity_usd * self.s.max_crypto_exposure_pct
                - state.crypto_exposure_usd,
            )
            amount = min(amount, remaining)
            if amount <= 0:
                reasons.append("crypto exposure cap reached")

        if amount <= 0:
            reasons.append("no available capital")
        if self.s.require_manual_approval and not proposal.approved_by_user:
            reasons.append("manual approval is required")

        return RiskDecision(
            allowed=not reasons,
            reasons=reasons or ["all deterministic risk checks passed"],
            adjusted_amount_usd=round(amount, 2) if amount > 0 else None,
        )
