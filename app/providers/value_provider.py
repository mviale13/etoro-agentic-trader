import yfinance as yf

from app.domain.valuation_snapshot import ValuationSnapshot


class ValueProvider:
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
        )
