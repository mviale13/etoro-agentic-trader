"""Carry protocol fundamentals over the wire, and interpret nothing.

Formatting only. Every judgment — standing, availability, methodology,
the account of each — was made in the domain; this groups by entity and
words the amounts. No adjective describing a figure as strong, weak,
healthy or attractive appears here or anywhere downstream: the investor
sees the evidence before the model is allowed an opinion of it.
"""

from __future__ import annotations

from datetime import datetime

from app.api.models.dossier import (
    DerivedFigureResponse,
    ProtocolEntityResponse,
    ProtocolFactResponse,
    ProtocolFundamentalsResponse,
)
from app.domain.protocol_fundamentals import (
    ProtocolFact,
    ProtocolFundamentals,
    ProtocolMetric,
)
from app.domain.provenance import Provenance

#: The metrics counted as notional value rather than money held. Both
#: are dollars; only the wording of the unit differs.
_NOTIONAL = (ProtocolMetric.DEX_VOLUME, ProtocolMetric.OPEN_INTEREST)


def protocol_fundamentals_response(
    fundamentals: ProtocolFundamentals | None,
) -> ProtocolFundamentalsResponse | None:
    """The economics over the wire, or null where the family does not apply."""

    if fundamentals is None:
        return None

    return ProtocolFundamentalsResponse(
        entities=[
            ProtocolEntityResponse(
                key=entity.key,
                name=entity.name,
                kind=entity.kind.value,
                measures=entity.measures,
                mapping_basis=entity.mapping_basis,
                mapping_settled=entity.mapping_settled,
                facts=[_fact(fact) for fact in fundamentals.facts_for(entity.key)],
            )
            for entity in fundamentals.entities
        ],
        derived=[
            DerivedFigureResponse(
                label=figure.label,
                stated_value=_money(figure.value),
                stated=figure.stated,
                caveat=figure.caveat,
            )
            for figure in fundamentals.derived
        ],
        unmapped_because=fundamentals.unmapped_because,
    )


def _fact(fact: ProtocolFact) -> ProtocolFactResponse:
    semantics = fact.semantics

    return ProtocolFactResponse(
        metric=fact.metric.value,
        label=semantics.label,
        family=semantics.family.value,
        stated=(
            _money(fact.value)
            if fact.value is not None and fact.standing.serves_value
            else None
        ),
        window=fact.window,
        standing=fact.standing.value,
        standing_stated=fact.standing.stated,
        availability=fact.availability.value,
        availability_stated=fact.availability.stated,
        source=fact.source,
        age=_age(fact.source, fact.observed_at),
        provider_methodology=fact.provider_methodology,
        because=fact.because,
    )


def _money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    if value >= 1_000:
        return f"${value / 1_000:,.1f}k"

    return f"${value:,.0f}"


def _age(source: str | None, observed_at: datetime | None) -> str | None:
    """The observation's age, worded the way every reading on the page is."""

    if source is None or observed_at is None:
        return None

    return Provenance(source=source, observed_at=observed_at).stated()
