import pytest

from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.watchlist_item import WatchlistItem
from app.services.company_signal_service import CompanySignalService
from tests.conftest import admissible_market_cap


class FakeFactsService:
    async def build(
        self,
        item: WatchlistItem,
    ) -> CompanyFacts:
        return CompanyFacts(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            name=item.name,
            asset_type="Stock",
            exchange="NASDAQ",
            current_price=100.0,
            daily_change_pct=2.3,
            market_cap=20_000_000_000,
            market_cap_magnitude=admissible_market_cap(20_000_000_000),
            forward_pe=16.0,
            eps=5.0,
            dividend_yield=0.01,
            sector="Technology",
            industry="Software",
        )


def item() -> WatchlistItem:
    return WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )


@pytest.mark.anyio
async def test_build_company_signals() -> None:
    service = CompanySignalService(
        facts_service=FakeFactsService(),
    )

    signals = await service.build(item())

    assert isinstance(signals, CompanySignals)
    assert signals.value.valuation == "CHEAP"
    assert signals.momentum.trend == "BULLISH"
    assert signals.quality.quality == "HIGH"
