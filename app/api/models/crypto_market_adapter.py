"""Carry the crypto market context over the wire, and interpret nothing.

Formatting and grouping only. Every figure was worded by the domain,
every standing judged there, and every piece of arithmetic performed
there with its inputs named. What this module adds is an age and a
grouping.

No adjective describing a market as strong, weak, risk-on or overheated
appears here or anywhere downstream, and no regime is named. A
difference in percentage points is a measurement; what it is worth is a
question for a layer that does not exist.
"""

from __future__ import annotations

from datetime import datetime

from app.api.models.dossier import (
    ConcentrationResponse,
    ConsideredPeerGroupResponse,
    CryptoMarketContextResponse,
    MarketObservationResponse,
    PeerGroupResponse,
    RelativeReturnResponse,
)
from app.domain.crypto_market import Concentration, MarketObservation, RelativeReturn
from app.domain.crypto_market_context import CryptoMarketContext
from app.domain.provenance import Provenance


def crypto_market_response(
    context: CryptoMarketContext | None,
) -> CryptoMarketContextResponse | None:
    """The market context over the wire, or null where it does not apply."""

    if context is None:
        return None

    snapshot = context.snapshot
    peer = context.peer

    group = peer.group if peer is not None else None

    return CryptoMarketContextResponse(
        market=[_observation(item) for item in snapshot.observations],
        market_source=snapshot.source,
        market_age=_age(snapshot.source, snapshot.observed_at),
        returns=[_observation(item) for item in context.returns],
        peer=(
            PeerGroupResponse(
                key=group.key,
                name=group.name,
                provider=group.provider,
                selected_because=group.selected_because,
                caveats=list(group.caveats),
            )
            if group is not None
            else None
        ),
        peer_unavailable_because=(
            peer.unavailable_because if peer is not None and group is None else None
        ),
        considered=[
            ConsideredPeerGroupResponse(
                name=item.name,
                rejected_because=item.rejected_because,
            )
            for item in (peer.considered if peer is not None else ())
        ],
        peer_observations=[_observation(item) for item in context.peer_observations],
        relative=[_relative(item) for item in context.relative],
        concentrations=[_concentration(item) for item in context.concentrations],
        uncompared=[interval.value for interval in context.uncompared],
        unavailable_because=(
            context.unavailable_because or snapshot.unavailable_because
        ),
    )


def _observation(item: MarketObservation) -> MarketObservationResponse:
    measure = item.measure

    return MarketObservationResponse(
        metric=item.metric.value,
        label=measure.label,
        interval=item.interval.value,
        interval_stated=item.interval.stated,
        stated=item.stated,
        standing=item.standing.value,
        standing_stated=item.standing.stated,
        derived=measure.derived,
        universe=item.universe.described if item.universe is not None else None,
        source=item.source,
        age=_age(item.source, item.observed_at),
        because=item.because,
    )


def _relative(item: RelativeReturn) -> RelativeReturnResponse:
    return RelativeReturnResponse(
        interval=item.interval.value,
        comparator=item.comparator,
        subject_return=f"{item.subject_return:+.2f}%",
        comparator_return=f"{item.comparator_return:+.2f}%",
        delta=f"{item.delta:+.2f} pp",
        standing=item.standing.value,
        stated=item.stated,
        caveat=item.caveat,
    )


def _concentration(item: Concentration) -> ConcentrationResponse:
    return ConcentrationResponse(
        comparator=item.comparator,
        stated=item.stated,
    )


def _age(source: str | None, observed_at: datetime | None) -> str | None:
    """The observation's age, worded the way every reading on the page is."""

    if source is None or observed_at is None:
        return None

    return Provenance(source=source, observed_at=observed_at).stated()
