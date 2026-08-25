"""The Overview's brief composes and never authors.

Every assertion here is about *whose words* reach the investor. The
layer is allowed headings, an order and one connective; a test that only
checked the shape would pass while the brief quietly restated a
committee's finding in its own vocabulary.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.models.crypto_brief_adapter import (
    BLOCK_LIMIT,
    LOWERCASEABLE,
    SETUP_LIMIT,
    BriefLine,
    brief_for,
)
from app.cio.digital_asset_decision import (
    DecisionState,
    DigitalAssetDecision,
    UnresolvedQuestion,
)
from app.domain.crypto_intelligence import (
    CryptoIntelligenceSnapshot,
    Direction,
    Driver,
    DriverSupport,
    WatchItem,
)


def _driver(
    stated: str,
    direction: Direction = Direction.SUPPORTIVE,
    matters: str | None = None,
) -> Driver:
    return Driver(
        stated=stated,
        direction=direction,
        support=DriverSupport.OBSERVED,
        claims=("ref",),
        matters_because=matters,
    )


def _snapshot(
    symbol: str = "HYPE",
    drivers: tuple[Driver, ...] = (),
    watch: tuple[WatchItem, ...] = (),
) -> CryptoIntelligenceSnapshot:
    return CryptoIntelligenceSnapshot(
        symbol=symbol,
        as_of=datetime(2026, 8, 25, tzinfo=UTC),
        drivers=drivers,
        watch_next=watch,
    )


def _decision(
    unresolved: tuple[UnresolvedQuestion, ...] = (),
    uncertainties: tuple[str, ...] = (),
) -> DigitalAssetDecision:
    return DigitalAssetDecision(
        symbol="HYPE",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established.",
        unresolved=unresolved,
        material_uncertainties=uncertainties,
    )


class TestQuoting:
    def test_a_driver_is_quoted_whole_and_never_split_on_its_category(self) -> None:
        """A driver's colon is a category, not a claim boundary.

        The live corpus produced ``Token economics: Hyperliquid Reports
        Strong Revenue, Supply Burn, and Ecosystem Expansion``. Splitting
        it left the brief asserting "Token economics" as a finding, and
        TAO rendered that non-sentence twice in one block.
        """

        stated = (
            "Token economics: Hyperliquid Reports Strong Revenue, "
            "Supply Burn, and Ecosystem Expansion"
        )

        brief = brief_for(_decision(), _snapshot(drivers=(_driver(stated),)))

        assert brief.current_view[0].stated == stated

    def test_a_decision_sentence_keeps_its_claim_and_carries_the_rest(self) -> None:
        question = UnresolvedQuestion(
            owner="Supply Governance Committee",
            stated=(
                "No mechanical issuance rule is held for this asset. That is "
                "a statement about what this platform has read, not about "
                "what the protocol does."
            ),
        )

        brief = brief_for(_decision(unresolved=(question,)), _snapshot())
        line = brief.blocks_progress[0]

        assert line.stated == "No mechanical issuance rule is held for this asset"
        assert line.qualification is not None
        assert line.qualification.startswith("That is a statement")
        assert line.owner == "Supply Governance Committee"

    def test_a_colon_cuts_only_before_a_continuation(self) -> None:
        """Lowercase after the colon is support; a capital is a title."""

        brief = brief_for(
            _decision(
                uncertainties=(
                    "Tokens in existence cannot be stated as a single figure: "
                    "available estimates run from 586.86 million to 955.31 "
                    "million, a spread of 39%.",
                    "Supply is unsettled: Hyperliquid Publishes Four Figures",
                )
            ),
            _snapshot(),
        )

        cut, kept = brief.blocks_progress[0], brief.blocks_progress[1]

        assert cut.stated == "Tokens in existence cannot be stated as a single figure"
        assert kept.stated == "Supply is unsettled: Hyperliquid Publishes Four Figures"
        assert kept.qualification is None


class TestSetup:
    def test_it_joins_two_sides_with_one_connective(self) -> None:
        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(
                        owner="Supply Governance Committee",
                        stated="No mechanical issuance rule is held for this asset.",
                    ),
                )
            ),
            _snapshot(
                drivers=(_driver("Economic activity is reaching the token itself."),)
            ),
        )

        assert brief.setup == (
            "Economic activity is reaching the token itself, but no "
            "mechanical issuance rule is held for this asset."
        )
        assert brief.setup_absent is None

    def test_an_unlowerable_opener_degrades_to_two_intact_sentences(self) -> None:
        """Never a mangled sentence — ``Committee`` is not lowercased."""

        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(
                        owner="Value Capture Committee",
                        stated="Committee judgment is off, so no verdict was reached.",
                    ),
                )
            ),
            _snapshot(drivers=(_driver("The asset has moved +36% over a month."),)),
        )

        assert brief.setup == (
            "The asset has moved +36% over a month. "
            "Committee judgment is off, so no verdict was reached."
        )
        assert "but Committee" not in (brief.setup or "")

    def test_a_side_degrades_to_fewer_clauses_and_never_vanishes(self) -> None:
        """ETH lost all three supportive findings to this.

        The second supportive clause could not be lowered, and refusing
        the whole side left the setup opening on a blocker while the
        block below still listed what supported the case.
        """

        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(
                        owner="Supply Governance Committee",
                        stated="No mechanical issuance rule is held for this asset.",
                    ),
                )
            ),
            _snapshot(
                drivers=(
                    _driver("Fund flows have been a net source of demand."),
                    _driver("Hyperliquid reported record volume."),
                )
            ),
        )

        assert brief.setup is not None
        assert brief.setup.startswith("Fund flows have been a net source of demand")
        assert "Hyperliquid reported" not in brief.setup

    def test_it_quotes_one_clause_a_side_rather_than_run_long(self) -> None:
        long_driver = "The asset has moved " + ("very " * 20) + "far this month"
        long_block = "No economic role is established " + ("at all " * 15)

        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(owner="Committee", stated=long_block + "."),
                )
            ),
            _snapshot(drivers=(_driver(long_driver + "."), _driver("The fee held."))),
        )

        assert brief.setup is not None
        assert "The fee held" not in brief.setup

    def test_nothing_held_is_a_stated_absence_never_an_empty_string(self) -> None:
        brief = brief_for(_decision(), _snapshot())

        assert brief.setup is None
        assert brief.setup_absent is not None
        assert "not about the asset" in brief.setup_absent

    def test_the_limit_is_a_length_not_a_truncation(self) -> None:
        """A long sentence is quoted whole; only the clause count drops."""

        block = "No economic role is established for this asset, " + ("x" * SETUP_LIMIT)

        brief = brief_for(
            _decision(
                unresolved=(UnresolvedQuestion(owner="Committee", stated=block + "."),)
            ),
            _snapshot(),
        )

        assert brief.setup is not None
        assert brief.setup.endswith(".")
        assert "…" not in brief.setup
        assert block in brief.setup


class TestBlocks:
    def test_an_adverse_driver_is_a_block_and_never_the_current_view(self) -> None:
        brief = brief_for(
            _decision(),
            _snapshot(
                drivers=(
                    _driver("Fees are rising."),
                    _driver("A regulator opened a review.", Direction.ADVERSE),
                )
            ),
        )

        assert [line.stated for line in brief.current_view] == ["Fees are rising"]
        assert [line.stated for line in brief.blocks_progress] == [
            "A regulator opened a review"
        ]

    def test_open_questions_come_before_uncertainties(self) -> None:
        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(owner="Committee", stated="No rule is held."),
                ),
                uncertainties=("Supply cannot be stated.",),
            ),
            _snapshot(),
        )

        assert [line.owner for line in brief.blocks_progress] == [
            "Committee",
            "Investor assessment",
        ]

    def test_a_capped_block_says_how_many_it_holds_back(self) -> None:
        brief = brief_for(
            _decision(
                uncertainties=tuple(f"Figure {n} is unsettled." for n in range(5))
            ),
            _snapshot(),
        )

        assert len(brief.blocks_progress) == BLOCK_LIMIT
        assert dict(brief.withheld)["blocks_progress"] == 5 - BLOCK_LIMIT

    def test_every_empty_block_states_its_absence(self) -> None:
        brief = brief_for(_decision(), _snapshot())

        assert brief.current_view_absent is not None
        assert brief.blocks_progress_absent is not None
        assert brief.would_change_view_absent is not None

    def test_a_watch_item_carries_what_would_settle_it(self) -> None:
        brief = brief_for(
            _decision(),
            _snapshot(
                watch=(
                    WatchItem(
                        stated="Whether the fee economy holds up.",
                        measured_by="the next daily fee reading",
                        because=("ref",),
                    ),
                )
            ),
        )

        line = brief.would_change_view[0]

        assert line.stated == "Whether the fee economy holds up"
        assert line.support == "the next daily fee reading"


class TestItAuthorsNothing:
    def test_every_rendered_sentence_is_a_substring_of_its_source(self) -> None:
        """The whole contract, asserted directly.

        A heading, an order and a connective are this layer's to add. A
        *word* of a finding is not — so every clause it emits must appear
        verbatim in the sentence the owning layer established.
        """

        drivers = (
            _driver("Economic activity is reaching the token itself."),
            _driver("A regulator opened a review.", Direction.ADVERSE),
        )
        questions = (
            UnresolvedQuestion(
                owner="Supply Governance Committee",
                stated="No mechanical issuance rule is held. That is about us.",
            ),
        )
        uncertainties = ("Supply cannot be stated: estimates run wide.",)
        watch = (
            WatchItem(
                stated="Whether the fee economy holds up.",
                measured_by="the next reading",
                because=("ref",),
            ),
        )

        brief = brief_for(
            _decision(unresolved=questions, uncertainties=uncertainties),
            _snapshot(drivers=drivers, watch=watch),
        )

        sources = [
            *(driver.stated for driver in drivers),
            *(question.stated for question in questions),
            *uncertainties,
            *(item.stated for item in watch),
        ]

        lines: list[BriefLine] = [
            *brief.current_view,
            *brief.blocks_progress,
            *brief.would_change_view,
        ]

        assert lines

        for line in lines:
            assert any(line.stated in source for source in sources), line.stated

            if line.qualification is not None:
                assert any(line.qualification in source for source in sources)

    def test_lowercasing_moves_exactly_one_character(self) -> None:
        for opener in LOWERCASEABLE:
            clause = f"{opener.capitalize()} Hyperliquid Reports X"

            brief = brief_for(
                _decision(
                    unresolved=(UnresolvedQuestion(owner="C", stated=clause + "."),)
                ),
                _snapshot(drivers=(_driver("Fees rose."),)),
            )

            assert brief.setup is not None
            # The interior name never changes case.
            assert "Hyperliquid Reports X" in brief.setup

    @pytest.mark.parametrize("opener", ["Hyperliquid", "MOVRvest", "CoinGecko"])
    def test_a_proper_noun_is_never_lowercased(self, opener: str) -> None:
        brief = brief_for(
            _decision(
                unresolved=(
                    UnresolvedQuestion(
                        owner="C", stated=f"{opener} publishes nothing."
                    ),
                )
            ),
            _snapshot(drivers=(_driver("Fees rose."),)),
        )

        assert brief.setup is not None
        assert opener in brief.setup
        assert opener.lower() not in brief.setup
