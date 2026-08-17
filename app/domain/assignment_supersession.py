"""When a positive assignment stops voting for a concept its statement disproves.

The third authority rule in the statement stream, beside two siblings it is
deliberately not merged with:

- **BQ20, `absence_supersession`** withdraws a historical *absence* where
  the contract that produced it provably could not have accepted the label
  a later reading located. Its proof is about what a reader *could see*.
- **BQ23, `financing_cost_refusal`** refuses a settled *positive* the
  concept it was read for, where the statement's own structure disproves
  the semantic role. Its proof is about what a figure *is*.
- **This module** withdraws a historical positive *assignment*: physical
  fact F stops voting as concept A where a later native reading — asked
  about both concepts — assigned the very same printed fact to a mutually
  exclusive concept B, on evidence the statement itself carries. Its proof
  is about *which question a fact answers*.

The case that earned it is BQ26's measured regression. Goldman's five
production readings assign `Total net revenues` 58,283 at one cell to
`TOTAL_REVENUE`; five later native readings assign the identical cell to
`REVENUE_NET_OF_INTEREST_EXPENSE`. That is not a disagreement about the
figure — every reading agrees to the digit what the filer printed. It is a
later, semantically qualified assignment of the same fact, and pooling the
two as one question deadlocks the claim 5-against-5 and replaces BQ23's
truthful refusal with *unsettled*.

## The rule

> A historical positive assignment of physical fact F to concept A loses
> its vote for A only where **all** of the following are proven:
>
> 1. another stored observation establishes **the same physical fact F** —
>    the same cell, the same row label, the same printed value, the same
>    period header (`same_reported_fact`);
> 2. that observation assigns F to a **different concept B**;
> 3. A and B **both** declare semantic qualification rules (`GOVERNED`);
> 4. those rules are **mutually exclusive for this occurrence** — one
>    marker concept, opposite requirements;
> 5. the deciding evidence is **in the statement itself**, read by the
>    superseding observation — its own established marker satisfies B's
>    requirement and refutes A's, through the same `refusal_for` every
>    consensus runs;
> 6. the superseding observation is **native to both questions** — it
>    carries producing-contract stamps for A *and* B, so declining A was
>    an arbitrated choice and never ignorance.

Nothing here reads a company, a label's words, an enum position, a
vocabulary size, a recency or a score, and reversing the observation order
cannot change a ruling. In particular, **what today's extractor would
choose is never evidence**: a stored observation must exist that made the
assignment, was asked both questions, and read the deciding evidence. A
parser improvement supersedes nothing by itself.

## What it does not do

It changes no stored byte. The superseded reading keeps its figure, its
provenance, its stamps and every other fact — its net income and net
interest income continue to vote untouched, because the withdrawal is one
concept of one observation, exactly as BQ20's is. The journal keeps telling
the historical truth: *under the contract of its day, this reading was
right to call the row total revenue.* What changed is only which question
that answer is allowed to settle today.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.financial_statements import (
    FinancialStatementObservation,
    StatementConcept,
)
from app.domain.financing_cost_refusal import GOVERNED, refusal_for
from app.domain.tabular_evidence import ReportedFigure


class AssignmentStanding(StrEnum):
    """Whether one positive assignment still votes, and why."""

    #: No semantically qualified reading assigns this fact elsewhere.
    ACTIVE = "active"

    #: A native reading, asked about both concepts, assigned the same
    #: printed fact to a mutually exclusive concept on the statement's
    #: own evidence. The figure stays historical; the assignment stops
    #: voting.
    SUPERSEDED = "assignment superseded by a semantically qualified reading"


@dataclass(frozen=True, slots=True)
class AssignmentRuling:
    """One positive assignment, and what the record says about its authority."""

    concept: StatementConcept
    position: int

    standing: AssignmentStanding
    because: str

    @property
    def votes(self) -> bool:
        return self.standing is not AssignmentStanding.SUPERSEDED


def same_reported_fact(first: ReportedFigure, second: ReportedFigure) -> bool:
    """Whether two anchors report the same printed fact of the same statement.

    Five conjuncts, and figure equality alone is deliberately not among
    the sufficient ones: two unrelated rows can print the same number, so
    the value is required *and* never decisive. The cell fixes the address
    (one table is one scale, one column is one period, one row is one
    line); the label fixes what the filer calls the row, so a parse whose
    rows drifted cannot alias two lines through a shared address; the
    printed text and value fix the content; and the column header fixes
    the period in the filer's own words.

    All five are read from checked anchors — figures this platform read
    back out of the document at observation time — which is what makes the
    identity durable rather than a claim about today's parse.
    """

    return (
        first.cell == second.cell
        and first.label.strip() == second.label.strip()
        and first.printed.strip() == second.printed.strip()
        and first.value == second.value
        and first.column_header.strip() == second.column_header.strip()
    )


def rule_assignments(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[AssignmentRuling, ...]:
    """Every positive assignment for this concept, ruled against the set.

    Deterministic and total: one ruling per observation that located a
    figure for the concept, in stored order, whatever the outcome. A
    concept with no semantic qualification rule returns no rulings at
    all — nothing could ever supersede its positives, and saying so per
    observation would imply the question had been asked.
    """

    if concept not in GOVERNED:
        return ()

    return tuple(
        _rule_one(concept, fact.anchor, position, observations)
        for position, observation in enumerate(observations)
        if (fact := observation.fact(concept)) is not None and fact.anchor is not None
    )


def assignment_voting(
    concept: StatementConcept,
    observations: tuple[FinancialStatementObservation, ...],
) -> tuple[FinancialStatementObservation, ...]:
    """The observations whose positive for this concept still counts."""

    withdrawn = {
        ruling.position
        for ruling in rule_assignments(concept, observations)
        if not ruling.votes
    }

    return tuple(
        observation
        for position, observation in enumerate(observations)
        if position not in withdrawn
    )


# ── one assignment ──────────────────────────────────────────────────


def _rule_one(
    concept: StatementConcept,
    anchor: ReportedFigure,
    position: int,
    observations: tuple[FinancialStatementObservation, ...],
) -> AssignmentRuling:
    """Whether any observation in the set supersedes this assignment."""

    for other in observations:
        because = _superseding(concept, anchor, other)

        if because is not None:
            return AssignmentRuling(
                concept=concept,
                position=position,
                standing=AssignmentStanding.SUPERSEDED,
                because=because,
            )

    return AssignmentRuling(
        concept=concept,
        position=position,
        standing=AssignmentStanding.ACTIVE,
        because=(
            "no semantically qualified reading assigns this fact to another concept"
        ),
    )


def _superseding(
    concept: StatementConcept,
    anchor: ReportedFigure,
    other: FinancialStatementObservation,
) -> str | None:
    """The worded proof that `other` supersedes this assignment, or None.

    Every one of the six obligations is checked here, and a single miss
    keeps the assignment voting: unknown remains unknown, exactly as it
    does for a contract that cannot be bounded.
    """

    marker_concept, requirement = GOVERNED[concept]

    for candidate, (candidate_marker, candidate_requirement) in GOVERNED.items():
        # 3–4. Both concepts governed, one marker, opposite requirements —
        # mutually exclusive by construction, never by name.
        if candidate is concept:
            continue

        if candidate_marker is not marker_concept:
            continue

        if candidate_requirement is requirement:
            continue

        # 2. The other observation assigns a figure to the candidate…
        assigned = other.fact(candidate)

        if assigned is None or assigned.anchor is None:
            continue

        # 1. …and it is the same physical fact, by the five-part identity.
        if not same_reported_fact(anchor, assigned.anchor):
            continue

        # 6. Native to both questions: stamped for the concept it declined
        # as well as the one it chose, so the choice was arbitrated.
        if other.produced_contract_for(concept) is None:
            continue

        if other.produced_contract_for(candidate) is None:
            continue

        # 5. The deciding evidence, read by the same observation from the
        # same statement — and judged by the same rule every consensus
        # runs, so this module cannot drift from BQ23's semantics.
        marker = other.fact(marker_concept)

        if marker is None or marker.anchor is None:
            continue

        established = {marker_concept: marker.anchor}

        if refusal_for(concept, assigned.anchor, assigned.row, established) is None:
            # The structure does not refute the old concept here.
            continue

        if (
            refusal_for(candidate, assigned.anchor, assigned.row, established)
            is not None
        ):
            # Nor does it support the new one.
            continue

        return (
            f"A later reading of the same statement, asked about both "
            f"{concept.value} and {candidate.value}, assigned the same "
            f'printed fact — "{anchor.label}" {anchor.printed} at '
            f'{anchor.cell.stated()}, under "{anchor.column_header}" — to '
            f"{candidate.value}, and the statement itself carries the "
            f'deciding evidence: "{marker.anchor.label}" '
            f"{marker.anchor.printed} at {marker.anchor.cell.stated()} "
            f"precedes it in the same column, which {candidate.value} "
            f"requires and {concept.value} excludes. The reading and its "
            f"figure remain stored; what is withdrawn is only its "
            f"authority to answer {concept.value}."
        )

    return None
