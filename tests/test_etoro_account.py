from app.brokers.etoro_account import EtoroAccountBroker


def test_calculate_empty_account():
    payload = {
        "credit": 10000,
        "positions": [],
        "ordersForOpen": [],
        "orders": [],
        "mirrors": [],
    }
    cash, invested, pnl, equity = EtoroAccountBroker._calculate_values(payload)
    assert cash == 10000
    assert invested == 0
    assert pnl == 0
    assert equity == 10000


def test_calculate_account_values():
    payload = {
        "credit": 1000,
        "positions": [
            {"amount": 500, "unrealizedPnL": {"pnL": 25}},
        ],
        "ordersForOpen": [
            {"amount": 100, "mirrorID": 0, "totalExternalCosts": 2},
            {"amount": 50, "mirrorID": 123},
        ],
        "orders": [{"amount": 50}],
        "mirrors": [],
    }
    cash, invested, pnl, equity = EtoroAccountBroker._calculate_values(payload)
    assert cash == 850
    assert invested == 652
    assert pnl == 25
    assert equity == 1527
