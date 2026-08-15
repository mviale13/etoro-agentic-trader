"""The inventory document is a view of the registry, not a second copy.

The audit's own finding about `market_snapshot_archive` — one
translation, two owners, and a fix to either misses the other —
applies to documentation as much as to code. So the inventory is
generated, and this test is what stops the generated copy from being
edited into a divergent second source of truth.
"""

from __future__ import annotations

from pathlib import Path

from app.commands.translations import render_markdown
from app.domain.provider_translation import (
    DecisionRelevance,
    TranslationWarrant,
)
from app.domain.provider_translations import (
    TRANSLATIONS,
    awaiting_warrant,
    counted,
)

DOCUMENT = Path(__file__).resolve().parents[1] / (
    "docs/architecture/PROVIDER_TRANSLATION_INVENTORY.md"
)


class TestTheDocumentIsGenerated:
    def test_the_checked_in_document_matches_the_registry(self) -> None:
        """Editing the document by hand fails here, by design."""

        assert DOCUMENT.exists(), (
            "the generated inventory is missing; run "
            "`movrvest translations --markdown > "
            "docs/architecture/PROVIDER_TRANSLATION_INVENTORY.md`"
        )

        assert DOCUMENT.read_text() == render_markdown() + "\n", (
            "the inventory document has drifted from the registry; "
            "regenerate it rather than editing it"
        )

    def test_the_document_names_its_own_generator(self) -> None:
        assert "movrvest translations --markdown" in DOCUMENT.read_text()


class TestTheRegistryIsHonest:
    def test_the_census_is_computed_rather_than_quoted(self) -> None:
        census = counted()

        assert sum(census.values()) == len(TRANSLATIONS)

    def test_almost_nothing_on_this_path_is_warranted(self) -> None:
        """The audit's finding, asserted so a silent upgrade is caught.

        Not a target. If a later slice earns a warrant it changes this
        number deliberately — what it cannot do is drift upward while
        nobody is looking, which is how an assumption becomes a fact.
        """

        established = [item for item in TRANSLATIONS if item.establishes_domain_fact]

        assert len(established) == 1
        assert established[0].warrant is TranslationWarrant.VERIFIED

    def test_every_translation_is_uniquely_keyed(self) -> None:
        keys = [item.key for item in TRANSLATIONS]

        assert len(keys) == len(set(keys))

    def test_the_ranked_list_leads_with_what_gates_a_decision(self) -> None:
        ranked = awaiting_warrant()

        gating = [
            position
            for position, item in enumerate(ranked)
            if item.decision_relevance is DecisionRelevance.GATES_A_DECISION
        ]

        others = [
            position
            for position, item in enumerate(ranked)
            if item.decision_relevance is not DecisionRelevance.GATES_A_DECISION
        ]

        assert gating and others
        assert max(gating) < min(others)

    def test_the_ranking_does_not_depend_on_registry_order(self) -> None:
        """A tie broken by file order would rank by typing, not by reach."""

        ranked = awaiting_warrant()

        assert [item.repair_rank for item in ranked] == sorted(
            item.repair_rank for item in ranked
        )

    def test_a_warrant_is_not_orderable(self) -> None:
        """No comparison operator — a warrant is not a quantity.

        `StrEnum` inherits string ordering, so the members *can* be
        compared as text; what must never exist is a domain ordering
        that means "more warranted". This asserts the alphabetical
        accident is not one.
        """

        alphabetical = sorted(warrant.value for warrant in TranslationWarrant)

        assert alphabetical != [
            TranslationWarrant.VERIFIED.value,
            TranslationWarrant.VALIDATED.value,
            TranslationWarrant.DECLARED.value,
            TranslationWarrant.ASSUMED.value,
            TranslationWarrant.UNKNOWN.value,
        ]
