from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.exchange_rate_service import ExchangeRateService


class PortfolioService:
    CASH_CONCENTRATION_THRESHOLD = 80.0

    def __init__(
        self,
        exchange_rate_service: ExchangeRateService | None = None,
    ) -> None:
        self._exchange_rate_service = exchange_rate_service or ExchangeRateService()

    def analyze(self, account: AccountSnapshot) -> PortfolioSnapshot:
        equity_usd = self._non_negative(account.equity_usd)
        cash_usd = self._non_negative(account.cash_usd)

        # Prefer the amount supplied by the broker because it is direct
        # evidence. Derive it only when the broker does not provide it.
        if account.invested_usd is None:
            invested_usd = max(equity_usd - cash_usd, 0.0)
        else:
            invested_usd = self._non_negative(account.invested_usd)

        if equity_usd <= 0:
            cash_pct = 0.0
            invested_pct = 0.0
        else:
            cash_pct = self._percentage(cash_usd, equity_usd)
            invested_pct = self._percentage(invested_usd, equity_usd)

        risk_flags: list[str] = []

        if cash_pct >= self.CASH_CONCENTRATION_THRESHOLD:
            risk_flags.append("Cash concentration")

        if invested_pct > 0:
            risk_flags.append("Invested assets are not yet classified by asset type")

        total_value_eur = self._exchange_rate_service.usd_to_eur(equity_usd)
        available_cash_eur = self._exchange_rate_service.usd_to_eur(cash_usd)
        invested_eur = self._exchange_rate_service.usd_to_eur(invested_usd)

        largest_position, largest_position_pct = self._largest_position(
            account.positions,
            equity_usd,
        )

        return PortfolioSnapshot(
            allocation=Allocation(
                cash=cash_pct,
                stocks=0.0,
                etfs=0.0,
                crypto=0.0,
                unclassified=invested_pct,
            ),
            total_value=round(equity_usd, 2),
            total_value_eur=round(total_value_eur, 2),
            available_cash_usd=round(cash_usd, 2),
            available_cash_eur=round(available_cash_eur, 2),
            invested_usd=round(invested_usd, 2),
            invested_eur=round(invested_eur, 2),
            liquidity_pct=cash_pct,
            positions=account.positions_count,
            largest_position=largest_position,
            largest_position_pct=largest_position_pct,
            risk_flags=tuple(risk_flags),
            last_sync=account.timestamp,
            holdings=account.positions,
            pending_orders=account.pending_orders,
            unrealized_pnl_usd=round(
                self._value(account.unrealized_pnl_usd),
                2,
            ),
        )

    @classmethod
    def _largest_position(
        cls,
        positions: tuple[PortfolioPosition, ...],
        equity_usd: float,
    ) -> tuple[str | None, float]:
        if not positions:
            return None, 0.0

        largest = max(positions, key=lambda position: position.market_value_usd)

        return largest.symbol, cls._percentage(
            largest.market_value_usd,
            equity_usd,
        )

    @staticmethod
    def _percentage(value: float, total: float) -> float:
        if total <= 0:
            return 0.0

        return round((value / total) * 100, 2)

    @staticmethod
    def _non_negative(value: float | None) -> float:
        if value is None:
            return 0.0

        return max(float(value), 0.0)

    @staticmethod
    def _value(value: float | None) -> float:
        """Unclamped: unrealized P&L is legitimately negative."""
        if value is None:
            return 0.0

        return float(value)
