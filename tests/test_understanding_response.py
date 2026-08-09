"""The wire carries the domain's own values, and computes none of its own.

The dossier's contract says no figure is derived at the API layer. These
tests hold the understanding section to it: every number that crosses is
the number the engine produced, and every absence crosses as the reason
the engine worded rather than as a null a surface would have to explain.
"""

from datetime import UTC, datetime

from app.api.models.understanding_adapter import understanding_response
from app.domain.agreement import agreement
from app.domain.business_understanding import (
    BusinessUnderstanding,
    RevenueMechanism,
    SellsThrough,
)
from app.domain.company_archetype import Archetype, CompanyArchetype
from app.domain.company_knowledge import RevenueModel
from app.domain.financial_statements import StatementKind
from app.domain.financial_understanding import (
    EstablishedMeasure,
    FinancialMeasure,
    FinancialUnderstanding,
)
from app.domain.provenance import Provenance
from app.services.company_understanding_service import CompanyUnderstanding


def business() -> BusinessUnderstanding:
    return BusinessUnderstanding(
        symbol="EXA",
        source="10-K 1 published 2026-02-13, via SEC EDGAR",
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
        quorate=True,
        observation_count=5,
        quorum=5,
        engine="multi-engine — services and transaction lead together",
        sells=(
            SellsThrough(
                name="Consumer",
                share=0.4096,
                unmeasured_because=None,
                mechanisms=(RevenueModel.SERVICES,),
                mechanisms_because=None,
            ),
            SellsThrough(
                name="Other",
                share=None,
                unmeasured_because="No observation settled a size for this segment.",
                mechanisms=(),
                mechanisms_because="No observation settled how this segment earns.",
            ),
        ),
        mechanisms=(
            RevenueMechanism(
                model=RevenueModel.SERVICES,
                through=("Consumer",),
                coverage=0.8324,
                support=agreement("earning", ["a", "a", "a", "a", "b"]),
            ),
        ),
        characteristics=CompanyArchetype(
            symbol="EXA",
            primary=Archetype.DIVERSIFIED,
            secondary=None,
            candidates=(),
            coverage=(),
            measured=0.9,
            explained=0.83,
            missing=(),
            basis=(),
            undecided_because=None,
            source="10-K 1",
            reading=Provenance(source="test", observed_at=datetime.now(UTC)),
            quorate=True,
            narrowest=agreement("narrowest", ["a", "a", "a", "b", "b"]),
        ),
        contingencies=(),
        not_established=(),
        segments_because=None,
    )


def financial() -> FinancialUnderstanding:
    return FinancialUnderstanding(
        symbol="EXA",
        source="10-K 1 published 2026-02-13, via SEC EDGAR",
        reading=Provenance(source="test", observed_at=datetime.now(UTC)),
        quorate=True,
        observation_count=5,
        quorum=5,
        statements=(StatementKind.INCOME_STATEMENT,),
        measures=(
            EstablishedMeasure(
                measure=FinancialMeasure.NET_MARGIN,
                value=0.31268258727192005,
                basis=(),
                stated='"Net income" 57,048 over "Total net revenue" 182,447',
                support=agreement("support", ["a"] * 5),
                absent_because=None,
            ),
            EstablishedMeasure(
                measure=FinancialMeasure.GROSS_MARGIN,
                value=None,
                basis=(),
                stated="",
                support=None,
                absent_because=(
                    "Gross margin needs gross_profit, which is not established."
                ),
            ),
        ),
        language=None,
    )


def test_every_number_crosses_the_wire_unrounded() -> None:
    """A surface rounds for display; the contract must not round for it."""

    response = understanding_response(
        CompanyUnderstanding(
            symbol="EXA",
            business=business(),
            business_absent_because=None,
            financial=financial(),
            financial_absent_because=None,
        )
    )

    assert response.business is not None
    assert response.financial is not None

    assert response.business.segments[0].share == 0.4096
    assert response.business.mechanisms[0].coverage == 0.8324
    assert response.financial.measures[0].value == 0.31268258727192005


def test_a_width_crosses_as_it_was_counted() -> None:
    response = understanding_response(
        CompanyUnderstanding(
            symbol="EXA",
            business=business(),
            business_absent_because=None,
            financial=None,
            financial_absent_because="not read",
        )
    )

    assert response.business is not None

    support = response.business.mechanisms[0].support

    assert (support.agreeing, support.readings) == (4, 5)
    assert not support.settled

    narrowest = response.business.narrowest

    assert narrowest is not None
    assert (narrowest.agreeing, narrowest.readings) == (3, 5)


def test_an_absent_measure_carries_the_engines_own_reason() -> None:
    response = understanding_response(
        CompanyUnderstanding(
            symbol="EXA",
            business=None,
            business_absent_because="No filing has been read.",
            financial=financial(),
            financial_absent_because=None,
        )
    )

    assert response.financial is not None

    absent = response.financial.measures[1]

    assert absent.value is None
    assert absent.absent_because is not None
    assert "not established" in absent.absent_because

    # And the half that is missing says so in the engine's words too.
    assert response.business is None
    assert response.business_absent_because == "No filing has been read."


def test_an_unmeasured_segment_crosses_with_its_reason_not_a_zero() -> None:
    """A null share is never a zero share, on any surface."""

    response = understanding_response(
        CompanyUnderstanding(
            symbol="EXA",
            business=business(),
            business_absent_because=None,
            financial=None,
            financial_absent_because="not read",
        )
    )

    assert response.business is not None

    unmeasured = response.business.segments[1]

    assert unmeasured.share is None
    assert unmeasured.unmeasured_because is not None
    assert unmeasured.earns == []
    assert unmeasured.earns_because is not None


def test_both_halves_absent_is_a_valid_response() -> None:
    """A company nothing has been read for still renders, saying so twice."""

    response = understanding_response(
        CompanyUnderstanding(
            symbol="EXA",
            business=None,
            business_absent_because="No filing has been read for EXA.",
            financial=None,
            financial_absent_because="No financial statement has been read for EXA.",
        )
    )

    assert response.business is None
    assert response.financial is None
    assert response.business_absent_because is not None
    assert response.financial_absent_because is not None
