from app.domain.opportunity import Opportunity


class OpportunityService:
    def top_opportunities(self) -> list[Opportunity]:
        return [
            Opportunity(
                company="Microsoft",
                action="BUY",
                confidence=92,
                summary="Highest overall opportunity today.",
            ),
            Opportunity(
                company="ASML",
                action="BUY",
                confidence=89,
                summary="Excellent quality at a reasonable valuation.",
            ),
            Opportunity(
                company="Constellation Software",
                action="DISCOVER",
                confidence=87,
                summary="Matches a long-term compounder profile.",
            ),
        ]
