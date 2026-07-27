from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.exchange_rate_service import ExchangeRateService


class PortfolioService:
    CASH_CONCENTRATION_THRESHOLD = 80.0

    def analyze(self, account: AccountSnapshot) -> PortfolioSnapshot:
        equity = account.equity_usd or 0.0
        cash = account.cash_usd or 0.0
        invested = account.invested_usd or 0.0

        if equity <= 0:
            cash_pct = 0.0
            invested_pct = 0.0
        else:
            cash_pct = self._percentage(cash, equity)
            invested_pct = self._percentage(invested, equity)

        risk_flags: list[str] = []

        if cash_pct >= self.CASH_CONCENTRATION_THRESHOLD:
            risk_flags.append("Cash concentration")

        if invested_pct > 0:
            risk_flags.append("Invested assets are not yet classified by asset type")

        return PortfolioSnapshot(
            allocation=Allocation(
                cash=cash_pct,
                stocks=0.0,
                etfs=0.0,
                crypto=0.0,
                unclassified=invested_pct,
            ),
            total_value=equity,
            positions=account.positions,
            largest_position=None,
            largest_position_pct=0.0,
            risk_flags=tuple(risk_flags),
            total_value_eur=ExchangeRateService().usd_to_eur(equity),
        )

    @staticmethod
    def _percentage(value: float, total: float) -> float:
        if total <= 0:
            return 0.0

        return round((value / total) * 100, 2)
