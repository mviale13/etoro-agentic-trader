"""The strongest absence claim the provenance actually supports.

BQ4. Two wording defects, repaired and pinned:

- `CONCEPT_WORDS` had no entry for `TOTAL_REVENUE` or `NET_INCOME`, so
  their `NOT_PRINTED` could never be downgraded — and the platform
  asserted that Coca-Cola prints no revenue line while its own reading
  had located a figure three rows below `Net Operating Revenues`.
- *"5 of 5 observations"* read as five independent corroborating
  sightings. Measured, they are five readings of one document by one
  model inside forty seconds.

The invariant under test: **a failure to locate a concept is not
evidence that the filer does not print it**, and **repeated readings
are repeated readings**.
"""

from __future__ import annotations

import pytest

from app.domain.financial_statements import (
    CONCEPT_LABELS,
    StatementConcept,
    matches_concept,
)
from app.domain.statement_shape import CONCEPT_WORDS

#: The two concepts BQ3 measured as unweakenable, now covered.
REPAIRED = (StatementConcept.TOTAL_REVENUE, StatementConcept.NET_INCOME)


class TestTheDowngradeIsReachable:
    """Both repaired concepts can now leave `NOT_PRINTED` at all."""

    @pytest.mark.parametrize("concept", REPAIRED)
    def test_the_concept_has_downgrade_vocabulary(
        self, concept: StatementConcept
    ) -> None:
        assert CONCEPT_WORDS.get(concept), (
            f"{concept.value} has no downgrade words, so a label this "
            "platform fails to read is reported as the filer's absence"
        )

    def test_a_revenue_label_outside_the_accepted_forms_downgrades(self) -> None:
        """A revenue-like label this platform still does not accept.

        M&T's shape. (Coca-Cola's `Net Operating Revenues` played this
        part until BQ11 earned it, and Union Pacific's `Total operating
        revenues` until BQ19 did; the property under test is unchanged,
        so it needs a specimen that is still outside the vocabulary.)
        """

        assert not matches_concept(
            StatementConcept.TOTAL_REVENUE, "Mortgage banking revenues"
        )

        assert any(
            word in "mortgage banking revenues"
            for word in CONCEPT_WORDS[StatementConcept.TOTAL_REVENUE]
        )

    @pytest.mark.parametrize(
        "label",
        ["Operating revenues:", "Revenues", "Total revenues, net of interest expense"],
    )
    def test_the_measured_revenue_labels_all_downgrade(self, label: str) -> None:
        """UNP, AXP and Citigroup's own printed labels."""

        assert any(
            word in label.casefold()
            for word in CONCEPT_WORDS[StatementConcept.TOTAL_REVENUE]
        )

    @pytest.mark.parametrize(
        "label",
        ["Consolidated Net Income", "Profit after tax", "Consolidated net income"],
    )
    def test_the_measured_bottom_line_labels_all_downgrade(self, label: str) -> None:
        """KO, BCS and WMT — the `NET_INCOME` path is reachable."""

        assert any(
            word in label.casefold()
            for word in CONCEPT_WORDS[StatementConcept.NET_INCOME]
        )


class TestWordingIsNotEvidence:
    """The property the whole repair depends on.

    Downgrade vocabulary decides what may be *said* about an absence.
    It must never decide what counts as an established financial fact —
    those are `CONCEPT_LABELS`, matched by exact equality, and this
    slice does not touch them.
    """

    #: Labels measured in the live filings that carry a downgrade word
    #: and are **not** accepted forms. Each one is a real row from a
    #: real income statement (KO, UNP, AXP, C, BCS, WMT, MTB).
    CONTAINING_BUT_NOT_ACCEPTED = (
        (StatementConcept.TOTAL_REVENUE, "Operating revenues:"),
        (StatementConcept.TOTAL_REVENUE, "Total revenues, net of interest expense"),
        (StatementConcept.TOTAL_REVENUE, "Mortgage banking revenues"),
        (StatementConcept.NET_INCOME, "Consolidated Net Income"),
        (StatementConcept.NET_INCOME, "Profit after tax"),
        (StatementConcept.NET_INCOME, "Net income (loss) from equity method investees"),
    )

    @pytest.mark.parametrize(("concept", "label"), CONTAINING_BUT_NOT_ACCEPTED)
    def test_a_downgraded_label_is_still_not_established_evidence(
        self, concept: StatementConcept, label: str
    ) -> None:
        """The load-bearing guard of the whole slice.

        Every one of these labels now *weakens* an absence claim, and
        not one of them may become a figure this platform accepts. The
        two vocabularies do overlap — `revenue` is both a downgrade
        word and an accepted form — so the property under test is not
        disjointness but that **matching a word is not matching a
        label**.
        """

        assert any(word in label.casefold() for word in CONCEPT_WORDS[concept]), (
            "the label must reach the downgrade at all"
        )

        assert not matches_concept(concept, label), (
            f"{label!r} became established evidence for {concept.value}; "
            "wording vocabulary must never establish a financial fact"
        )

    @pytest.mark.parametrize("concept", REPAIRED)
    def test_the_accepted_forms_are_untouched(self, concept: StatementConcept) -> None:
        """`CONCEPT_LABELS` is out of scope and is not edited here.

        Pinned by content so that widening what counts as evidence —
        a funded change with its own ruling — cannot ride along with a
        wording repair.
        """

        pinned = {
            StatementConcept.TOTAL_REVENUE: (
                "total net revenue",
                "total net revenues",
                "total revenue",
                "total revenues",
                "net revenues",
                "net revenue",
                "revenues",
                "revenue",
                "net sales",
                "total net sales",
                "total sales and revenues",
                "total revenues and other income",
                # BQ11: earned by Coca-Cola's own arithmetic, one label.
                "net operating revenues",
                # BQ19: earned by Union Pacific's own arithmetic —
                # 23,220 + 1,290 = 24,510, an addition of two revenue
                # components with no expense deducted. One label again.
                "total operating revenues",
            ),
            StatementConcept.NET_INCOME: (
                "net income",
                "net income (loss)",
                "net earnings",
                "net earnings (loss)",
                "profit for the year",
                "profit for the period",
            ),
        }

        assert CONCEPT_LABELS[concept] == pinned[concept]


class TestSupportedAbsencesSurvive:
    """The repair may only weaken claims that were never supported."""

    def test_a_bank_statement_still_prints_no_gross_profit(self) -> None:
        """JPM and TRV's shape: no `gross` word anywhere, so the strong
        claim stays strong. The repair must not reach it."""

        assert "gross" in CONCEPT_WORDS[StatementConcept.GROSS_PROFIT]

        bank_labels = ("Total net revenue", "Net interest income", "Net income")

        assert not any(
            word in label.casefold()
            for label in bank_labels
            for word in CONCEPT_WORDS[StatementConcept.GROSS_PROFIT]
        )

    def test_the_bare_word_income_is_not_a_bottom_line_word(self) -> None:
        """The guard that keeps every interest and fee line out.

        `income` alone would downgrade `NET_INCOME` on any bank
        statement, weakening a finding on evidence that has nothing to
        do with the bottom line.
        """

        assert "income" not in CONCEPT_WORDS[StatementConcept.NET_INCOME]

        for label in ("Interest income", "Total interest income", "Other income"):
            assert not any(
                word in label.casefold()
                for word in CONCEPT_WORDS[StatementConcept.NET_INCOME]
            )


class TestTotalRevenueVocabulary:
    """What may establish `TOTAL_REVENUE`, and what may never (BQ11).

    The load-bearing distinction of this slice: `CONCEPT_WORDS` is
    deliberately broad, because its only power is to *weaken* an
    unsupported absence claim. `CONCEPT_LABELS` establishes a financial
    fact, so it must be narrow — a label that legitimately downgrades a
    `NOT_PRINTED` claim must not thereby become the company's top line.
    """

    #: Real corpus rows that are revenue-like and are **not** the
    #: company's consolidated top line. Every one of these carries a
    #: `CONCEPT_WORDS` revenue token, so each would weaken an absence
    #: claim — and none may establish the concept.
    COMPONENTS = (
        ("MTB", "Mortgage banking revenues"),
        ("FITB", "Wealth and asset management revenue"),
        ("FITB", "Commercial payments revenue"),
        ("FITB", "Consumer banking revenue"),
        ("AXP", "Discount revenue"),
        ("AXP", "Service fees and other revenue"),
        ("AXP", "Total non-interest revenues"),
        ("C", "Total non-interest revenues"),
        ("ALL", "Other revenue"),
        ("TRV", "Other revenues"),
        ("UNP", "Freight revenues"),
        ("TSLA", "Total automotive revenues"),
        ("TSLA", "Automotive sales"),
        ("HON", "Product sales"),
        ("HON", "Service sales"),
        ("MTB", "Other revenues from operations"),
    )

    def test_coca_colas_top_line_is_established(self) -> None:
        """The one label this slice adds."""

        assert matches_concept(StatementConcept.TOTAL_REVENUE, "Net Operating Revenues")

    @pytest.mark.parametrize(
        ("symbol", "label"), COMPONENTS, ids=[f"{sym}:{lab}" for sym, lab in COMPONENTS]
    )
    def test_a_component_never_becomes_total_revenue(
        self, symbol: str, label: str
    ) -> None:
        assert not matches_concept(StatementConcept.TOTAL_REVENUE, label), (
            f"{symbol}'s {label!r} is a component, segment or subtotal and "
            "must never establish the company's top line"
        )

    def test_the_two_vocabularies_are_broad_and_narrow_respectively(self) -> None:
        """The distinction, proved in both directions on real rows.

        A component carrying a revenue token reaches `CONCEPT_WORDS` —
        so a filing printing one may not be said to print no revenue
        line — while reaching `CONCEPT_LABELS` for none of them. Broad
        enough to refuse a false absence; narrow enough to refuse a
        false fact.
        """

        weakening = [
            label
            for _, label in self.COMPONENTS
            if any(
                word in label.casefold()
                for word in CONCEPT_WORDS[StatementConcept.TOTAL_REVENUE]
            )
        ]

        # The revenue-token components: every one weakens, none establishes.
        assert len(weakening) >= 10

        for label in weakening:
            assert not matches_concept(StatementConcept.TOTAL_REVENUE, label)

    def test_a_revenue_net_of_an_expense_is_not_the_top_line(self) -> None:
        """AXP and Citigroup print revenue *after* deducting interest.

        A different economic quantity from consolidated total revenue,
        and refused for that reason rather than for its wording.
        """

        for label in (
            "Total revenues net of interest expense",
            "Total revenues, net of interest expense",
        ):
            assert not matches_concept(StatementConcept.TOTAL_REVENUE, label)

    def test_every_operating_form_was_earned_one_filing_at_a_time(self) -> None:
        """No family, no pattern, no fuzzy rule — filing labels, one each.

        Two now, and the count is not the property: each was measured
        against one filer's own arithmetic and added alone. A rule that
        admitted an *operating revenue* family would also admit
        `Operating revenues:` — the heading Union Pacific prints above
        its components, which carries no figure and must never
        establish anything.
        """

        added = [
            label
            for label in CONCEPT_LABELS[StatementConcept.TOTAL_REVENUE]
            if "operating" in label
        ]

        assert added == ["net operating revenues", "total operating revenues"]

        assert not matches_concept(
            StatementConcept.TOTAL_REVENUE, "Operating revenues:"
        )
