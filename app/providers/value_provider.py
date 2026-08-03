from datetime import UTC, datetime

import yfinance as yf

from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot


class ValueProvider:
    SOURCE = "Yahoo Finance"

    """
    Read the fundamentals a single provider call already returns.

    One request carries valuation, size and earnings. Reading only part of
    it and reporting the rest as unavailable would understate what the
    platform can evidence about a company.
    """

    def snapshot(
        self,
        symbol: str,
    ) -> ValuationSnapshot:
        info = yf.Ticker(symbol).info

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
            inception=self._inception(info.get("startDate")),
            reading=Provenance(source=self.SOURCE, observed_at=datetime.now(UTC)),
        )

    @staticmethod
    def _inception(value: object) -> datetime | None:
        """When the asset began trading, if the provider says."""

        if not isinstance(value, (int, float)):
            return None

        try:
            return datetime.fromtimestamp(int(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
