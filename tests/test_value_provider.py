from app.providers.value_provider import ValueProvider


class FakeTicker:
    @property
    def info(self):
        return {
            "forwardPE": 21.5,
            "trailingPE": 24.1,
            "pegRatio": 1.4,
            "dividendYield": 0.012,
        }


def test_value_provider(monkeypatch):
    monkeypatch.setattr(
        "yfinance.Ticker",
        lambda symbol: FakeTicker(),
    )

    valuation = ValueProvider().snapshot("MSFT")

    assert valuation.forward_pe == 21.5
    assert valuation.trailing_pe == 24.1
    assert valuation.peg_ratio == 1.4
    assert valuation.dividend_yield == 0.012


def test_fundamentals_are_read_from_the_same_call() -> None:
    valuation = ValueProvider.from_info(
        {
            "revenueGrowth": 0.164,
            "earningsGrowth": 0.21,
            "grossMargins": 0.486,
            "operatingMargins": 0.31,
            "profitMargins": 0.243,
            "returnOnEquity": 1.5,
            "currentRatio": 1.07,
            "operatingCashflow": 118_000_000_000,
            "freeCashflow": 99_000_000_000,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
    )

    assert valuation.revenue_growth == 0.164
    assert valuation.gross_margin == 0.486
    assert valuation.net_margin == 0.243
    assert valuation.current_ratio == 1.07
    assert valuation.free_cash_flow == 99_000_000_000
    assert valuation.sector == "Technology"


def test_debt_to_equity_is_normalised_from_percent_to_ratio() -> None:
    """Yahoo reports 78.4 for 0.78x; scored raw, every company reads broke."""

    valuation = ValueProvider.from_info({"debtToEquity": 78.4})

    assert valuation.debt_to_equity == 0.784


def test_missing_or_unreadable_fundamentals_are_absent_not_zero() -> None:
    valuation = ValueProvider.from_info(
        {"grossMargins": None, "debtToEquity": "n/a", "sector": ""}
    )

    assert valuation.gross_margin is None
    assert valuation.debt_to_equity is None
    assert valuation.sector is None
