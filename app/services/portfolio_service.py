from dataclasses import replace

from app.domain.account_snapshot import AccountSnapshot
from app.domain.asset_class import AssetClass
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

        # True of a snapshot the broker has just been read into: nothing
        # here knows what the holdings are yet. `allocate` replaces this
        # once they have been classified against the watchlists.
        if invested_pct > 0:
            risk_flags.append("Invested assets are not yet classified by asset type")

        # Read once, so every euro figure on the page is converted at one
        # rate. Absent where no rate has been read: a conversion is
        # derived from a measurement, and without the measurement the
        # figure is absent rather than filled in from a constant.
        rate = self._exchange_rate_service.rate()

        total_value_eur = self._exchange_rate_service.usd_to_eur(equity_usd, rate)
        available_cash_eur = self._exchange_rate_service.usd_to_eur(cash_usd, rate)
        invested_eur = self._exchange_rate_service.usd_to_eur(invested_usd, rate)

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
            total_value_eur=total_value_eur,
            available_cash_usd=round(cash_usd, 2),
            available_cash_eur=available_cash_eur,
            invested_usd=round(invested_usd, 2),
            invested_eur=invested_eur,
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
    def allocate(
        cls,
        snapshot: PortfolioSnapshot,
    ) -> PortfolioSnapshot:
        """
        Split the invested share of the account by asset class.

        Called once the holdings know what they are. Until they did, every
        invested euro sat in `unclassified` and the account carried a
        standing risk flag saying so, which meant the policy's stock, ETF
        and crypto targets had nothing to be compared against.

        A holding no watchlist describes stays unclassified, and so does one
        whose class the policy sets no target for — a commodity cannot drift
        from a target that does not exist. The flag is raised only for what
        remains genuinely unaccounted for, and says how much.
        """

        equity = snapshot.total_value

        if equity <= 0 or not snapshot.holdings:
            return snapshot

        totals = {AssetClass.STOCK: 0.0, AssetClass.ETF: 0.0, AssetClass.CRYPTO: 0.0}
        unclassified = 0.0

        for holding in snapshot.holdings:
            asset_class = cls._asset_class(holding)

            if asset_class in totals:
                totals[asset_class] += holding.market_value_usd
            else:
                unclassified += holding.market_value_usd

        unclassified_pct = cls._percentage(unclassified, equity)

        risk_flags = tuple(
            flag
            for flag in snapshot.risk_flags
            if not flag.startswith("Invested assets are not")
        )

        if unclassified_pct > 0:
            risk_flags = (
                *risk_flags,
                f"{unclassified_pct:.1f}% of the account is held in assets "
                "the platform cannot classify",
            )

        return replace(
            snapshot,
            allocation=replace(
                snapshot.allocation,
                stocks=cls._percentage(totals[AssetClass.STOCK], equity),
                etfs=cls._percentage(totals[AssetClass.ETF], equity),
                crypto=cls._percentage(totals[AssetClass.CRYPTO], equity),
                unclassified=unclassified_pct,
            ),
            risk_flags=risk_flags,
        )

    @staticmethod
    def _asset_class(holding: PortfolioPosition) -> AssetClass | None:
        if holding.asset_class is None:
            return None

        try:
            return AssetClass(holding.asset_class)
        except ValueError:
            return None

    @classmethod
    def _largest_position(
        cls,
        positions: tuple[PortfolioPosition, ...],
        equity_usd: float,
    ) -> tuple[str | None, float]:
        """
        The largest holding by security, not the largest single trade.

        The broker reports a position per trade, so a security bought
        twice arrives as two rows. Measuring the biggest row measures a
        transaction, and the investor's policy limits a *security*: two
        BTC buys of 20.0% and 0.5% were read as a 20.0% holding exactly
        at a 20% limit, when the holding was 20.5% and over it. A breach
        of the investor's own policy reported as compliance.
        """

        if not positions:
            return None, 0.0

        held: dict[str, float] = {}

        for position in positions:
            held[position.symbol] = (
                held.get(position.symbol, 0.0) + position.market_value_usd
            )

        symbol, value = max(held.items(), key=lambda holding: holding[1])

        return symbol, cls._percentage(value, equity_usd)

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
