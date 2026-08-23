"""The fundamentals section over the wire, standings and sentences intact.

A projection of `fundamentals_presentation` and nothing more: every row
carries the domain's own sentence beside its state, so the page renders
what the backend said and composes nothing analytical of its own.
"""

from __future__ import annotations

from app.api.models.dossier import FundamentalRowResponse, FundamentalsResponse
from app.domain.fundamentals_presentation import FundamentalFact

#: The one section-level explanation, stated once rather than repeated
#: as a warning under every row.
_EXPLAINED = (
    "Filing-established figures come from the filing itself. Where the "
    "filing establishes nothing, a provider-reported value is shown as an "
    "explicitly labelled fallback — it is descriptive, it is not filing "
    "evidence, and the filing-grade gap it stands in front of still stands."
)


def fundamentals_response(
    facts: tuple[FundamentalFact, ...],
) -> FundamentalsResponse:
    return FundamentalsResponse(
        explained=_EXPLAINED,
        rows=[
            FundamentalRowResponse(
                metric=fact.metric,
                label=fact.label,
                value=fact.value,
                unit=fact.unit,
                standing=fact.standing.value,
                source=fact.source,
                as_of=fact.as_of,
                currency=fact.currency,
                period=fact.period,
                because=fact.because,
                stated=fact.stated,
            )
            for fact in facts
        ],
    )
