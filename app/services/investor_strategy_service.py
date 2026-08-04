import json
from pathlib import Path
from typing import Any, cast

from app.domain.investment_policy import (
    InvestmentPolicy,
)
from app.services.investment_policy_mapper import (
    InvestmentPolicyMapper,
)


class InvestorStrategyService:
    def __init__(
        self,
        path: Path | None = None,
    ) -> None:
        self._path = path or Path(
            "data/investor_strategy.json",
        )

    def load(self) -> dict[str, Any]:
        with self._path.open(
            encoding="utf-8",
        ) as file:
            return cast(
                dict[str, Any],
                json.load(file),
            )

    def save(
        self,
        strategy: dict[str, Any],
    ) -> dict[str, Any]:
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                strategy,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

        return strategy

    def load_policy(
        self,
    ) -> InvestmentPolicy | None:
        if not self.readiness()["configured"]:
            return None

        return InvestmentPolicyMapper().map(
            self.load(),
        )

    def readiness(self) -> dict[str, object]:
        strategy = self.load()

        objectives = cast(
            dict[str, Any],
            strategy.get("objectives", {}),
        )
        policy = cast(
            dict[str, Any],
            strategy.get(
                "portfolio_policy",
                {},
            ),
        )
        preferences = cast(
            dict[str, Any],
            strategy.get(
                "investment_preferences",
                {},
            ),
        )

        required_fields = {
            "investor_type": preferences.get("investor_type"),
            "primary_goal": objectives.get("primary_goal"),
            "time_horizon_years": objectives.get("time_horizon_years"),
            "maximum_acceptable_drawdown_pct": (
                objectives.get("maximum_acceptable_drawdown_pct")
            ),
            "target_cash_pct": policy.get("target_cash_pct"),
        }

        completed_fields = [
            field
            for field, value in required_fields.items()
            if value is not None and value != ""
        ]

        missing_fields = [
            field
            for field, value in required_fields.items()
            if value is None or value == ""
        ]

        if not completed_fields:
            status = "empty"
        elif missing_fields:
            status = "incomplete"
        else:
            status = "ready"

        return {
            "status": status,
            "configured": status == "ready",
            "completed_fields": len(completed_fields),
            "total_fields": len(required_fields),
            "missing_fields": missing_fields,
            "message": {
                "empty": (
                    "Complete your Investment Policy "
                    "so MOVRvest can personalize its "
                    "advice."
                ),
                "incomplete": (
                    "Your Investment Policy needs a "
                    "little more information before "
                    "it can guide the Brain."
                ),
                "ready": ("Your Investment Policy is ready and active."),
            }[status],
        }
