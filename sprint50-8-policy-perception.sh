#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Sprint 50.8 — PolicyPerception"
echo "============================================================"

mkdir -p app/application/brain/perception

###############################################################################
# PolicyPerception
###############################################################################

cat > app/application/brain/perception/policy_perception.py <<'PY'
"""Policy perception component."""

from app.domain.investment_policy import InvestmentPolicy
from app.services.investor_strategy_service import (
    InvestorStrategyService,
)


class PolicyPerception:
    """Produces the active investment policy."""

    def __init__(
        self,
        strategy_service: InvestorStrategyService | None = None,
    ) -> None:
        self._strategy_service = (
            strategy_service or InvestorStrategyService()
        )

    def execute(self) -> InvestmentPolicy | None:
        return self._strategy_service.load_policy()
PY

###############################################################################
# BrainContextBuilder
###############################################################################

python - <<'PY'
from pathlib import Path

path = Path("app/services/brain_context_builder.py")
content = path.read_text()

content = content.replace(
"""from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)
""",
"""from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)
from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)
"""
)

content = content.replace(
"""from app.services.investor_strategy_service import (
    InvestorStrategyService,
)
""",
""
)

old = """        investment_policy = InvestorStrategyService().load_policy()
"""

new = """        investment_policy = PolicyPerception().execute()
"""

if old not in content:
    raise SystemExit("Policy block not found.")

content = content.replace(old, new)

path.write_text(content)
PY

###############################################################################
# Tests
###############################################################################

cat > tests/test_policy_perception.py <<'PY'
from app.application.brain.perception.policy_perception import (
    PolicyPerception,
)


def test_policy_perception_is_in_perception_layer() -> None:
    assert PolicyPerception.__module__ == (
        "app.application.brain.perception.policy_perception"
    )
PY

ruff check --fix .
ruff format .
mypy app
pytest

echo
echo "============================================================"
echo "PERCEPTION LAYER COMPLETE"
echo "============================================================"

echo
echo "Commit:"
echo
echo "git add \\"
echo " app/application/brain/perception/policy_perception.py \\"
echo " app/services/brain_context_builder.py \\"
echo " tests/test_policy_perception.py"
echo
echo 'git commit -m "refactor: complete perception layer"'
