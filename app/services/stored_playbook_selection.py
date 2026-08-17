"""The governing financial model from stored evidence, and from nothing else.

Why this module exists is a defect, and the defect is worth keeping in
view. `movrvest financials` documented itself *"Read-only and free …
never observes"* and asked `PlaybookSelectionService.select` for its
governing model — whose grounded route opens the **acquiring**
`knowledge()` door, and whose industry fallback fetches the investor's
watchlist from the broker. One run of that command read a filing with a
paid model and archived two watchlist payloads, because the read-only
contract lived in a docstring while the dependency graph said otherwise.

So this is the same selection *rule* built from read-only doors alone,
and the boundary is structural rather than promised:

- the grounded route runs over `CompanyKnowledgeService.established()`,
  which asks the store and stops — the identical rule the dossier's
  earned-playbook section applies;
- there is **no fallback route**, because the industry route's inputs
  (the broker's watchlist, the provider profile) arrive by acquisition,
  and a read surface that cannot fetch them must say so rather than
  fetch them. Where nothing grounded is established, the generic model
  governs and the sentence says why — an absence rendered, not a
  provider silently called.

`tests/test_read_only_purity.py` pins both halves: this module's
dependency graph never touches an acquiring seam, and the command built
on it completes against booby-trapped acquisition doors.
"""

from __future__ import annotations

from app.domain.financial_question import (
    FinancialModel,
    FinancialModelSelection,
    model_for,
)
from app.domain.playbook_selection import PlaybookSelection
from app.services.company_knowledge_service import CompanyKnowledgeService
from app.services.playbook_mapping import select_grounded
from app.services.understanding_engine import understand


class StoredPlaybookSelection:
    """The grounded route over the store's read-only door — no other route.

    Deliberately not a second selector. The rule is `select_grounded`,
    the same canonical mapping `PlaybookSelectionService` and the
    dossier both run; what this class owns is only the refusal to reach
    any input that would have to be acquired.
    """

    def __init__(self, knowledge: CompanyKnowledgeService | None = None) -> None:
        self._knowledge = knowledge or CompanyKnowledgeService()

    def governing(self, symbol: str) -> FinancialModelSelection:
        """Which financial language governs, from what is already held."""

        outcome = self._knowledge.established(symbol.upper().strip())

        if outcome.knowledge is not None:
            grounded = select_grounded(understand(outcome.knowledge))

            if isinstance(grounded, PlaybookSelection):
                # The earned answer, through the one canonical coupling.
                # `model_for` owns which playbook implies which language
                # and words the derivation; nothing is re-decided here.
                return model_for(grounded.playbook.kind)

            refused_because = grounded.because
        else:
            refused_because = outcome.absent_because or (
                "no current reading of this company's filing is held"
            )

        return FinancialModelSelection(
            model=FinancialModel.GENERIC,
            from_playbook=None,
            because=(
                "the generic financial language, because no grounded "
                f"playbook is established from stored evidence — "
                f"{refused_because} This surface reads what has been "
                "acquired and acquires nothing, so the industry route "
                "(a broker and provider lookup) is not consulted; "
                "`movrvest playbook` runs it, and `--model` inspects "
                "another language explicitly."
            ),
        )
