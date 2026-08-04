from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import (
    BusinessModel,
    CompanyLifecycle,
    CompanyProfile,
    Sector,
)


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
        return CompanyProfile(
            business_model=BusinessModel.STANDARD_CORPORATE,
            lifecycle=CompanyLifecycle.MATURE,
            sector=self._normalize_sector(company.sector),
            industry=company.industry,
        )

    def _normalize_sector(self, sector: str | None) -> Sector:
        if sector is None:
            return Sector.OTHER

        normalized = sector.strip().casefold()

        return self._SECTOR_MAP.get(normalized, Sector.OTHER)
