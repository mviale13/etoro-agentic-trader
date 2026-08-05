from dataclasses import dataclass
from enum import StrEnum

from app.domain.asset_class import AssetClass


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

    It is the bridge between raw facts and the playbook chosen for them.

    It once carried a `business_model` and a `lifecycle` as well. Both were
    literal constants — every company in existence was a mature standard
    corporate — and nothing read either of them. The question they were
    meant to answer belongs to the playbook, and it is answered there from
    evidence rather than asserted here.
    """

    #: What kind of security this is. It outranks the industry: a token
    #: filed under "financial services" is still a token.
    asset_class: AssetClass

    sector: Sector
    industry: str | None = None
