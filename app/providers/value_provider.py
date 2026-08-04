from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot


class ValueProvider:
    SOURCE = "Yahoo Finance"

    """
    Read the fundamentals a single provider call already returns.

    One request carries valuation, size, earnings — and the growth, margins,
    balance sheet and cash flow beside them. Reading only part of it and
    reporting the rest as unavailable would understate what the platform can
    evidence about a company, and leave the fundamental analysts nothing to
    analyse though the numbers were already in the response.
    """

    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot:
        return self.from_info(
            yf.Ticker(symbol).info,
            reading=Provenance(source=self.SOURCE, observed_at=datetime.now(UTC)),
        )

    @classmethod
    def from_info(
        cls,
        info: dict[str, Any],
        *,
        reading: Provenance | None = None,
    ) -> ValuationSnapshot:
        """
        Read a valuation snapshot out of one `info` payload.

        Pure and provider-shaped so the reading of the payload can be tested
        without the network, and so the one request's growth, margins and
        cash flow are read from the same dict its valuation is.
        """

        return ValuationSnapshot(
            forward_pe=info.get("forwardPE"),
            trailing_pe=info.get("trailingPE"),
            peg_ratio=info.get("pegRatio"),
            dividend_yield=info.get("dividendYield"),
            market_cap=info.get("marketCap"),
            eps=info.get("trailingEps", info.get("forwardEps")),
            circulating_supply=info.get("circulatingSupply"),
            max_supply=info.get("maxSupply"),
            volume_24h=info.get("volume24Hr", info.get("regularMarketVolume")),
            inception=cls._inception(info.get("startDate")),
            # Growth and margins arrive as decimal ratios already.
            revenue_growth=cls._ratio(info.get("revenueGrowth")),
            earnings_growth=cls._ratio(info.get("earningsGrowth")),
            gross_margin=cls._ratio(info.get("grossMargins")),
            operating_margin=cls._ratio(info.get("operatingMargins")),
            net_margin=cls._ratio(info.get("profitMargins")),
            return_on_equity=cls._ratio(info.get("returnOnEquity")),
            # Yahoo reports debt-to-equity as a percentage (195.6 for 1.96x),
            # while the balance-sheet analyst bands it as a ratio. Left as the
            # percentage it arrives as, it would read every company as
            # drowning in debt.
            debt_to_equity=cls._percentage_as_ratio(info.get("debtToEquity")),
            current_ratio=cls._ratio(info.get("currentRatio")),
            operating_cash_flow=cls._ratio(info.get("operatingCashflow")),
            free_cash_flow=cls._ratio(info.get("freeCashflow")),
            sector=cls._text(info.get("sector")),
            industry=cls._text(info.get("industry")),
            reading=reading,
        )

    @staticmethod
    def _ratio(value: object) -> float | None:
        """A finite number the provider reported, or nothing."""

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None

        return float(value)

    @classmethod
    def _percentage_as_ratio(cls, value: object) -> float | None:
        number = cls._ratio(value)

        return number / 100.0 if number is not None else None

    @staticmethod
    def _text(value: object) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _inception(value: object) -> datetime | None:
        """When the asset began trading, if the provider says."""

        if not isinstance(value, (int, float)):
            return None

        try:
            return datetime.fromtimestamp(int(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
