from app.domain.morning_brief import MorningBrief


class MorningRenderer:
    @staticmethod
    def _money(value: float | None) -> str:
        return "Unavailable" if value is None else f"${value:,.2f}"

    @classmethod
    def render(cls, brief: MorningBrief) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("Good morning, Marcos.")
        print()
        print(f"Portfolio health: {brief.portfolio_health}")
        print(f"Portfolio value:  {cls._money(brief.portfolio_value)}")
        print(f"Cash allocation:  {brief.cash_allocation:.1f}%")
        print(f"Open positions:   {brief.open_positions}")
        print()
        print(f"Recommendation:   {brief.recommendation}")
        print(f"Confidence:       {brief.confidence}%")
        print()
        print(brief.summary)
        print()
