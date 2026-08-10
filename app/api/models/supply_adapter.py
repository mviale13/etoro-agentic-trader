"""Carry the supply picture over the wire, and interpret nothing.

Formatting and grouping only. Which quantity each number counts, whose
definition decided it and whether two figures really disagree were all
settled in the domain, and each travels in the domain's own words.

No word implying that a supply structure is good, bad, dilutive or
attractive appears here or anywhere downstream. Those are S5's to make,
and only once somebody has ruled what they mean.
"""

from __future__ import annotations

from datetime import datetime

from app.api.models.dossier import (
    SupplyComparisonResponse,
    SupplyFigureResponse,
    SupplyPictureResponse,
)
from app.domain.provenance import Provenance
from app.domain.supply_semantics import (
    SupplyComparison,
    SupplyConcept,
    SupplyFact,
    SupplyPicture,
)

#: The order an investor reads them in: what can exist, what does, what
#: is still to come, what is held to be available, and what was left out.
_ORDER = (
    SupplyConcept.MAX_SUPPLY,
    SupplyConcept.EMITTED_SUPPLY,
    SupplyConcept.FUTURE_EMISSIONS,
    SupplyConcept.CIRCULATING_ESTIMATE,
    SupplyConcept.EXCLUDED_BALANCE,
)


def supply_response(picture: SupplyPicture | None) -> SupplyPictureResponse | None:
    """The supply picture over the wire, or null where it does not apply."""

    if picture is None:
        return None

    figures = [_figure(fact) for concept in _ORDER for fact in picture.of(concept)]

    return SupplyPictureResponse(
        figures=figures,
        comparisons=[_comparison(item) for item in picture.comparisons],
        methodology_disagreement=picture.has_methodology_disagreement,
        unresolved=list(picture.unresolved),
        unavailable_because=picture.unavailable_because,
    )


def _figure(fact: SupplyFact) -> SupplyFigureResponse:
    return SupplyFigureResponse(
        concept=fact.concept.value,
        concept_stated=fact.concept.stated,
        stated=fact.stated,
        defined_by=fact.methodology.defined_by,
        methodology=fact.methodology.stated,
        disclosed=fact.methodology.disclosed,
        excludes=list(fact.methodology.excludes),
        source=fact.source,
        age=_age(fact.source, fact.observed_at),
        reported_as=fact.reported_as,
        standing=fact.standing.value,
        standing_stated=fact.standing.stated,
        authority=fact.authority.value,
        authority_stated=fact.authority.stated,
        because=fact.because,
        caveats=list(fact.caveats),
    )


def _comparison(item: SupplyComparison) -> SupplyComparisonResponse:
    return SupplyComparisonResponse(
        verdict=item.verdict.value,
        verdict_stated=item.verdict.stated,
        left_source=item.left.source,
        left_stated=item.left.stated,
        right_source=item.right.source,
        right_stated=item.right.stated,
        because=item.because,
    )


def _age(source: str | None, observed_at: datetime | None) -> str | None:
    if source is None or observed_at is None:
        return None

    return Provenance(source=source, observed_at=observed_at).stated()
