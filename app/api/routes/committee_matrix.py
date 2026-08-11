"""Serve the independent committee portfolio. A read, and nothing else.

Deliberately its own endpoint rather than a section of the dossier.
Placing it on the dossier would mean deciding *where in the investor's
narrative* a collection of independent structural judgments belongs, and
that decision is the layer this slice was told not to build. A
standalone read has no such opinion: it serves the projection and stops.

**Every semantic decision is already made server-side.** The payload
carries states and the committees' own sentences — `posture_stated`,
`verdict_stated`, `stated` — never the raw material from which a client
could infer what a verdict means, whether a question applies, or how two
committees relate. The dashboard presents; it never calculates, and here
there is nothing left to calculate.

No aggregate is served because none exists. There is no overall verdict
in the payload, no agreement, no score, no ranking and no ordering that
means anything.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.crypto_committees import CONTRACTS

router = APIRouter(prefix="/committees", tags=["committees"])


@router.get("/contracts")
async def get_contracts() -> dict[str, Any]:
    """Which committees are registered, and what each one asks.

    Served separately from any asset so a client can render column
    headings — and the question with them, because a heading of
    *Supply Governance* alone tells a reader nothing about what a cell
    beneath it means.
    """

    return {
        "committees": [
            {
                "key": contract.key,
                "name": contract.name,
                "question": contract.question,
                "version": contract.version,
                "fingerprint": contract.fingerprint,
                "stated": contract.stated,
                "verdicts": list(contract.verdicts),
            }
            for contract in CONTRACTS
        ]
    }


@router.get("/{symbol}")
async def get_committee_matrix(symbol: str) -> dict[str, Any]:
    """What every registered committee has concluded about this asset.

    Read-only: it opens the judgment record and returns it. It convenes
    no committee, so requesting it can neither spend nor manufacture a
    judgment event — the rule every knowledge surface on this platform
    already lives by.
    """

    return CommitteeMatrixService().for_asset(symbol).as_dict()
