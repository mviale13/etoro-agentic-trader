from typing import Any, cast

from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)

DEFAULT_REBALANCE_THRESHOLD_PCT = 5.0


class InvestmentPolicyMapper:
    def map(
        self,
        strategy: dict[str, Any],
    ) -> InvestmentPolicy:
        preferences = cast(
            dict[str, Any],
            strategy.get(
                "investment_preferences",
                {},
            ),
        )

        portfolio_policy = cast(
            dict[str, Any],
            strategy.get(
                "portfolio_policy",
                {},
            ),
        )

        objectives = cast(
            dict[str, Any],
            strategy.get(
                "objectives",
                {},
            ),
        )

        investor_type = str(preferences.get("investor_type") or "custom")

        target_cash = self._required_number(
            portfolio_policy,
            "target_cash_pct",
        )

        maximum_single_position = self._optional_number(
            portfolio_policy,
            "maximum_single_position_pct",
            default=100.0,
        )

        maximum_crypto = self._optional_number(
            portfolio_policy,
            "maximum_crypto_pct",
            default=0.0,
        )

        # The one figure the investor states about losses rather than about
        # allocations. It was collected by the strategy form, checked for
        # completeness and then read by nothing.
        maximum_drawdown = self._stated_number(
            objectives,
            "maximum_acceptable_drawdown_pct",
        )

        return InvestmentPolicy(
            risk_profile=investor_type,
            target=AllocationTarget(
                stocks=0.0,
                etfs=0.0,
                crypto=0.0,
                cash=target_cash,
            ),
            constraints=InvestmentConstraints(
                max_single_position=(maximum_single_position),
                max_crypto=maximum_crypto,
                rebalance_threshold=(DEFAULT_REBALANCE_THRESHOLD_PCT),
                max_drawdown=maximum_drawdown,
            ),
        )

    def _stated_number(
        self,
        source: dict[str, Any],
        field: str,
    ) -> float | None:
        """The investor's figure, or nothing where they gave none."""

        value = source.get(field)

        if value is None or value == "":
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _required_number(
        self,
        source: dict[str, Any],
        field: str,
    ) -> float:
        value = source.get(field)

        if value is None or value == "":
            raise ValueError(f"Missing required policy field: {field}")

        return float(value)

    def _optional_number(
        self,
        source: dict[str, Any],
        field: str,
        default: float,
    ) -> float:
        value = source.get(field)

        if value is None or value == "":
            return default

        return float(value)
