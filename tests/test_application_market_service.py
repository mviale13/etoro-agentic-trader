"""Architecture tests for the MarketService application-layer migration."""

from app.application.services import MarketService as ApplicationMarketService
from app.services.market_service import MarketService as LegacyMarketService


def test_legacy_market_service_import_remains_compatible() -> None:
    assert LegacyMarketService is ApplicationMarketService


def test_market_service_is_defined_in_application_layer() -> None:
    assert ApplicationMarketService.__module__ == (
        "app.application.services.market_service"
    )
