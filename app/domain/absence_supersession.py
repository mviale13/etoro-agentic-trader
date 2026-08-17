"""When a reading's absence stops voting, and when it never may.

Two companies reached the same deadlock independently. Coca-Cola holds
five readings answering *no figure located* for `total_revenue* beside
five answering `Net Operating Revenues`; Union Pacific holds five and
five for `Total operating revenues`. Five against five is no majority,
so the claim is unsettled and every margin loses its denominator — and
the older readings are not wrong about anything. They were reading under
a vocabulary that could not accept the label they were looking at, and
they said so honestly.

So this is not *newer evidence wins*, and it must not become that. The
rule below fires on one narrow, provable situation:

> An **absence** loses its vote where the contract that produced it
> provably could not have accepted the label a later reading located
> for the same concept.

Everything else keeps voting. Two positive readings that disagree are a
disagreement and stay one — a difference in vocabulary fingerprints is
not a reason to prefer either. An absence produced under a contract that
*could* have accepted the label is a genuine reader disagreement and
stays one. And an absence whose producing contract cannot be bounded
proves nothing, so it keeps its vote: unknown remains unknown.

## What makes it causal rather than chronological

Nothing here reads a date, a store order, or a band. The chain is:
which concept was absent, which contract produced the absence, which
label a later reading located, and whether that label lies outside every
contract the absence could have come from. The last clause is where a
fingerprint alone is not enough — `vocabulary_contracts` holds the forms
so the question can be asked at all — and it is why widening a
vocabulary for one concept can never touch another's absences.

## What it does not do

It changes no stored byte. A superseded absence is still in the file,
still says exactly what it said, still carries the provenance it was
taken with; the journal keeps telling the truth that under contract A
this producer established nothing. What it loses is a vote in today's
consensus, and only for the one concept whose vocabulary moved.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
)
from app.domain.vocabulary_contracts import bounded_contracts, registry_is_current


class AbsenceStanding(StrEnum):
    """Whether one absence still votes, and why."""

    #: No vocabulary reason to withdraw it.
    ACTIVE = "active"

    #: Every contract this absence could have come from lacks the form a
    #: later reading located. The absence is a true statement about a
    #: narrower contract and no longer speaks to this one.
    SUPERSEDED = "superseded by a vocabulary it was not read under"

    #: The producing contract cannot be bounded, so nothing is proven.
    #: Keeps its vote.
    UNPROVABLE = "producing contract unknown"


@dataclass(frozen=True, slots=True)
class AbsenceRuling:
    """One absence, and what the record says about its authority."""

    concept: StatementConcept
    position: int

    standing: AbsenceStanding
    because: str

    @property
    def votes(self) -> bool:
        return self.standing is not AbsenceStanding.SUPERSEDED


def rule_absences(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[AbsenceRuling, ...]:
    """Every absence for this concept, ruled against the located labels.

    Deterministic and total: one ruling per observation that recorded an
    absence, in stored order, whatever the outcome would be.
    """

    if not registry_is_current(concept):
        # The live vocabulary is newer than anything recorded, so every
        # bound would be short by at least one contract. Refuse to
        # reason rather than reason from a stale lineage.
        return tuple(
            AbsenceRuling(
                concept=concept,
                position=position,
                standing=AbsenceStanding.UNPROVABLE,
                because=(
                    f"the published vocabulary lineage for {concept.value} is "
                    "not current, so no producing contract can be bounded"
                ),
            )
            for position, observation in enumerate(observations)
            if _is_absence(observation, concept)
        )

    located = _located_labels(concept, observations)

    return tuple(
        _rule_one(concept, observation, position, located)
        for position, observation in enumerate(observations)
        if _is_absence(observation, concept)
    )


def voting(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[FinancialStatementObservation, ...]:
    """The observations whose answer for this concept still counts."""

    withdrawn = {
        ruling.position
        for ruling in rule_absences(concept, observations)
        if not ruling.votes
    }

    return tuple(
        observation
        for position, observation in enumerate(observations)
        if position not in withdrawn
    )


# ── one absence ─────────────────────────────────────────────────────


def _rule_one(
    concept: StatementConcept,
    observation: FinancialStatementObservation,
    position: int,
    located: tuple[tuple[str, str | None], ...],
) -> AbsenceRuling:
    """Whether this absence survives every label a later reading found."""

    def ruled(standing: AbsenceStanding, because: str) -> AbsenceRuling:
        return AbsenceRuling(
            concept=concept, position=position, standing=standing, because=because
        )

    if not located:
        return ruled(
            AbsenceStanding.ACTIVE,
            "no reading of this concept located a figure, so there is no "
            "label the absence could have failed to recognise",
        )

    stamped = observation.produced_contract_for(concept)
    candidates = bounded_contracts(concept, stamped)

    if candidates is None:
        return ruled(
            AbsenceStanding.UNPROVABLE,
            (
                f"the reading records {concept.value} as produced under "
                f"{stamped!r}, which is not a published vocabulary"
                if stamped is not None
                else (
                    "the reading records no producing vocabulary for "
                    f"{concept.value}, and none can be bounded from the "
                    "published lineage"
                )
            ),
        )

    for label, by_contract in located:
        if by_contract is not None and by_contract == stamped:
            # Read under the very same contract: a genuine reader
            # disagreement about one document, which is exactly what the
            # quorum exists to measure.
            continue

        if any(vocabulary.accepts(label) for vocabulary in candidates):
            # The absence's own contract could have accepted this label,
            # so failing to find it is a reading difference and not a
            # contract difference. Fingerprint inequality alone proves
            # nothing.
            continue

        names = ", ".join(vocabulary.fingerprint for vocabulary in candidates)

        return ruled(
            AbsenceStanding.SUPERSEDED,
            (
                f"a later reading locates {concept.value} on {label!r}, "
                f"which no vocabulary this absence could have been read "
                f"under accepts ({names}); the absence is a true statement "
                "about a narrower contract and does not speak to this one"
            ),
        )

    return ruled(
        AbsenceStanding.ACTIVE,
        (
            f"every label located for {concept.value} was already "
            "acceptable under the vocabulary this absence was read "
            "under, so the difference is between readings rather than "
            "between contracts"
        ),
    )


def _is_absence(
    observation: FinancialStatementObservation, concept: StatementConcept
) -> bool:
    fact = observation.fact(concept)

    return fact is not None and fact.anchor is None


def _located_labels(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[tuple[str, str | None], ...]:
    """Each label located for this concept, with the contract that found it."""

    found = []

    for observation in observations:
        fact = observation.fact(concept)

        if fact is None or fact.anchor is None:
            continue

        found.append((fact.anchor.label, observation.produced_contract_for(concept)))

    return tuple(found)
