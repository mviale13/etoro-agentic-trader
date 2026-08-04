from dataclasses import dataclass

from app.domain.company_facts import CompanyFacts
from app.domain.company_profile import CompanyProfile


@dataclass(frozen=True, slots=True)
class CompanyResearchContext:
    """Complete context provided to every company research analyst.

    This object groups the immutable inputs required to evaluate a company:

    - CompanyFacts: observable financial and market data.
    - CompanyProfile: business characteristics that determine how those
      facts should be interpreted.

    Analysts receive this context as read-only and produce opinions without
    modifying its contents.
    """

    facts: CompanyFacts
    profile: CompanyProfile
