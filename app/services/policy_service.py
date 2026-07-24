from pathlib import Path

import yaml

from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)


class PolicyService:
    def __init__(self, path: str = "config/policy.yaml"):
        self.path = Path(path)

    def load(self) -> InvestmentPolicy:
        with self.path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return InvestmentPolicy(
            risk_profile=data["risk_profile"],
            target=AllocationTarget(**data["target"]),
            constraints=InvestmentConstraints(**data["constraints"]),
        )
