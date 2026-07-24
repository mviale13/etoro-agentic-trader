from app.domain.policy_analysis import (
    AllocationDifference,
    PolicyAnalysis,
)
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.investment_policy import InvestmentPolicy


class PolicyAnalyzer:
    def analyze(
        self,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> PolicyAnalysis:

        def compare(current: float, target: float):
            return AllocationDifference(
                current=current,
                target=target,
                difference=round(current - target, 2),
            )

        analysis = PolicyAnalysis(
            stocks=compare(
                portfolio.allocation.stocks,
                policy.target.stocks,
            ),
            etfs=compare(
                portfolio.allocation.etfs,
                policy.target.etfs,
            ),
            crypto=compare(
                portfolio.allocation.crypto,
                policy.target.crypto,
            ),
            cash=compare(
                portfolio.allocation.cash,
                policy.target.cash,
            ),
            compliant=True,
        )

        compliant = all(
            abs(item.difference)
            <= policy.constraints.rebalance_threshold
            for item in (
                analysis.stocks,
                analysis.etfs,
                analysis.crypto,
                analysis.cash,
            )
        )

        return PolicyAnalysis(
            stocks=analysis.stocks,
            etfs=analysis.etfs,
            crypto=analysis.crypto,
            cash=analysis.cash,
            compliant=compliant,
        )