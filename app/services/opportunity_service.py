from app.domain.opportunity import Opportunity


class OpportunityService:
    def top_opportunities(self) -> list[Opportunity]:
        return [
            Opportunity(
                symbol="MSFT",
                action="BUY",
                score=92.0,
                policy_fit=95.0,
                committee_confidence=90.0,
                market_score=91.0,
                diversification_score=88.0,
                reason="Highest overall opportunity today.",
            ),
            Opportunity(
                symbol="ASML",
                action="BUY",
                score=89.0,
                policy_fit=90.0,
                committee_confidence=88.0,
                market_score=87.0,
                diversification_score=89.0,
                reason="Excellent quality at a reasonable valuation.",
            ),
            Opportunity(
                symbol="CSU",
                action="DISCOVER",
                score=87.0,
                policy_fit=86.0,
                committee_confidence=87.0,
                market_score=85.0,
                diversification_score=90.0,
                reason="Matches a long-term compounder profile.",
            ),
        ]
