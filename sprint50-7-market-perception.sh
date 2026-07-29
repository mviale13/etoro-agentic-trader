#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "Sprint 50.7 — MarketPerception"
echo "============================================================"

mkdir -p app/application/brain/perception

###############################################################################
# MarketPerception
###############################################################################

cat > app/application/brain/perception/market_perception.py <<'PY'
"""Market perception component."""

from app.domain.market_context import MarketContext
from app.services.market_context_service import MarketContextService


class MarketPerception:
    """Produces the current market context."""

    def __init__(
        self,
        market_service: MarketContextService | None = None,
    ) -> None:
        self._market_service = market_service or MarketContextService()

    def execute(self) -> MarketContext:
        return self._market_service.build()
PY

###############################################################################
# Refactor BrainContextBuilder
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
from app.application.brain.perception.market_perception import (
    MarketPerception,
)
"""
)

content = content.replace(
"""from app.services.market_context_service import (
    MarketContextService,
)
""",
""
)

old = """        market = MarketContextService().build()
"""

new = """        market = MarketPerception().execute()
"""

if old not in content:
    raise SystemExit("MarketContextService block not found.")

content = content.replace(old, new)

path.write_text(content)
PY

###############################################################################
# Tests
###############################################################################

cat > tests/test_market_perception.py <<'PY'
from app.application.brain.perception.market_perception import (
    MarketPerception,
)


def test_market_perception_is_in_perception_layer() -> None:
    assert MarketPerception.__module__ == (
        "app.application.brain.perception.market_perception"
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
echo " app/application/brain/perception/market_perception.py \\"
echo " app/services/brain_context_builder.py \\"
echo " tests/test_market_perception.py"
echo
echo 'git commit -m "refactor: extract market perception"'
