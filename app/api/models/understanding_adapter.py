"""Turn both understandings into their wire shape, deriving nothing.

Every value here is read off a domain object. The one thing this module
is allowed to do is choose which fields cross the wire; it may not
compute, round, reword or fill in. A reader comparing this file against
`business_understanding.py` and `financial_understanding.py` should find
no arithmetic.
"""

from __future__ import annotations

from app.api.models.understanding import (
    AgreementResponse,
    BusinessUnderstandingResponse,
    FinancialUnderstandingResponse,
    MeasureResponse,
    MechanismResponse,
    SegmentResponse,
    UnderstandingResponse,
    UnestablishedResponse,
)
from app.domain.agreement import Agreement
from app.domain.business_understanding import BusinessUnderstanding
from app.domain.financial_understanding import FinancialUnderstanding
from app.services.company_understanding_service import CompanyUnderstanding


def understanding_response(
    understanding: CompanyUnderstanding,
) -> UnderstandingResponse:
    """Both halves, each carried across or absent with its reason."""

    return UnderstandingResponse(
        business=(
            _business(understanding.business)
            if understanding.business is not None
            else None
        ),
        business_absent_because=understanding.business_absent_because,
        financial=(
            _financial(understanding.financial)
            if understanding.financial is not None
            else None
        ),
        financial_absent_because=understanding.financial_absent_because,
    )


def _agreement(counted: Agreement) -> AgreementResponse:
    return AgreementResponse(
        agreeing=counted.agreeing,
        readings=counted.readings,
        settled=counted.settled,
    )


def _agreement_or_none(counted: Agreement | None) -> AgreementResponse | None:
    """For the widths a domain object may genuinely not have.

    Kept apart from `_agreement` rather than folded into it: a mechanism
    always carries the agreement of the segments that earn that way, and
    a measure carries one only where something was established. Making
    the second shape serve both would let a missing width pass silently
    where the domain guarantees one.
    """

    return None if counted is None else _agreement(counted)


def _business(understanding: BusinessUnderstanding) -> BusinessUnderstandingResponse:
    characteristics = understanding.characteristics

    return BusinessUnderstandingResponse(
        source=understanding.source,
        read=understanding.reading.source,
        quorate=understanding.quorate,
        observation_count=understanding.observation_count,
        quorum=understanding.quorum,
        engine=understanding.engine,
        archetype=(
            characteristics.primary.value
            if characteristics.primary is not None
            else None
        ),
        undecided_because=characteristics.undecided_because,
        narrowest=_agreement_or_none(characteristics.narrowest),
        segments=[
            SegmentResponse(
                name=segment.name,
                share=segment.share,
                unmeasured_because=segment.unmeasured_because,
                earns=[model.value for model in segment.mechanisms],
                earns_because=segment.mechanisms_because,
                depends=segment.depends_stated,
                depends_quoted=segment.depends_quoted,
                depends_support=segment.depends_support,
            )
            for segment in understanding.sells
        ],
        segments_because=understanding.segments_because,
        mechanisms=[
            MechanismResponse(
                model=mechanism.model.value,
                through=list(mechanism.through),
                coverage=mechanism.coverage,
                support=_agreement(mechanism.support),
            )
            for mechanism in understanding.mechanisms
        ],
        not_established=[
            UnestablishedResponse(
                segment=missing.segment,
                dimension=missing.dimension.value,
                because=missing.because,
            )
            for missing in understanding.not_established
        ],
    )


def _financial(understanding: FinancialUnderstanding) -> FinancialUnderstandingResponse:
    established = understanding.language

    return FinancialUnderstandingResponse(
        source=understanding.source,
        read=understanding.reading.source,
        quorate=understanding.quorate,
        observation_count=understanding.observation_count,
        quorum=understanding.quorum,
        statements=[statement.value for statement in understanding.statements],
        language=(established.language.value if established is not None else None),
        language_because=(
            established.absent_because if established is not None else None
        ),
        measures=[
            MeasureResponse(
                measure=measure.measure.value,
                label=measure.label,
                value=measure.value,
                unit=measure.unit.value,
                stated=measure.stated,
                support=_agreement_or_none(measure.support),
                absent_because=measure.absent_because,
            )
            for measure in understanding.measures
        ],
    )
