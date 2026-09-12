"""One security, from every broker row that reports it.

**eToro reports a position per *trade*.** An account holding one
security bought twice arrives as two rows, and every layer that reads
one row as one security produces a wrong investor-facing number. That
has now been found four times — a 20.0% + 0.5% BTC holding read as
compliant with a 20% limit, a largest-holding name that disagreed with
the percentage beside it, a cycle record printing one security's whole
share beside each partial value, and a holdings table ranking ETOR 7th
and 16th when it is the account's 4th largest position.

Each sighting was fixed where it was found, so the same fold was
written three times over the same rows with the same key. This is that
fold, once. `PortfolioService._largest_position`,
`_portfolio_weights` and the portfolio surface all read it, and a
fifth caller gets it for free rather than writing a fourth copy.

**What this is not.** `holdings_by_security`
(`app/domain/daily_cycle.py`) folds `RecordedHolding` — a *stored
record*, repaired on read, carrying no instrument identity and a share
that is already the security's. It answers a different question about
different data and is deliberately left alone; see its own docstring
for the contract, which is the opposite of this one.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.portfolio_position import PortfolioPosition


@dataclass(frozen=True, slots=True)
class HeldSecurity:
    """Every open trade in one instrument, as the single holding it is.

    The money adds; the identity does not. `trades` is how many broker
    rows were folded into this one — a count of transactions, never a
    quantity of anything owned.
    """

    #: The broker's own instrument identity, which is what this folds
    #: on. Never the symbol: see `held_securities`.
    instrument_id: int

    #: The resolved ticker, or the broker's placeholder. Carried exactly
    #: as the first resolved row stated it — not upper-cased, not
    #: stripped. A caller that needs a normalised key normalises it,
    #: because two callers here disagreed on whether to.
    symbol: str

    #: Whether a tradeable ticker was resolved for this instrument. An
    #: unresolved holding is still a holding the investor owns, so it is
    #: folded and carried rather than dropped.
    resolved: bool

    #: The first asset class any row stated, or None where none did.
    asset_class: str | None

    quantity: float
    invested_usd: float

    #: Summed **unrounded**. Rounding belongs where the figure is
    #: presented: rounding here would move a percentage derived from it,
    #: and `_largest_position` measures a policy limit with that
    #: percentage.
    market_value_usd: float

    unrealized_pnl_usd: float

    #: How many broker rows this holding was reported as.
    trades: int


def held_securities(
    positions: Iterable[PortfolioPosition],
) -> tuple[HeldSecurity, ...]:
    """One entry per instrument, largest first.

    **Folded on `instrument_id`, never on the symbol.** The broker
    reports every position with an empty symbol and a real instrument
    id; symbols are resolved from the watchlists a step later. Folding
    on the symbol therefore collapsed the whole account into one
    nameless holding and reported it as the largest — the scar is in
    `PortfolioService._largest_position`'s own history. A live account
    whose rows all happen to be resolved makes a symbol fold look
    correct right up until one is not.

    **Ranked here as well as folded here**, because a fold changes the
    ranking: two small trades can outweigh a larger single one. On the
    live account eleven of thirteen securities move, and ETOR goes from
    rows 7 and 16 to the fourth largest holding. A caller handed an
    order that no longer matched its own values could only fix it by
    sorting, which is analysis a presentation layer may not do.

    **Ties keep the broker's order**, so the first of two equal
    holdings is the first the broker reported — `sorted` is stable, and
    `max` returned the first maximal element, which is the behaviour
    this replaced.

    Identity is taken from the **first** row that resolves one, for both
    the symbol and the asset class. Two rows of one instrument stating
    *different* symbols would be a contradiction rather than an
    aggregation, and this does not raise on it: the two folds replaced
    here disagreed silently — one kept the first symbol, the other the
    last — and neither has ever failed. Turning a refactor into a new
    way for a live cycle to crash is not a trade this makes. Recorded,
    not solved.
    """

    folded: dict[int, HeldSecurity] = {}

    for position in positions:
        held = folded.get(position.instrument_id)

        if held is None:
            folded[position.instrument_id] = HeldSecurity(
                instrument_id=position.instrument_id,
                symbol=position.symbol,
                resolved=position.is_resolved,
                asset_class=position.asset_class,
                quantity=position.quantity or 0.0,
                invested_usd=position.invested_usd or 0.0,
                market_value_usd=position.market_value_usd or 0.0,
                unrealized_pnl_usd=position.unrealized_pnl_usd or 0.0,
                trades=1,
            )
            continue

        folded[position.instrument_id] = HeldSecurity(
            instrument_id=held.instrument_id,
            # The first resolved row names the holding. An unresolved
            # row carries a placeholder, and a placeholder must never
            # displace a ticker that was actually resolved.
            symbol=held.symbol if held.resolved else position.symbol,
            resolved=held.resolved or position.is_resolved,
            asset_class=(
                held.asset_class
                if held.asset_class is not None
                else position.asset_class
            ),
            quantity=held.quantity + (position.quantity or 0.0),
            invested_usd=held.invested_usd + (position.invested_usd or 0.0),
            market_value_usd=(
                held.market_value_usd + (position.market_value_usd or 0.0)
            ),
            unrealized_pnl_usd=(
                held.unrealized_pnl_usd + (position.unrealized_pnl_usd or 0.0)
            ),
            trades=held.trades + 1,
        )

    return tuple(
        sorted(
            folded.values(),
            key=lambda held: held.market_value_usd,
            reverse=True,
        )
    )
