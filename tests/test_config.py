from app.config import Settings


def test_csv_lists_parse():
    settings = Settings(
        _env_file=None,
        allowed_symbols="BTC,ETH,SPY",
        crypto_symbols="BTC,ETH",
    )
    assert settings.allowed_symbols == ["BTC", "ETH", "SPY"]
    assert settings.crypto_symbols == ["BTC", "ETH"]
