from app.models import Side, TradeProposal
from app.strategy.sma import moving_average_signal


def propose_from_prices(
    symbol: str,
    closes: list[float],
    amount_usd: float = 50,
) -> TradeProposal | None:
    signal = moving_average_signal(closes)
    if signal.action != "buy":
        return None

    return TradeProposal(
        symbol=symbol,
        side=Side.buy,
        amount_usd=amount_usd,
        leverage=1,
        stop_loss_pct=0.03,
        take_profit_pct=0.06,
        confidence=signal.confidence,
        strategy="sma_10_30",
        reasons=[
            f"10-period average ({signal.fast:.4f}) exceeds "
            f"30-period average ({signal.slow:.4f})",
            "Deterministic risk approval is still required",
        ],
    )
