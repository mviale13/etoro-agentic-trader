"""What this platform already believes a symbol denotes, from held evidence.

The read-only half of the issuer guard. It asks the stores what they
hold and stops: no fetch, no model, and nothing written.

**The identity is derived, not stored.** Every source this platform has
ever kept carries the issuer's registry number inside the address it was
fetched from — `/edgar/data/4962/…` — so the guarantee needed no new
field, no schema bump and no backfill of records taken before it
existed. A record that predates the guard is as protected as one taken
after it.
"""

from __future__ import annotations

from app.domain.issuer_identity import IssuerIdentity, issuer_id_in
from app.domain.primary_source import PrimarySource
from app.repositories.financial_statement_store import JsonFinancialStatementStore


def held_issuer_identity(symbol: str) -> IssuerIdentity | None:
    """The issuer the newest held evidence for this symbol was read from.

    `None` where nothing is held, or where what is held states no issuer
    number this can read. Both are honestly unguarded rather than
    silently passing: a first reading has nothing to disagree with, and
    an address this cannot parse yields no claim rather than a guess.

    The **newest** filing rather than the oldest, deliberately. A symbol
    that changed hands legitimately — the platform re-read the new
    issuer under the operator's own direction — settles on the identity
    it most recently accepted, and the next reassignment is caught
    against that. Comparing against the oldest would leave a company
    permanently refused for a change already accounted for.
    """

    return _identity_of(_newest_source(symbol))


def _newest_source(symbol: str) -> PrimarySource | None:
    store = JsonFinancialStatementStore()

    newest: PrimarySource | None = None

    for path in store.directory.glob(f"{symbol.upper().strip()}.*.json"):
        for observation in store._restore(path):
            source = observation.source

            if newest is None or source.published_on > newest.published_on:
                newest = source

    return newest


def _identity_of(source: PrimarySource | None) -> IssuerIdentity | None:
    if source is None:
        return None

    issuer = issuer_id_in(source.location)

    if issuer is None:
        return None

    return IssuerIdentity(
        symbol=source.symbol,
        registry=source.provider,
        issuer_id=issuer,
        name=source.company,
        observed_on=source.published_on,
    )
