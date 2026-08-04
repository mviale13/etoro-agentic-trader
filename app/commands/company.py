from app.renderers.company_renderer import CompanyRenderer
from app.services.company_committee_service import CompanyCommitteeService
from app.services.company_signal_service import CompanySignalService
from app.services.watchlist_service import WatchlistService


class CompanyCommand:
    async def run(
        self,
        symbol: str,
    ) -> int:
        normalized_symbol = symbol.upper().strip()

        item = await WatchlistService().find_symbol(
            normalized_symbol,
        )

        if item is None:
            print(f"{normalized_symbol} was not found in your eToro watchlists.")
            return 1

        signals = await CompanySignalService().build(
            item,
        )

        recommendation = CompanyCommitteeService().evaluate(
            item.symbol,
            signals,
        )

        CompanyRenderer().render(
            recommendation,
        )

        return 0


async def run(
    symbol: str,
) -> int:
    return await CompanyCommand().run(
        symbol,
    )
