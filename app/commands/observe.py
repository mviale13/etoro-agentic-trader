"""Take observations of a company's current document up to the quorum.

The explicit spend that fills a consensus, and its own opt-in exactly as
`writer-compare` is: invoking it is the request to pay for the readings.
The stopping rule references only the count — never what any observation
says — which is what keeps this from being read-until-classifiable. An
entry stops at quorum whether its claims settled or not, and an
unsettled consensus at quorum is a finding, not a failure to keep
asking.
"""

from __future__ import annotations

from app.commands.knowledge import _render
from app.services.company_knowledge_service import CompanyKnowledgeService


class ObserveCommand:
    async def run(self, symbol: str) -> int:
        normalized = symbol.upper().strip()

        outcome = await CompanyKnowledgeService().observe(normalized)

        _render(normalized, outcome)

        return 0 if outcome.knowledge is not None else 1


async def run(symbol: str) -> int:
    return await ObserveCommand().run(symbol)
