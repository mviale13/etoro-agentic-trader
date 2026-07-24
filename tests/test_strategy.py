from app.strategy.sma import moving_average_signal


def test_buy_signal():
    assert moving_average_signal(list(range(1, 31))).action == "buy"


def test_hold_without_history():
    assert moving_average_signal([1, 2, 3]).action == "hold"
