from dataclasses import dataclass
from datetime import datetime

from app.domain.committee_vote import CommitteeVote


@dataclass(frozen=True, slots=True)
class InvestmentDossier:
    """
    Complete investment case prepared by the Artificial CIO.

    This object contains everything required for an investor to
    review one investment opportunity.

    It is intentionally simple for MOVRvest v0.9 and will evolve
    as new capabilities are introduced.
    """

    # Investment
    symbol: str
    name: str

    # Executive assessment (0-100)
    executive_score: int

    # One-paragraph executive briefing
    executive_summary: str

    # Opinions from the investment committees
    committee_votes: tuple[CommitteeVote, ...]

    # Current market context relevant to this investment
    market_summary: str

    # Impact on the investor's portfolio if executed
    portfolio_impact: str

    # Main risks identified by the Brain
    risk_summary: str

    # Suggested maximum allocation
    suggested_allocation: str

    # Supporting evidence
    evidence: tuple[str, ...]

    # Generation timestamp
    generated_at: datetime
