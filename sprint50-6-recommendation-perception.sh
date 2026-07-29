#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Sprint 50.6 — RecommendationPerception"
echo "============================================================"

mkdir -p app/application/brain/perception

###############################################################################
# RecommendationPerception
###############################################################################

cat > app/application/brain/perception/recommendation_perception.py <<'PY'
"""Recommendation perception component."""

from app.domain.recommendation import Recommendation
from app.repositories.event_repository import EventRepository
from app.services.committee_service import CommitteeService


class RecommendationPerception:
    """Produces the executive recommendation."""

    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._committee = CommitteeService(repository)

    async def execute(self) -> Recommendation:
        return await self._committee.evaluate()
PY

###############################################################################
# Refactor BrainContextBuilder
###############################################################################

python - <<'PY'
from pathlib import Path

path = Path("app/services/brain_context_builder.py")

content = path.read_text()

content = content.replace(
"""from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
""",
"""from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)
"""
)

content = content.replace(
"""from app.services.committee_service import (
    CommitteeService,
)
""",
""
)

old = """        recommendation = await CommitteeService(
            repository,
        ).evaluate()
"""

new = """        recommendation = await RecommendationPerception(
            repository=repository,
        ).execute()
"""

if old not in content:
    raise SystemExit("Committee block not found.")

content = content.replace(old, new)

path.write_text(content)
PY

###############################################################################
# Tests
###############################################################################

cat > tests/test_recommendation_perception.py <<'PY'
from app.application.brain.perception.recommendation_perception import (
    RecommendationPerception,
)


def test_recommendation_perception_is_in_perception_layer():
    assert RecommendationPerception.__module__ == (
        "app.application.brain.perception.recommendation_perception"
    )
PY

ruff check --fix .
ruff format .
mypy app
pytest

echo
echo "============================================================"
echo "DONE"
echo "============================================================"

echo
echo "Commit:"
echo
echo "git add \\"
echo " app/application/brain/perception/recommendation_perception.py \\"
echo " app/services/brain_context_builder.py \\"
echo " tests/test_recommendation_perception.py"
echo
echo 'git commit -m "refactor: extract recommendation perception"'
