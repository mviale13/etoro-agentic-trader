"""When one printed cell answers two concepts' vocabularies, and only one of them.

BQ25. Goldman and JPMorgan print a row whose label is in both
`TOTAL_REVENUE`'s vocabulary and `REVENUE_NET_OF_INTEREST_EXPENSE`'s. The
extractor resolved that collision by *enum order* — the first concept to
reach the cell claimed it, and the second raised, rejecting the whole
observation and losing every other concept the reading had found.

Enum order is not evidence. These two concepts carry mutually exclusive
structural predicates, so the statement itself says which one owns the row,
and this file pins that it does — and pins just as hard that arbitration
never becomes a guess where the evidence is silent.
"""

from __future__ import annotations

import asyncio
import json
from datetime import date

import pytest

from app.domain.financial_statements import (
    StatementConcept,
    StatementKind,
    concept_vocabulary_fingerprint,
    matches_concept,
)
from app.domain.financing_cost_refusal import Requirement, survivors_for
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    SourceAuthority,
    SourceDocument,
    SourceType,
)
from app.domain.tabular_evidence import (
    CellReference,
    ReportedFigure,
    SourceTable,
    TableRow,
)
from app.providers.narrative_provider import Draft, DraftRequest
from app.services.company_knowledge_extractor import ExtractionRejected
from app.services.financial_statement_extractor import FinancialStatementExtractor

INCOME = StatementKind.INCOME_STATEMENT
REVENUE = StatementConcept.TOTAL_REVENUE
NET_OF_INTEREST = StatementConcept.REVENUE_NET_OF_INTEREST_EXPENSE
NII = StatementConcept.NET_INTEREST_INCOME
EARNINGS = StatementConcept.NET_INCOME

#: Goldman's shape, and the figures are its own: the non-interest subtotal,
#: the net interest subtotal immediately above the total, and the total the
#: two reconcile to exactly.
GOLDMAN = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total non-interest revenues", "44,724", "45,456")),
        TableRow(cells=("Net interest income", "13,559", "8,056")),
        TableRow(cells=("Total net revenues", "58,283", "53,512")),
        TableRow(cells=("Net earnings", "17,176", "14,276")),
    ),
)

#: JPMorgan's, on the same terms.
JPMORGAN = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Noninterest revenue", "87,004", "84,973")),
        TableRow(cells=("Net interest income", "95,443", "92,583")),
        TableRow(cells=("Total net revenue", "182,447", "177,556")),
        TableRow(cells=("Net income", "57,048", "58,471")),
    ),
)

#: The industrial control: the identical shared label with **no** net
#: interest income anywhere on the statement. Interest expense below the
#: top line, which is the ordinary shape.
INDUSTRIAL = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total net revenues", "58,283", "53,512")),
        TableRow(cells=("Interest expense", "1,200", "1,100")),
        TableRow(cells=("Net income", "17,176", "14,276")),
    ),
)

#: The paired control: the same two rows, marker **below** the candidate.
MARKER_BELOW = SourceTable(
    index=0,
    caption="(in millions)",
    rows=(
        TableRow(cells=("", "2025", "2024")),
        TableRow(cells=("Total net revenues", "58,283", "53,512")),
        TableRow(cells=("Net interest income", "13,559", "8,056")),
        TableRow(cells=("Net income", "17,176", "14,276")),
    ),
)


def document(tables: tuple[SourceTable, ...]) -> SourceDocument:
    return SourceDocument(
        source=PrimarySource(
            symbol="EXA",
            company="Example",
            source_type=SourceType.ANNUAL_REPORT,
            identifier="10-K 0000019617-26-000100",
            key="0000019617-26-000100",
            published_on=date(2026, 2, 13),
            reporting_period=None,
            document_format="html",
            language="en",
            location="https://www.sec.gov/Archives/example",
            provider="SEC EDGAR",
            authority=SourceAuthority.REGULATOR_FILED,
            verification=(IdentityCheck.REGISTER_INDEXED,),
        ),
        business_description="",
        income_statement_text="Consolidated statements of income",
        income_statement_tables=tables,
    )


class StubProvider:
    name = "Stub"
    model = "stub-1"

    def __init__(self, payload: object) -> None:
        self._payload = payload

    async def draft(self, request: DraftRequest) -> Draft:
        return Draft(text=json.dumps(self._payload), model=self.model, usage=None)


def cite(concept: str, row: int, value: float) -> dict[str, object]:
    return {"concept": concept, "table": 0, "row": row, "column": 1, "value": value}


def extract(payload: object, table: SourceTable):
    return asyncio.run(
        FinancialStatementExtractor(StubProvider(payload)).extract(
            "EXA", document((table,))
        )
    )


def figure(label: str, value: float, *, row: int, column: int = 1) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header="2025",
        printed=f"{value:,.0f}",
        value=value,
        cell=CellReference(table=0, row=row, column=column),
        caption="(in millions)",
    )


# ── 1. the failure this slice exists to repair ──────────────────────


def test_the_shared_label_is_genuinely_in_both_vocabularies() -> None:
    """The reproducer's premise, checked rather than asserted.

    Neither vocabulary is edited by this slice, so the collision is real
    and stays real. If this ever fails, the collision was removed
    somewhere else and the arbitration below is no longer load-bearing.
    """

    for label in ("Total net revenues", "Total net revenue"):
        assert matches_concept(REVENUE, label), label
        assert matches_concept(NET_OF_INTEREST, label), label

    # And the marker's vocabulary is shared with nothing.
    assert matches_concept(NII, "Net interest income")
    assert not matches_concept(REVENUE, "Net interest income")
    assert not matches_concept(NET_OF_INTEREST, "Net interest income")


# ── 2–3. the rule for a contested cell ──────────────────────────────


def test_the_predicates_are_mutually_exclusive_under_one_relationship() -> None:
    """One marker, one relationship, opposite requirements."""

    marker, candidate = (
        figure("Net interest income", 13559.0, row=2),
        figure("Total net revenues", 58283.0, row=3),
    )

    assert survivors_for((REVENUE, NET_OF_INTEREST), candidate, {NII: marker}) == (
        NET_OF_INTEREST,
    )

    # The same two concepts, no marker at all.
    assert survivors_for((REVENUE, NET_OF_INTEREST), candidate, {}) == (REVENUE,)


def test_arbitration_refuses_where_a_candidate_carries_no_discriminator() -> None:
    """A concept with no predicate cannot be refuted, so nothing is decided.

    This is the guard against every shape §3 forbids. `GROSS_PROFIT` has no
    structural requirement, so pairing it with one that does leaves two
    survivors — and two survivors is ambiguity, never a winner.
    """

    candidate = figure("Total net revenues", 58283.0, row=3)
    marker = figure("Net interest income", 13559.0, row=2)

    contested = (StatementConcept.GROSS_PROFIT, NET_OF_INTEREST)

    assert set(survivors_for(contested, candidate, {NII: marker})) == set(contested)


def test_arbitration_can_leave_no_survivor() -> None:
    """Then the cell answers neither, which is a third outcome and not a tie."""

    candidate = figure("Total net revenues", 58283.0, row=3)

    # A marker above refutes `TOTAL_REVENUE`; asking only about it leaves
    # nothing standing.
    marker = figure("Net interest income", 13559.0, row=2)

    assert survivors_for((REVENUE,), candidate, {NII: marker}) == ()


def test_arbitration_reads_no_name_and_no_order() -> None:
    """The rule is the predicate, and reversing the input cannot move it."""

    marker = figure("Net interest income", 13559.0, row=2)
    candidate = figure("Total net revenues", 58283.0, row=3)

    forward = survivors_for((REVENUE, NET_OF_INTEREST), candidate, {NII: marker})
    backward = survivors_for((NET_OF_INTEREST, REVENUE), candidate, {NII: marker})

    assert forward == backward == (NET_OF_INTEREST,)


# ── 4–5. the mandatory controls, through the extractor ──────────────


def test_goldman_resolves_to_the_new_concept_and_keeps_everything_else() -> None:
    """The whole observation survives, and the shared row has one owner."""

    observation = extract(
        {
            "located": [
                cite("total_revenue", 3, 58283),
                cite("revenue_net_of_interest_expense", 3, 58283),
                cite("net_interest_income", 2, 13559),
                cite("net_income", 4, 17176),
            ]
        },
        GOLDMAN,
    )

    net_of_interest = observation.fact(NET_OF_INTEREST)

    assert net_of_interest is not None and net_of_interest.anchor is not None
    assert net_of_interest.anchor.label == "Total net revenues"
    assert net_of_interest.anchor.value == 58283.0

    # `TOTAL_REVENUE` did not take the cell, and says why.
    revenue = observation.fact(REVENUE)

    assert revenue is not None
    assert revenue.anchor is None
    assert revenue.unlocated_because is not None
    assert "net interest income" in revenue.unlocated_because
    assert "revenue_net_of_interest_expense" in revenue.unlocated_because

    # And nothing else was lost — the defect's real cost.
    for concept, value in ((NII, 13559.0), (EARNINGS, 17176.0)):
        fact = observation.fact(concept)

        assert fact is not None and fact.anchor is not None, concept
        assert fact.anchor.value == value


def test_jpmorgan_resolves_the_same_way() -> None:
    observation = extract(
        {
            "located": [
                cite("total_revenue", 3, 182447),
                cite("revenue_net_of_interest_expense", 3, 182447),
                cite("net_interest_income", 2, 95443),
                cite("net_income", 4, 57048),
            ]
        },
        JPMORGAN,
    )

    net_of_interest = observation.fact(NET_OF_INTEREST)

    assert net_of_interest is not None and net_of_interest.anchor is not None
    assert net_of_interest.anchor.value == 182447.0

    revenue = observation.fact(REVENUE)

    assert revenue is not None and revenue.anchor is None

    assert observation.fact(NII) is not None
    nii = observation.fact(NII)
    assert nii is not None and nii.anchor is not None and nii.anchor.value == 95443.0


def test_the_uncontested_reading_is_untouched() -> None:
    """American Express's shape: only one vocabulary matches, so no arbitration.

    The control that proves the new stage is inert where nothing is
    contested — which is every reading this platform has ever taken.
    """

    axp = SourceTable(
        index=0,
        caption="(in millions)",
        rows=(
            TableRow(cells=("", "2025", "2024")),
            TableRow(cells=("Net interest income", "17,364", "15,543")),
            TableRow(
                cells=("Total revenues net of interest expense", "72,229", "65,949")
            ),
            TableRow(cells=("Net income", "10,833", "10,129")),
        ),
    )

    observation = extract(
        {
            "located": [
                cite("revenue_net_of_interest_expense", 2, 72229),
                cite("net_interest_income", 1, 17364),
                cite("net_income", 3, 10833),
            ]
        },
        axp,
    )

    fact = observation.fact(NET_OF_INTEREST)

    assert fact is not None and fact.anchor is not None
    assert fact.anchor.value == 72229.0

    # `TOTAL_REVENUE` is simply not located: the reading never claimed it
    # and its label is not an accepted form.
    revenue = observation.fact(REVENUE)

    assert revenue is not None and revenue.anchor is None
    assert revenue.unlocated_because is not None
    assert "The reading located no cell" in revenue.unlocated_because


def test_the_industrial_control_keeps_total_revenue() -> None:
    """The same shared label, no marker, and the gross reading survives."""

    observation = extract(
        {
            "located": [
                cite("total_revenue", 1, 58283),
                cite("revenue_net_of_interest_expense", 1, 58283),
                cite("net_income", 3, 17176),
            ]
        },
        INDUSTRIAL,
    )

    revenue = observation.fact(REVENUE)

    assert revenue is not None and revenue.anchor is not None
    assert revenue.anchor.label == "Total net revenues"
    assert revenue.anchor.value == 58283.0

    net_of_interest = observation.fact(NET_OF_INTEREST)

    assert net_of_interest is not None and net_of_interest.anchor is None


def test_the_marker_below_control_does_not_reach_the_new_concept() -> None:
    """Order is the evidence: a marker beneath the total refutes nothing."""

    observation = extract(
        {
            "located": [
                cite("total_revenue", 1, 58283),
                cite("revenue_net_of_interest_expense", 1, 58283),
                cite("net_interest_income", 2, 13559),
                cite("net_income", 3, 17176),
            ]
        },
        MARKER_BELOW,
    )

    revenue = observation.fact(REVENUE)

    assert revenue is not None and revenue.anchor is not None
    assert revenue.anchor.value == 58283.0

    assert observation.fact(NET_OF_INTEREST) is not None
    net_of_interest = observation.fact(NET_OF_INTEREST)
    assert net_of_interest is not None and net_of_interest.anchor is None


def test_an_unresolved_collision_still_refuses_the_observation() -> None:
    """Two survivors is ambiguity, and ambiguity is never resolved by order.

    Constructed from a concept that carries no structural requirement, so
    nothing can refute it: `OPERATING_INCOME` and `TOTAL_REVENUE` both
    accept `total operating income`… they do not, so the collision is built
    at the extractor's own level instead — two concepts citing one cell
    where the platform holds no discriminator for either.
    """

    table = SourceTable(
        index=0,
        caption="(in millions)",
        rows=(
            TableRow(cells=("", "2025", "2024")),
            TableRow(cells=("Total revenues", "58,283", "53,512")),
            TableRow(cells=("Net income", "17,176", "14,276")),
        ),
    )

    with pytest.raises(ExtractionRejected) as rejected:
        extract(
            {
                "located": [
                    cite("total_revenue", 1, 58283),
                    cite("net_income", 1, 58283),
                ]
            },
            table,
        )

    # Rejected for the label, before arbitration is even reached: the
    # reading cited a revenue row as net income.
    assert "does not read as answering it" in str(rejected.value)


def test_two_surviving_candidates_reject_rather_than_choose(monkeypatch) -> None:
    """The arbitration's own refusal path, and it has to be constructed.

    No two concepts in the live vocabulary both accept one label *and*
    lack a discriminator — the only real overlap is the pair this slice
    exists for, and that pair always resolves. So the collision is built:
    `GROSS_PROFIT` is given the shared form for the length of this test.
    It declares no structural requirement, so nothing can refute it, and
    two survivors must refuse rather than let either win.

    Monkeypatched rather than mocked, so the extractor runs its real
    lexical, qualification and uniqueness stages over a real document.
    """

    from app.domain.financial_statements import CONCEPT_LABELS

    monkeypatch.setitem(
        CONCEPT_LABELS,
        StatementConcept.GROSS_PROFIT,
        (*CONCEPT_LABELS[StatementConcept.GROSS_PROFIT], "total net revenues"),
    )

    assert matches_concept(StatementConcept.GROSS_PROFIT, "Total net revenues")

    with pytest.raises(ExtractionRejected) as rejected:
        extract(
            {
                "located": [
                    cite("revenue_net_of_interest_expense", 3, 58283),
                    cite("gross_profit", 3, 58283),
                    cite("net_interest_income", 2, 13559),
                ]
            },
            GOLDMAN,
        )

    because = str(rejected.value)

    assert "cites a cell already read as" in because
    assert "holds no evidence that tells the two apart" in because
    assert "gross_profit" in because

    # And the mechanism, checked directly: the marker satisfies the new
    # concept and cannot refute a concept that demands nothing, so two
    # stand and neither may be preferred.
    marker = figure("Net interest income", 13559.0, row=2)
    candidate = figure("Total net revenues", 58283.0, row=3)

    assert set(
        survivors_for(
            (StatementConcept.GROSS_PROFIT, NET_OF_INTEREST), candidate, {NII: marker}
        )
    ) == {StatementConcept.GROSS_PROFIT, NET_OF_INTEREST}


def test_a_refuted_candidate_yields_to_the_one_left_standing(monkeypatch) -> None:
    """One survivor owns the cell even where it declares no requirement.

    The rule is *survives refutation*, not *has the better predicate*. A
    concept nothing can refute wins a contest whose only other candidate
    the statement refuted — which is the correct reading of the evidence
    and is worth pinning, because it looks like a weakness and is not.
    """

    from app.domain.financial_statements import CONCEPT_LABELS

    monkeypatch.setitem(
        CONCEPT_LABELS,
        StatementConcept.GROSS_PROFIT,
        (*CONCEPT_LABELS[StatementConcept.GROSS_PROFIT], "total net revenues"),
    )

    observation = extract(
        {
            "located": [
                cite("total_revenue", 3, 58283),
                cite("gross_profit", 3, 58283),
                cite("net_interest_income", 2, 13559),
            ]
        },
        GOLDMAN,
    )

    gross = observation.fact(StatementConcept.GROSS_PROFIT)

    assert gross is not None and gross.anchor is not None
    assert gross.anchor.value == 58283.0

    revenue = observation.fact(REVENUE)

    assert revenue is not None and revenue.anchor is None


# ── 6–7. the invariants that must not move ──────────────────────────


def test_one_cell_still_establishes_at_most_one_concept() -> None:
    """Arbitration decides the owner; it never licenses two owners."""

    observation = extract(
        {
            "located": [
                cite("total_revenue", 3, 58283),
                cite("revenue_net_of_interest_expense", 3, 58283),
                cite("net_interest_income", 2, 13559),
                cite("net_income", 4, 17176),
            ]
        },
        GOLDMAN,
    )

    cells = [fact.anchor.cell for fact in observation.facts if fact.anchor is not None]

    assert len(cells) == len(set(cells))


def test_neither_vocabulary_moved() -> None:
    """Arbitration is a resolution stage, not a contract change."""

    assert concept_vocabulary_fingerprint(REVENUE) == "ea9df9c5adbc7f44"
    assert concept_vocabulary_fingerprint(NET_OF_INTEREST) == "3e077c247f109a37"

    from app.repositories.financial_statement_store import STATEMENT_SCHEMA_VERSION

    assert STATEMENT_SCHEMA_VERSION == 3


def test_the_governing_requirements_are_unchanged() -> None:
    from app.domain.financing_cost_refusal import GOVERNED

    assert GOVERNED[REVENUE] == (NII, Requirement.ABSENT_ABOVE)
    assert GOVERNED[NET_OF_INTEREST] == (NII, Requirement.PRESENT_ABOVE)
