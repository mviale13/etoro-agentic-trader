from app.domain.opportunity_facts import (
    OpportunityFacts,
)
from app.domain.opportunity_scorecard import (
    OpportunityScorecard,
)


class OpportunityScoringService:
    def score(
        self,
        facts: OpportunityFacts,
    ) -> OpportunityScorecard:
        momentum = 50

        if facts.daily_change_percent > 3:
            momentum = 90

        elif facts.daily_change_percent > 1:
            momentum = 75

        elif facts.daily_change_percent < -2:
            momentum = 25

        quality = 70

        valuation = 70

        volatility = 60 if facts.asset_type == "crypto" else 80

        liquidity = 90

        overall = round((momentum + quality + valuation + volatility + liquidity) / 5)

        return OpportunityScorecard(
            symbol=facts.symbol,
            momentum=momentum,
            quality=quality,
            valuation=valuation,
            volatility=volatility,
            liquidity=liquidity,
            overall=overall,
        )
