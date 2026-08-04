from dataclasses import dataclass
from enum import StrEnum


class BusinessModel(StrEnum):
    """The economic structure through which a company creates value."""

    STANDARD_CORPORATE = "standard_corporate"
    BANK = "bank"
    INSURER = "insurer"
    REIT = "reit"
    ASSET_MANAGER = "asset_manager"
    EARLY_STAGE = "early_stage"


class CompanyLifecycle(StrEnum):
    """The company's current stage of economic development."""

    EARLY_STAGE = "early_stage"
    GROWTH = "growth"
    MATURE = "mature"
    DECLINING = "declining"


class Sector(StrEnum):
    """Broad economic sector used to contextualize company analysis."""

    FINANCIALS = "financials"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    INDUSTRIALS = "industrials"
    CONSUMER = "consumer"
    ENERGY = "energy"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"
    UTILITIES = "utilities"
    MATERIALS = "materials"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class CompanyProfile:
    """Business context used to interpret CompanyFacts.

    Unlike CompanyFacts, which represent observable data, CompanyProfile
    represents the structural characteristics of a business that determine
    how it should be analyzed.

    It is the bridge between raw facts and the research strategy.
    """

    business_model: BusinessModel
    lifecycle: CompanyLifecycle
    sector: Sector
    industry: str | None = None
