from app.domain.account_snapshot import AccountSnapshot


class StatusRenderer:
    @staticmethod
    def _money(value: float | None) -> str:
        return "Unavailable" if value is None else f"${value:,.2f}"

    @classmethod
    def render(cls, snapshot: AccountSnapshot) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print(f"Broker:          {snapshot.broker} {snapshot.mode.title()}")
        print("Status:          Connected")
        print(f"Latency:         {snapshot.latency_ms:.1f} ms")
        print(
            f"Last sync:       {snapshot.timestamp.astimezone():%Y-%m-%d %H:%M:%S %Z}"
        )
        print()
        print(f"Equity:          {cls._money(snapshot.equity_usd)}")
        print(f"Available cash:  {cls._money(snapshot.cash_usd)}")
        print(f"Invested:        {cls._money(snapshot.invested_usd)}")
        print(f"Unrealized P&L:  {cls._money(snapshot.unrealized_pnl_usd)}")
        print(f"Positions:       {snapshot.positions_count}")
        print(f"Pending orders:  {snapshot.pending_orders}")
        print(f"Copy portfolios: {snapshot.copy_portfolios}")
        print()
