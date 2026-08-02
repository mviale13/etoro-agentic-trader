from datetime import UTC, datetime

import yfinance as yf

from app.domain.valuation_snapshot import ValuationSnapshot


class ValueProvider:
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
            observed_at=datetime.now(UTC),
        )
