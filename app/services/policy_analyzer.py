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

        # An unmeasured difference cannot pass a threshold. Treating None
        # as compliant would report a policy-compliant account on the
        # strength of a figure nobody could read.
        compliant = all(
            item.difference is not None and abs(item.difference) <= threshold
            for item in differences
        )

        return PolicyAnalysis(
            allocations=differences,
            compliant=compliant,
        )

    @staticmethod
    def _compare(
        asset: str,
        current: float | None,
        target: float,
    ) -> AllocationDifference:
        """One allocation against its target, or an unmeasured difference.

        A None current reading yields a None difference rather than a
        zero one: an allocation nobody could read is not an allocation
        sitting exactly on its target, and compliance must not be
        credited to it.
        """

        if current is None:
            return AllocationDifference(
                asset=asset,
                current=None,
                target=round(target, 2),
                difference=None,
            )

        return AllocationDifference(
            asset=asset,
            current=round(current, 2),
            target=round(target, 2),
            difference=round(current - target, 2),
        )
