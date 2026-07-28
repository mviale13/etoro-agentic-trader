import pytest

from app.domain.watchlist_item import WatchlistItem
from app.services.company_facts_service import CompanyFactsService


@pytest.mark.anyio
async def test_build_company_facts_from_watchlist_item() -> None:
    item = WatchlistItem(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )

    facts = await CompanyFactsService().build(item)

    assert facts.instrument_id == 1004
    assert facts.symbol == "MSFT"
    assert facts.name == "Microsoft"
