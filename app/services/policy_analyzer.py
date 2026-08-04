from app.domain.investment_policy import InvestmentPolicy
from app.domain.policy_analysis import (
    AllocationDifference,
    PolicyAnalysis,
)
from app.domain.portfolio_snapshot import PortfolioSnapshot


class PolicyAnalyzer:
    def analyze(
        self,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> PolicyAnalysis:
        differences = (
            self._compare(
                "stocks",
                portfolio.allocation.stocks,
                policy.target.stocks,
            ),
            self._compare(
                "etfs",
                portfolio.allocation.etfs,
                policy.target.etfs,
            ),
            self._compare(
                "crypto",
                portfolio.allocation.crypto,
                policy.target.crypto,
            ),
            self._compare(
                "cash",
                portfolio.allocation.cash,
                policy.target.cash,
            ),
        )

        threshold = policy.constraints.rebalance_threshold

        compliant = all(abs(item.difference) <= threshold for item in differences)

        return PolicyAnalysis(
            allocations=differences,
            compliant=compliant,
        )

    @staticmethod
    def _compare(
        asset: str,
        current: float,
        target: float,
    ) -> AllocationDifference:
        return AllocationDifference(
            asset=asset,
            current=round(current, 2),
            target=round(target, 2),
            difference=round(current - target, 2),
        )
