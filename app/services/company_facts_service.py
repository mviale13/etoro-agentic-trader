from app.domain.company_facts import CompanyFacts
from app.domain.watchlist_item import WatchlistItem


class CompanyFactsService:
    async def build(
        self,
        item: WatchlistItem,
    ) -> CompanyFacts:
        return CompanyFacts(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            name=item.name,
            asset_type=str(item.asset_type_id),
            exchange=str(item.exchange_id),
            current_price=None,
            daily_change_pct=None,
            market_cap=None,
            forward_pe=None,
            eps=None,
            dividend_yield=None,
            sector=None,
            industry=None,
        )
