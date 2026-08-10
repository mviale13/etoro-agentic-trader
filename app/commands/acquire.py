"""Read the market for the whole book, once, on purpose.

The explicit spend that fills the store every surface reads from — the
provider half of the rule `observe` already carries for filings. A page
view serves what this left behind and stops, so nothing an investor opens
waits on a provider, and nothing an investor opens decides to spend.
"""

from __future__ import annotations

from app.domain.market_acquisition import AcquiredSecurity, MarketAcquisition
from app.services.market_acquisition_service import (
    DEFAULT_CANDIDATE_BUDGET,
    MarketAcquisitionService,
)

__all__ = ["DEFAULT_CANDIDATE_BUDGET", "run"]


async def run(
    candidates: int = DEFAULT_CANDIDATE_BUDGET,
    service: MarketAcquisitionService | None = None,
) -> int:
    try:
        acquired = await (service or MarketAcquisitionService()).acquire(
            candidate_budget=candidates,
        )
    except Exception as exc:
        print(f"MOVRvest market acquisition failed: {exc}")

        return 1

    _render(acquired)

    # Nothing priced is a failed cycle: the pages that follow it have no
    # price for anything, and an operator who saw a zero exit code would
    # be told the opposite.
    return 0 if acquired.priced else 1


def _render(acquired: MarketAcquisition) -> None:
    print()
    print("MARKET ACQUISITION")
    print("=" * 60)

    print(
        f"  Securities   {len(acquired.priced)} priced "
        f"of {len(acquired.securities)} asked"
    )
    print(f"  Market strip {len(acquired.instruments)} instruments")
    print(f"  VIX          {acquired.vix if acquired.vix is not None else 'not read'}")

    # The rate the account's euro figures are converted at. Absent here
    # means absent on the page: no rate is invented to fill them.
    if acquired.rate is not None:
        print(
            f"  USD -> EUR   {acquired.rate.rate:.4f}  "
            f"({acquired.rate.reading.stated()})"
        )
    else:
        print("  USD -> EUR   not read, so the euro figures stay absent")

    # Somebody else's published rating, read for the tokens this platform
    # can say least about. Counted, because it is a metered allowance.
    rated = [security for security in acquired.securities if security.rating]

    if rated:
        print(
            f"  Ratings      {len(rated)} tokens "
            f"({', '.join(security.symbol for security in rated)})"
        )

    # The crypto-native provider's market claims — the raw material the
    # validation gate judges on read. The same metered allowance.
    facted = [security for security in acquired.securities if security.token_facts]

    if facted:
        print(
            f"  Token facts  {len(facted)} tokens "
            f"({', '.join(security.symbol for security in facted)})"
        )

    # The economics behind the tokens — a separate evidence family, read
    # per mapped entity. A token with no entity mapped is not counted
    # here at all rather than counted as empty.
    with_protocols = [
        security for security in acquired.securities if security.protocol_facts
    ]

    if with_protocols:
        print(
            f"  Protocols    {len(with_protocols)} tokens "
            f"({', '.join(security.symbol for security in with_protocols)})"
        )

    thin = [
        security
        for security in acquired.securities
        if security.priced and not security.complete
    ]

    if thin:
        print()
        print("  Priced, and thinner than a full reading:")

        for security in thin:
            print(f"    {security.symbol:<12} {_missing(security)}")

    if acquired.unpriced:
        print()
        print("  No price came back — their pages will say so:")

        for security in acquired.unpriced:
            print(f"    {security.symbol}")

    print()


def _missing(security: AcquiredSecurity) -> str:
    """What one security is short of, named rather than counted."""

    absent = []

    if not security.fundamentals:
        absent.append("no fundamentals")

    if security.calendar is False:
        absent.append("no earnings calendar")

    return ", ".join(absent)
