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
