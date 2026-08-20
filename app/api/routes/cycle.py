"""Serve the latest recorded CIO cycle. A read of the store, and nothing else.

**This endpoint is the reason the homepage can stop deciding.**
`/executive/portfolio` builds a Brain, runs the executive pipeline and
writes a `DecisionJournal` — during a page request. So opening the
homepage acquired evidence, produced decisions and appended journal
entries, which meant page traffic and not the cycle was the origin of
what the investor read, and two visits could disagree for reasons that
had nothing to do with the account.

Here the source is the cycle record. This route reads
`DailyCycleStore.log()` and projects it. There is no builder, no
pipeline, no journal and no provider in the module at all — not
configured off, but absent, so no future edit can reintroduce a spend
behind a page view without adding an import that a guard test will see.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_daily_cycle_store
from app.api.models.cycle import CycleReviewResponse
from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

router = APIRouter(prefix="/cycle", tags=["cycle"])


@router.get("/latest", response_model=CycleReviewResponse)
def latest_cycle(
    store: DailyCycleStore = Depends(get_daily_cycle_store),
) -> CycleReviewResponse:
    """The latest recorded cycle, projected for an investor surface.

    Read-only in the strongest sense available: the only collaborator is
    the append-only store's reader, and the projection beneath is a pure
    function of what it returns.
    """

    return CycleReviewResponse.from_log(store.log())
