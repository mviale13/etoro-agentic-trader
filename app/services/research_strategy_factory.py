from app.domain.company_profile import BusinessModel, CompanyProfile
from app.services.research_strategy import (
    CorporateResearchStrategy,
    ResearchStrategy,
)


class ResearchStrategyFactory:
    """Selects the research strategy appropriate for a company profile."""

    def create(self, profile: CompanyProfile) -> ResearchStrategy:
        if profile.business_model is BusinessModel.STANDARD_CORPORATE:
            return CorporateResearchStrategy()

        raise ValueError(
            f"No research strategy available for business model: "
            f"{profile.business_model.value}"
        )
