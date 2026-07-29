"""Compatibility import for the relocated application MarketService.

New code should import MarketService from app.application.services.
This module remains temporarily so existing callers can migrate safely.
"""

from app.application.services.market_service import MarketService

__all__ = ["MarketService"]
