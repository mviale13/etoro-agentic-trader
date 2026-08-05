from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import CompanyProfile, Sector


class CompanyProfiler:
    """Builds a normalized company profile from available company facts."""

    _SECTOR_MAP: dict[str, Sector] = {
        "financials": Sector.FINANCIALS,
        "financial services": Sector.FINANCIALS,
        "healthcare": Sector.HEALTHCARE,
        "health care": Sector.HEALTHCARE,
        "technology": Sector.TECHNOLOGY,
        "information technology": Sector.TECHNOLOGY,
        "industrials": Sector.INDUSTRIALS,
        "consumer": Sector.CONSUMER,
        "consumer cyclical": Sector.CONSUMER,
        "consumer defensive": Sector.CONSUMER,
        "consumer discretionary": Sector.CONSUMER,
        "consumer staples": Sector.CONSUMER,
        "energy": Sector.ENERGY,
        "real estate": Sector.REAL_ESTATE,
        "communication services": Sector.COMMUNICATION_SERVICES,
        "utilities": Sector.UTILITIES,
        "basic materials": Sector.MATERIALS,
        "materials": Sector.MATERIALS,
    }

    def profile(self, company: CompanyFacts) -> CompanyProfile:
        """
        Normalise what the provider reported, and assert nothing else.

        This used to return a business model and a lifecycle as literal
        constants — every company was a mature standard corporate — which
        read as a classification and was a placeholder. What kind of
        business this is is now the playbook's question, answered from
        this profile rather than asserted alongside it.
        """

        return CompanyProfile(
            asset_class=self._normalize_asset_class(company.asset_type),
            sector=self._normalize_sector(company.sector),
            industry=company.industry,
        )

    @staticmethod
    def _normalize_asset_class(asset_type: str) -> AssetClass:
        """
        What kind of security this is, or that nobody established it.

        An asset type this platform does not recognise is UNKNOWN rather
        than an exception: a security described oddly should still be
        analysed, on the honest footing that its kind is not known.
        """

        try:
            return AssetClass(asset_type.strip().casefold())
        except ValueError:
            return AssetClass.UNKNOWN

    def _normalize_sector(self, sector: str | None) -> Sector:
        if sector is None:
            return Sector.OTHER

        normalized = sector.strip().casefold()

        return self._SECTOR_MAP.get(normalized, Sector.OTHER)
