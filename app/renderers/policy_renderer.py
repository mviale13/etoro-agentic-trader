from app.domain.investment_policy import InvestmentPolicy


class PolicyRenderer:
    @staticmethod
    def render(policy: InvestmentPolicy) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("Investment Policy")
        print("────────────────────────────────")
        print()

        print(f"Risk Profile : {policy.risk_profile.title()}")
        print()

        print("Target Allocation")

        print(f"Stocks     {policy.target.stocks:>5}%")
        print(f"ETFs       {policy.target.etfs:>5}%")
        print(f"Crypto     {policy.target.crypto:>5}%")
        print(f"Cash       {policy.target.cash:>5}%")

        print()

        print("Constraints")

        print(f"Max Position        {policy.constraints.max_single_position}%")

        print(f"Max Crypto          {policy.constraints.max_crypto}%")

        print(f"Rebalance Threshold {policy.constraints.rebalance_threshold}%")

        print()
