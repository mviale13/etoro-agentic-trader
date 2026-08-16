"""A reading authorises the row; the parser reports what the row prints.

BQ7. The CTO ruling implemented: a deterministically parsed cell may
establish that *this document literally reports value V in row R under
period header P*, and may never establish that V is concept C. The
concept comes from the reading that anchored the row, and nothing here
re-decides it.

BQ6 measured why this matters: seven stored readings hold one cell
where the filing prints three, because the header-detection this
platform uses changed after those readings were taken. The values were
never missing from the document — only from the store.
"""

from __future__ import annotations

from app.domain.tabular_evidence import (
    CellReference,
    ReportedFigure,
    SourceTable,
    TableRow,
    historical_row,
)


def _table(
    rows: list[list[str]], index: int = 0, caption: str = "STATEMENTS"
) -> SourceTable:
    return SourceTable(
        index=index,
        caption=caption,
        rows=tuple(TableRow(cells=tuple(cells)) for cells in rows),
    )


REVENUE_ROW = [
    "Total revenues",
    "Total revenues",
    "Total revenues",
    "94,827",
    "97,690",
    "96,773",
]

#: TSLA's shape, as BQ6 measured it: a spanned title above the years.
TSLA = _table(
    [
        ["", "", "", "Year Ended December 31,", "", ""],
        ["", "", "", "2025", "2024", "2023"],
        ["Revenues", "Revenues", "Revenues", "", "", ""],
        REVENUE_ROW,
    ]
)


def _anchor(label: str, printed: str, value: float, row: int = 3) -> ReportedFigure:
    return ReportedFigure(
        label=label,
        column_header="Year Ended December 31,",
        printed=printed,
        value=value,
        cell=CellReference(table=0, row=row, column=3),
        caption="STATEMENTS",
    )


TSLA_ANCHOR = _anchor("Total revenues", "94,827", 94_827.0)


class TestTheAuthorisedRowExpands:
    def test_the_three_periods_are_recovered_with_their_headers(self) -> None:
        """The BQ6 specimen, pinned to the digit."""

        figures = historical_row(TSLA, TSLA_ANCHOR, 3)

        assert [(f.column_header, f.value) for f in figures] == [
            ("2025", 94_827.0),
            ("2024", 97_690.0),
            ("2023", 96_773.0),
        ]

    def test_every_recovered_cell_names_its_own_period(self) -> None:
        for figure in historical_row(TSLA, TSLA_ANCHOR, 3):
            assert figure.column_header.strip()
            assert figure.label == "Total revenues"

    def test_the_anchor_value_is_among_them(self) -> None:
        """The reading's own figure survives the expansion unchanged."""

        values = [f.value for f in historical_row(TSLA, TSLA_ANCHOR, 3)]

        assert TSLA_ANCHOR.value in values


class TestItRefusesRatherThanGuesses:
    """Every falsification case the brief demands. Each must return ()."""

    def test_a_moved_row_index_abstains(self) -> None:
        """HON's live shape: the stored index no longer names that row.

        The most important refusal in the slice — two of BQ6's nine
        instances behave exactly this way against today's parse.
        """

        assert historical_row(TSLA, TSLA_ANCHOR, 2) == ()

    def test_a_similar_but_unauthorised_row_abstains(self) -> None:
        """A tempting row the reading never authorised."""

        tempting = _anchor(
            "Total revenues, net of interest expense", "94,827", 94_827.0
        )

        assert historical_row(TSLA, tempting, 3) == ()

    def test_a_row_no_longer_carrying_the_anchor_figure_abstains(self) -> None:
        """Label matches by coincidence; the numbers say otherwise."""

        stale = _anchor("Total revenues", "81,462", 81_462.0)

        assert historical_row(TSLA, stale, 3) == ()

    def test_an_unheaded_column_contributes_no_cell(self) -> None:
        """A number whose period is unproven is not preserved."""

        unheaded = _table(
            [
                ["", "", "", "2025", "", "2023"],
                REVENUE_ROW,
            ]
        )

        figures = historical_row(unheaded, TSLA_ANCHOR, 1)

        assert [f.column_header for f in figures] == ["2025", "2023"]
        assert 97_690.0 not in [f.value for f in figures]

    def test_the_header_row_itself_is_never_expanded(self) -> None:
        assert historical_row(TSLA, TSLA_ANCHOR, 1) == ()
        assert historical_row(TSLA, TSLA_ANCHOR, 0) == ()

    def test_an_out_of_range_row_abstains(self) -> None:
        assert historical_row(TSLA, TSLA_ANCHOR, 99) == ()

    def test_no_table_is_crossed(self) -> None:
        """The function is given one table and cannot reach another.

        Structural rather than asserted: `historical_row` takes a single
        `SourceTable`, so crossing tables or documents is unexpressible
        at this boundary.
        """

        import inspect

        signature = inspect.signature(historical_row)

        assert list(signature.parameters) == ["table", "anchor", "row"]


class TestSemanticPromotionStaysElsewhere:
    def test_the_function_names_no_financial_concept(self) -> None:
        """The parser half may not decide meaning.

        `historical_row` takes no concept, returns no concept, and its
        source mentions none — the reading that produced the anchor is
        the only thing that ever said what this row is.
        """

        import inspect

        source = inspect.getsource(historical_row)

        for forbidden in (
            "StatementConcept",
            "matches_concept",
            "CONCEPT_LABELS",
            "total_revenue",
            "net_income",
        ):
            assert forbidden not in source

    def test_recovered_cells_are_figures_not_facts(self) -> None:
        """What comes back is what the document prints, nothing more."""

        for figure in historical_row(TSLA, TSLA_ANCHOR, 3):
            assert isinstance(figure, ReportedFigure)
            assert not hasattr(figure, "concept")
