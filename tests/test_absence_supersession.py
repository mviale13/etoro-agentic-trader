"""An absence stops voting only where a contract, not a clock, explains it.

The seven controls the BQ20 brief names, plus the two live specimens.
The one this file exists for is the last: a difference in vocabulary
fingerprints is not evidence of anything on its own, and a rule that
treated it as evidence would quietly become *newer wins*.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

from app.domain.absence_supersession import (
    AbsenceStanding,
    rule_absences,
    voting,
)
from app.domain.financial_statement_consensus import statement_consensus_of
from app.domain.financial_statements import (
    ConceptContract,
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import CellReference, ReportedFigure
from app.repositories.financial_statement_store import JsonFinancialStatementStore
from tests.test_financial_statement_store import source

INCOME = StatementKind.INCOME_STATEMENT
REVENUE = StatementConcept.TOTAL_REVENUE
EARNINGS = StatementConcept.NET_INCOME

#: The published lineage, by fingerprint.
BEFORE_BQ11 = "ba55a427097938f3"
BEFORE_BQ19 = "3cdbddd6a1fcf0e6"
TODAY = "ea9df9c5adbc7f44"

#: A form only today's contract accepts, and one every contract accepts.
NEW_FORM = "Total operating revenues"
OLD_FORM = "Total revenues"


def figure(label: str, printed: str = "24,510", value: float = 24510.0):
    return ReportedFigure(
        label=label,
        column_header="2025",
        printed=printed,
        value=value,
        cell=CellReference(table=0, row=4, column=1),
        caption="(in millions)",
    )


def reading(
    *,
    revenue: str | None,
    stamped: str | None,
    printed: str = "24,510",
    value: float = 24510.0,
    earnings: str | None = None,
) -> FinancialStatementObservation:
    """One reading: a located revenue label or an absence, plus a stamp."""

    anchor = figure(revenue, printed, value) if revenue else None

    facts = [
        StatementFact(
            concept=REVENUE,
            anchor=anchor,
            row=(anchor,) if anchor else (),
            unlocated_because=None if anchor else "The reading located no cell.",
        )
    ]

    if earnings is not None:
        bottom = figure(earnings, "7,138", 7138.0)
        facts.append(StatementFact(concept=EARNINGS, anchor=bottom, row=(bottom,)))

    produced = ()
    if stamped is not None:
        produced = (ConceptContract(concept=REVENUE, fingerprint=stamped),)

    return FinancialStatementObservation(
        symbol="UNP",
        statement=INCOME,
        facts=tuple(facts),
        source=source(),
        reading=Provenance(
            source="reader", observed_at=datetime(2026, 8, 17, tzinfo=UTC)
        ),
        produced_under=produced,
    )


def standings(observations) -> list[AbsenceStanding]:
    return [ruling.standing for ruling in rule_absences(REVENUE, observations)]


# ── control 1: the UNP shape ────────────────────────────────────────


def test_an_absence_a_later_vocabulary_explains_stops_voting() -> None:
    """The new form is one the older contract could not have accepted."""

    absences = tuple(reading(revenue=None, stamped=BEFORE_BQ19) for _ in range(5))
    located = tuple(reading(revenue=NEW_FORM, stamped=TODAY) for _ in range(5))

    assert standings(absences + located) == [AbsenceStanding.SUPERSEDED] * 5

    consensus = statement_consensus_of(absences + located)
    fact = consensus.fact(REVENUE)

    assert fact.withdrawn_absences == 5
    assert fact.anchor is not None
    assert fact.anchor.label == NEW_FORM


def test_the_live_unp_specimen_resolves() -> None:
    """The real five and five, now both sides in production.

    Until BQ20's recommended append the two halves lived in two stores
    and this control composed them. They are one store now, which is a
    stronger specimen and the same rule: five absences withdrawn, the
    located label settling the claim.
    """

    prod = JsonFinancialStatementStore("data/statements")
    held = prod.read("UNP", "0000100885-26-000037", INCOME)

    assert len(held) == 10

    consensus = statement_consensus_of(held)
    fact = consensus.fact(REVENUE)

    assert fact.withdrawn_absences == 5
    assert fact.anchor is not None
    assert fact.anchor.label == NEW_FORM
    assert fact.agreement.by_majority

    # Concept-locality, on the live specimen rather than a fixture: the
    # readings whose revenue absence was withdrawn keep every other
    # fact and go on voting with it.
    earnings = consensus.fact(EARNINGS)

    assert earnings.withdrawn_absences == 0
    assert earnings.agreement.answers[0].given == 10


# ── control 2: KO, under the same generic rule ──────────────────────


def test_the_live_ko_specimen_is_ruled_by_the_same_rule() -> None:
    """No company exception — and KO's absences survive it.

    KO's *positive* readings predate native stamping too, so both sides
    fall in the same unstamped candidate set — and one of those
    contracts (BQ11's) accepts `Net Operating Revenues`. The absence
    could have been produced by a contract that would have found the
    label, so nothing about the vocabulary explains it.
    """

    prod = JsonFinancialStatementStore("data/statements")
    held = prod.read("KO", "0001628280-26-010047", INCOME)

    assert len(held) == 10

    fact = statement_consensus_of(held).fact(REVENUE)

    assert fact.withdrawn_absences == 0
    assert fact.anchor is None
    assert not fact.agreement.by_majority


# ── control 3: two positives are a disagreement ─────────────────────


def test_two_different_positive_readings_both_keep_voting() -> None:
    """Conflicting evidence stays conflicting, whatever produced it."""

    old = tuple(
        reading(revenue=OLD_FORM, printed="24,510", value=24510.0, stamped=BEFORE_BQ19)
        for _ in range(5)
    )
    new = tuple(
        reading(revenue=NEW_FORM, printed="99,999", value=99999.0, stamped=TODAY)
        for _ in range(5)
    )

    assert standings(old + new) == [], "no absence to rule on"
    assert len(voting(REVENUE, old + new)) == 10

    fact = statement_consensus_of(old + new).fact(REVENUE)

    assert fact.withdrawn_absences == 0
    assert fact.anchor is None, "a five-five split of positives settles nothing"


# ── control 4: the vocabulary did not move ──────────────────────────


def test_an_absence_keeps_voting_when_the_located_form_was_always_accepted() -> None:
    absences = tuple(reading(revenue=None, stamped=BEFORE_BQ19) for _ in range(5))
    located = tuple(reading(revenue=OLD_FORM, stamped=TODAY) for _ in range(5))

    assert standings(absences + located) == [AbsenceStanding.ACTIVE] * 5
    assert statement_consensus_of(absences + located).fact(REVENUE).anchor is None


# ── control 5: the producing contract cannot be bounded ─────────────


def test_an_absence_from_an_unknown_contract_keeps_voting() -> None:
    """A fingerprint no published vocabulary matches proves nothing."""

    absences = tuple(
        reading(revenue=None, stamped="ffffffffffffffff") for _ in range(5)
    )
    located = tuple(reading(revenue=NEW_FORM, stamped=TODAY) for _ in range(5))

    assert standings(absences + located) == [AbsenceStanding.UNPROVABLE] * 5
    assert statement_consensus_of(absences + located).fact(REVENUE).anchor is None


def test_an_unstamped_absence_is_bounded_but_not_assumed() -> None:
    """Silence bounds the candidates; it does not license a withdrawal.

    An unstamped reading cannot have come from a contract that stamps,
    so the candidates are the era's earlier vocabularies — and the
    absence is withdrawn only where *every* one of them lacks the form.
    Against a form they all accept, the same unstamped absence stands.
    """

    unstamped = tuple(reading(revenue=None, stamped=None) for _ in range(5))

    against_new = unstamped + tuple(
        reading(revenue=NEW_FORM, stamped=TODAY) for _ in range(5)
    )
    against_old = unstamped + tuple(
        reading(revenue=OLD_FORM, stamped=TODAY) for _ in range(5)
    )

    assert standings(against_new) == [AbsenceStanding.SUPERSEDED] * 5
    assert standings(against_old) == [AbsenceStanding.ACTIVE] * 5


# ── control 6: another concept's vocabulary ─────────────────────────


def test_a_widening_of_another_concept_touches_nothing() -> None:
    """Concept-local: an absence is ruled against its own vocabulary."""

    absences = tuple(reading(revenue=None, stamped=BEFORE_BQ19) for _ in range(5))
    located = tuple(reading(revenue=OLD_FORM, stamped=TODAY) for _ in range(5))

    # `net_income`'s vocabulary has never moved, so nothing about it is
    # published and nothing about it can be ruled.
    assert rule_absences(EARNINGS, absences + located) == ()
    assert standings(absences + located) == [AbsenceStanding.ACTIVE] * 5


# ── control 7: a fingerprint difference is not evidence ─────────────


def test_a_different_fingerprint_alone_never_supersedes() -> None:
    """The load-bearing control.

    Two contracts differ, the newer one located the figure, and the
    older one could have accepted that very label. Nothing about the
    vocabulary explains the absence, so it keeps its vote — and a rule
    that fired here would be *newer wins* wearing a contract's clothes.
    """

    absences = tuple(reading(revenue=None, stamped=BEFORE_BQ11) for _ in range(5))
    located = tuple(reading(revenue=OLD_FORM, stamped=TODAY) for _ in range(5))

    assert BEFORE_BQ11 != TODAY

    assert standings(absences + located) == [AbsenceStanding.ACTIVE] * 5
    assert (
        statement_consensus_of(absences + located).fact(REVENUE).withdrawn_absences == 0
    )


# ── concept-locality and immutability ───────────────────────────────


def test_only_the_stale_concept_loses_its_vote() -> None:
    """A withdrawn revenue absence does not cost the reading its earnings."""

    absences = tuple(
        reading(revenue=None, stamped=BEFORE_BQ19, earnings="Net income")
        for _ in range(5)
    )
    located = tuple(reading(revenue=NEW_FORM, stamped=TODAY) for _ in range(5))

    consensus = statement_consensus_of(absences + located)

    assert consensus.fact(REVENUE).withdrawn_absences == 5

    earnings = consensus.fact(EARNINGS)

    assert earnings is not None
    assert earnings.anchor is not None, "the same readings still carry net income"
    assert earnings.agreement.agreeing == 5


def test_supersession_rewrites_no_observation() -> None:
    """The rule is derived; the records it reads are untouched."""

    absences = tuple(reading(revenue=None, stamped=BEFORE_BQ19) for _ in range(5))
    located = tuple(reading(revenue=NEW_FORM, stamped=TODAY) for _ in range(5))

    before = dataclasses.astuple(absences[0])

    statement_consensus_of(absences + located)

    assert dataclasses.astuple(absences[0]) == before
    assert absences[0].fact(REVENUE).anchor is None
    assert absences[0].superseded_because is None
    assert absences[0].produced_contract_for(REVENUE) == BEFORE_BQ19
