from app.domain.company_recommendation import CompanyRecommendation


class CompanyRenderer:
    def render(
        self,
        recommendation: CompanyRecommendation,
    ) -> None:
        print("=" * 60)
        print(f"{recommendation.symbol}")
        print("=" * 60)
        print()

        print("Recommendation")
        print("--------------")
        print(recommendation.recommendation)
        print(f"Confidence: {recommendation.confidence}%")
        print()

        print("Signals")
        print("-------")
        print(f"Value     : {recommendation.signals.value.valuation}")
        print(f"Quality   : {recommendation.signals.quality.quality}")
        print(f"Momentum  : {recommendation.signals.momentum.trend}")
        print()

        print("Evidence")
        print("--------")
        for item in recommendation.evidence:
            print(f"• {item}")
