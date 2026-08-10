"""Carry the crypto playbook over the wire, and decide nothing.

Formatting and grouping only. Every judgment — which questions apply,
which are declined and why, how far each piece of evidence can be
trusted — was made in the domain, and each is carried in the domain's
own words. No adjective describing a question as strong, weak,
promising or attractive appears here: an applicability is not a verdict,
and a page that shaded it would be scoring by typography.
"""

from __future__ import annotations

from datetime import datetime

from app.api.models.dossier import (
    AnalyticalCapabilityResponse,
    ConsideredArchetypeResponse,
    CryptoPlaybookResponse,
    CryptoQuestionResponse,
    QuestionEvidenceResponse,
    ValueChainLinkResponse,
    ValueChainResponse,
)
from app.domain.crypto_playbook import CryptoPlaybook, DemandCoverage, QuestionCoverage
from app.domain.provenance import Provenance
from app.domain.token_value_flow import ValueChain, ValueChainLink


def crypto_playbook_response(
    playbook: CryptoPlaybook | None,
) -> CryptoPlaybookResponse | None:
    """The playbook over the wire, or null where the family does not apply."""

    if playbook is None:
        return None

    assignment = playbook.assignment
    definition = assignment.definition

    return CryptoPlaybookResponse(
        archetype=assignment.archetype.value,
        name=definition.name,
        explanation=definition.explanation,
        confidence=assignment.confidence.value,
        confidence_stated=assignment.confidence.stated,
        because=assignment.because,
        rests_on=list(assignment.rests_on),
        does_not_establish=list(assignment.does_not_establish),
        alternatives=[
            ConsideredArchetypeResponse(
                archetype=alternative.archetype.value,
                not_chosen_because=alternative.not_chosen_because,
            )
            for alternative in assignment.alternatives
        ],
        not_classified_from=list(assignment.not_classified_from),
        capabilities=[
            AnalyticalCapabilityResponse(
                key=capability.value,
                label=capability.label,
                reads=capability.reads,
            )
            for capability in assignment.capabilities
        ],
        unmodelled=list(definition.unmodelled),
        questions=[_question(item) for item in playbook.coverage],
        chains=[_chain(chain) for chain in playbook.chains],
        unmapped_because=playbook.unmapped_because,
    )


def _question(item: QuestionCoverage) -> CryptoQuestionResponse:
    applicability = item.applicability

    return CryptoQuestionResponse(
        key=item.question.key.value,
        label=item.question.label,
        asks=item.question.asks,
        matters_because=item.question.matters_because,
        cell=item.cell.value,
        cell_stated=item.cell.stated,
        applicability=applicability.state.value,
        applicability_because=applicability.because,
        asked_by=(
            applicability.asked_by.label if applicability.asked_by is not None else None
        ),
        best_standing=item.best_standing.value,
        best_standing_stated=item.best_standing.stated,
        # Empty for an inapplicable question, and empty in the domain
        # too — the service never gathers evidence for one. Listing what
        # would have answered a question this platform holds to be the
        # wrong one would present a decline as a gap, which is the
        # distinction the whole layer exists on.
        evidence=[_evidence(covered) for covered in item.covered],
    )


def _evidence(covered: DemandCoverage) -> QuestionEvidenceResponse:
    return QuestionEvidenceResponse(
        demand=covered.demand.stated,
        met=covered.is_met,
        stated=covered.stated,
        standing=covered.standing.value,
        standing_stated=covered.standing.stated,
        source=covered.source,
        age=_age(covered.source, covered.observed_at),
        entity=covered.entity,
        because=covered.because,
    )


def _chain(chain: ValueChain) -> ValueChainResponse:
    return ValueChainResponse(
        entity=chain.entity.name,
        kind=chain.entity.kind.stated,
        measures=chain.entity.measures,
        mapping_settled=chain.entity.mapping_settled,
        links=[_link(link) for link in chain.links],
        mechanism=chain.mechanism.value,
        mechanism_stated=chain.mechanism.stated,
        mechanism_source_wording=chain.mechanism_stated,
        because=chain.because,
    )


def _link(link: ValueChainLink) -> ValueChainLinkResponse:
    return ValueChainLinkResponse(
        stage=link.stage.value,
        label=link.stage.label,
        stated=(
            _money(link.value)
            if link.value is not None and link.standing.serves_value
            else None
        ),
        window=link.window,
        standing=link.standing.value,
        standing_stated=link.standing.stated,
        availability_stated=link.availability.stated,
        methodology=link.methodology,
        because=link.because,
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
