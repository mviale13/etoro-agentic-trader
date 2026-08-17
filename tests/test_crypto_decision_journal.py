"""What MOVRvest judged about a digital asset, at each recorded point.

DV6. The read side converged across DV3–DV5; the canonical crypto
decision was still never written down, so the platform could say what it
thinks about BTC today and nothing about what it thought last week under
the evidence that existed then.

Pinned here:

1. **One authority.** The journal receives the canonical decision the
   live surfaces receive. There is no second crypto decision constructor
   and no recomputation at write time.
2. **A recorded rationale belongs to the decision made then.** #113's
   law: reading history never re-words an old entry from today's
   committee judgments, even when the software would phrase the same
   state differently now.
3. **Change is checked, not assumed.** A decision naming the records it
   rests on is appended only when that set — or the answer over it, or
   the rule that produced it — has moved. Re-reading a page appends
   nothing.
4. **Absence is first-class.** No conviction, no scores, no fabricated
   strengths or risks, and `digital-asset-gates@1` recorded as the
   authority.

**Every test here writes to a `tmp_path` repository.** None reads the
acquired store, so none can pass by exercising zero specimens — and
`test_the_acceptance_suite_exercised_every_specimen` fails outright if
the corpus below ever empties.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.application.learning.decision_journal import DecisionJournal
from app.cio.decision_state import DecisionState
from app.cio.digital_asset_decision import (
    DigitalAssetDecision,
    UnresolvedQuestion,
    as_executive_decision,
)
from app.domain.decision_rules import DIGITAL_ASSET_GATES
from app.repositories.json_event_repository import JsonEventRepository

#: The DV3 specimens, each carrying the shape its live judgment has.
#: Declared rather than read from the store, because the suite runs
#: against an empty evidence root and a corpus-shaped fixture would
#: quietly test nothing.
SPECIMENS: dict[str, DigitalAssetDecision] = {
    "BTC": DigitalAssetDecision(
        symbol="BTC",
        state=DecisionState.INVESTIGATE,
        rationale=(
            "Structural evidence is established and quoted below, and the "
            "case cannot progress past research."
        ),
        established=(
            "Supply Governance Committee established that new supply is "
            "created by a mechanical rule this platform has read and re-run. "
            "On its investment meaning, what this conclusion means for an "
            "investment case is not established by this platform.",
        ),
        not_applicable=(
            "Value Capture Committee: This asset's established economic role "
            "is monetary, so asking whether fees are captured for holders is "
            "the wrong instrument.",
        ),
        judged=True,
        judgment_ids=("20260811T122514-e730d6ad", "20260811T122548-7739b78e"),
    ),
    "ETH": DigitalAssetDecision(
        symbol="ETH",
        state=DecisionState.INVESTIGATE,
        rationale=(
            "Structural evidence is established and quoted below, and the "
            "case cannot progress past research."
        ),
        established=(
            "Value Capture Committee established that measured network "
            "activity is captured for the token by an evidenced mechanism.",
        ),
        unresolved=(
            UnresolvedQuestion(
                owner="Supply Governance Committee",
                stated="No mechanical issuance rule is held for this asset.",
            ),
        ),
        judged=True,
        judgment_ids=("20260811T122514-41c52439", "20260811T122555-ffb93742"),
    ),
    "TAO": DigitalAssetDecision(
        symbol="TAO",
        state=DecisionState.MONITOR,
        rationale=(
            "No structural question is yet established as applicable to this "
            "asset. Establishing the asset's economic role is the advance."
        ),
        unresolved=(
            UnresolvedQuestion(
                owner="Supply Governance Committee",
                stated="No economic role is established for this asset.",
            ),
            UnresolvedQuestion(
                owner="Value Capture Committee",
                stated="No economic role is established for this asset.",
            ),
        ),
        judged=True,
        judgment_ids=("20260811T122514-77f93628", "20260811T122623-3e012af9"),
    ),
    "ARB": DigitalAssetDecision(
        symbol="ARB",
        state=DecisionState.INVESTIGATE,
        rationale=(
            "Structural evidence is established and quoted below, and the "
            "case cannot progress past research."
        ),
        established=(
            "Value Capture Committee established that measured network "
            "activity is not captured for the token.",
        ),
        material_uncertainties=(
            "Circulating supply cannot be stated as a single figure: "
            "available estimates run from 1.27 billion to 6.61 billion, a "
            "spread of 81%.",
        ),
        judged=True,
        judgment_ids=("20260811T122514-7ece7caa", "20260811T122548-3380ddeb"),
    ),
}

#: Every symbol a test in this module actually wrote and read back.
#: The aggregate guard at the end asserts it covers the corpus, so a
#: fixture that silently stopped producing specimens fails loudly.
EXERCISED: set[str] = set()


def journal(tmp_path: Path) -> DecisionJournal:
    return DecisionJournal(repository=JsonEventRepository(tmp_path))


def record(tmp_path: Path, symbol: str) -> DecisionJournal:
    """Write one specimen and return the journal holding it."""

    written = journal(tmp_path)

    assert written.record(as_executive_decision(SPECIMENS[symbol])) is True

    EXERCISED.add(symbol)

    return written


# ── 1. the canonical decision, written and read back ────────────────


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_the_written_record_is_the_live_decision(
    symbol: str,
    tmp_path: Path,
) -> None:
    """One authority: what is stored is what the surfaces were given."""

    live = as_executive_decision(SPECIMENS[symbol])

    stored = record(tmp_path, symbol).history(symbol).latest

    assert stored is not None
    assert stored.state is live.state
    assert stored.rationale == live.rationale
    assert stored.decided_under == ("digital-asset-gates@1",)
    assert stored.evidence_records == live.evidence_records


@pytest.mark.parametrize("symbol", sorted(SPECIMENS))
def test_no_conviction_and_no_scores_are_recorded(
    symbol: str,
    tmp_path: Path,
) -> None:
    """Absence as a first-class fact, never a zero."""

    stored = record(tmp_path, symbol).history(symbol).latest

    assert stored is not None
    assert stored.conviction is None
    assert stored.scores.is_empty


def test_the_rule_that_decided_is_recorded_with_its_version() -> None:
    """`digital-asset-gates@1`, so a later @2 cannot claim these records."""

    assert DIGITAL_ASSET_GATES.identity == "digital-asset-gates@1"


# ── 2. the specimens, each keeping what makes it itself ─────────────


def test_bitcoin_keeps_its_conclusion_and_its_wrong_instrument_finding(
    tmp_path: Path,
) -> None:
    """The established rule is preserved; NOT_APPLICABLE never turns adverse."""

    live = as_executive_decision(SPECIMENS["BTC"])

    stored = record(tmp_path, "BTC").history("BTC").latest

    assert stored is not None
    assert stored.state is DecisionState.INVESTIGATE

    # Both travel as evidence weighed on the decision, and neither is a
    # risk anywhere — the record has no field one could become.
    assert any("Supply Governance" in line for line in live.evidence_weighed)
    assert any("wrong instrument" in line for line in live.evidence_weighed)
    assert live.key_risks == ()


def test_ethereum_keeps_its_mechanism_and_its_open_question(
    tmp_path: Path,
) -> None:
    live = as_executive_decision(SPECIMENS["ETH"])

    stored = record(tmp_path, "ETH").history("ETH").latest

    assert stored is not None
    assert stored.conviction is None

    assert any("evidenced mechanism" in line for line in live.evidence_weighed)
    assert any(
        line.startswith("Supply Governance Committee: ")
        for line in live.missing_evidence
    )
    assert live.key_risks == ()


def test_bittensor_monitor_is_recorded_as_a_decision(tmp_path: Path) -> None:
    """MONITOR is a judged state, not the absence of one.

    A history that dropped it would report *we have never judged this*
    about an asset whose committees both ran and concluded that they
    cannot establish whether their questions apply.
    """

    stored = record(tmp_path, "TAO").history("TAO")

    assert stored.total == 1
    assert stored.current_state is DecisionState.MONITOR

    latest = stored.latest

    assert latest is not None
    assert latest.decided_under == ("digital-asset-gates@1",)
    assert latest.evidence_records == SPECIMENS["TAO"].judgment_ids
    assert "economic role" in latest.rationale


def test_arbitrum_uncertainty_is_recorded_as_uncertainty(
    tmp_path: Path,
) -> None:
    """The 81% spread is what research would settle, never a risk."""

    live = as_executive_decision(SPECIMENS["ARB"])

    stored = record(tmp_path, "ARB").history("ARB").latest

    assert stored is not None
    assert stored.state is DecisionState.INVESTIGATE

    assert any("spread of 81%" in line for line in live.missing_evidence)
    assert live.key_risks == ()
    assert all("spread of 81%" not in line for line in live.evidence_weighed)


# ── 3. change semantics ─────────────────────────────────────────────


def moved(symbol: str, **changes: object) -> DigitalAssetDecision:
    from dataclasses import replace

    return replace(SPECIMENS[symbol], **changes)  # type: ignore[arg-type]


def test_an_unchanged_decision_is_not_recorded_twice(tmp_path: Path) -> None:
    """Re-reading a page appends nothing.

    Same answer, same rules, same records beneath it — and that is
    checked against the ids rather than assumed from the clock, so it
    holds across days as well as within one.
    """

    written = record(tmp_path, "BTC")

    again = as_executive_decision(SPECIMENS["BTC"])

    assert written.record(again) is False
    assert written.history("BTC").total == 1


def test_a_posture_change_is_recorded(tmp_path: Path) -> None:
    """MONITOR → INVESTIGATE once an applicable question is established."""

    written = journal(tmp_path)

    before = DigitalAssetDecision(
        symbol="NEW",
        state=DecisionState.MONITOR,
        rationale="No structural question is yet established as applicable.",
        judged=True,
        judgment_ids=("j-1", "j-2"),
    )

    after = DigitalAssetDecision(
        symbol="NEW",
        state=DecisionState.INVESTIGATE,
        rationale="Structural evidence is established and quoted below.",
        judged=True,
        judgment_ids=("j-1", "j-3"),
    )

    assert written.record(as_executive_decision(before)) is True
    assert written.record(as_executive_decision(after)) is True

    records = written.history("NEW").records

    assert [item.state for item in records] == [
        DecisionState.MONITOR,
        DecisionState.INVESTIGATE,
    ]

    # The first entry is untouched by the second being written.
    assert records[0].rationale == before.rationale
    assert records[0].evidence_records == ("j-1", "j-2")


def test_evidence_moving_under_a_steady_answer_is_recorded(
    tmp_path: Path,
) -> None:
    """#113's ordinary case, which a day-and-state rule silently drops.

    A committee re-judged and reached the same posture from different
    evidence. That is a new decision about the same question, and a
    journal that could not say so would report the case as untouched.
    """

    written = record(tmp_path, "BTC")

    rejudged = as_executive_decision(
        moved(
            "BTC",
            judgment_ids=("20260811T122514-e730d6ad", "20260901T090000-newer0id"),
        )
    )

    assert written.record(rejudged) is True
    assert written.history("BTC").total == 2


def test_a_rule_version_change_is_recorded(tmp_path: Path) -> None:
    """A decision reached under a new rule is not the old decision.

    Without this, upgrading the rule would leave the last record looking
    as though it had been decided under a rule that did not exist yet.
    """

    from dataclasses import replace

    written = record(tmp_path, "BTC")

    # `ExecutiveDecision` is a pydantic model; the rule beneath it is a
    # frozen dataclass. Each is copied the way its own type allows.
    under_two = as_executive_decision(SPECIMENS["BTC"]).model_copy(
        update={"decided_under": (replace(DIGITAL_ASSET_GATES, version=2),)},
    )

    assert written.record(under_two) is True

    records = written.history("BTC").records

    assert [item.decided_under for item in records] == [
        ("digital-asset-gates@1",),
        ("digital-asset-gates@2",),
    ]


# ── 4. history is never recomputed ──────────────────────────────────


def test_an_old_rationale_survives_the_evidence_moving_on(
    tmp_path: Path,
) -> None:
    """#113's law, at the journal.

    The first entry's every recorded word is byte-identical after a
    later decision is written from different evidence with different
    wording — because reading history reads the record, and never the
    committees as they stand today.
    """

    written = record(tmp_path, "BTC")

    first = written.history("BTC").records[0]

    frozen = (
        first.state,
        first.rationale,
        first.conviction,
        first.decided_under,
        first.evidence_records,
    )

    assert (
        written.record(
            as_executive_decision(
                moved(
                    "BTC",
                    state=DecisionState.MONITOR,
                    rationale="Worded entirely differently today.",
                    judgment_ids=("later-1",),
                )
            )
        )
        is True
    )

    reread = written.history("BTC").records[0]

    assert (
        reread.state,
        reread.rationale,
        reread.conviction,
        reread.decided_under,
        reread.evidence_records,
    ) == frozen


# ── 5. coexistence with the history already recorded ────────────────


def test_a_legacy_record_is_distinguishable_without_being_rewritten(
    tmp_path: Path,
) -> None:
    """The production journal holds crypto decisions from the retired path.

    They carry numeric convictions and rationales no current rule could
    produce, and they stay exactly as written. What tells them apart is
    that they name no rule — which is the truth about them: the rule was
    not recorded, not absent.
    """

    from app.domain.event import Event
    from app.domain.event_type import EventType

    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 8, 11, 14, 37, 54, tzinfo=UTC),
            event_type=EventType.EXECUTIVE_DECISION_RECORDED,
            symbol="BTC",
            payload={
                "state": "INVESTIGATE",
                "conviction": 46,
                "rationale": (
                    "A cryptocurrency has no business quality or valuation to "
                    "assess, and this platform judges an investment case on both."
                ),
            },
        )
    )

    written = DecisionJournal(repository)

    assert written.record(as_executive_decision(SPECIMENS["BTC"])) is True

    EXERCISED.add("BTC")

    legacy, canonical = written.history("BTC").records

    # Untouched, including the number no current rule can produce.
    assert legacy.conviction == 46
    assert legacy.decided_under == ()
    assert legacy.evidence_records == ()
    assert "no business quality" in legacy.rationale

    # And the new one says which rule reached it.
    assert canonical.conviction is None
    assert canonical.decided_under == ("digital-asset-gates@1",)


# ── 6. the company journal is untouched ─────────────────────────────


def test_a_scored_decision_keeps_the_day_and_state_rule(
    tmp_path: Path,
) -> None:
    """A decision naming no records is deduped exactly as it always was."""

    from app.cio.executive_decision import ExecutiveDecision

    written = journal(tmp_path)

    def equity(state: DecisionState, rationale: str) -> ExecutiveDecision:
        return ExecutiveDecision(
            symbol="MSFT",
            state=state,
            conviction=64,
            rationale=rationale,
        )

    assert written.record(equity(DecisionState.INVESTIGATE, "first")) is True

    # Same day, same state, different wording: still one record, which is
    # the behaviour every equity has had since the journal existed.
    assert written.record(equity(DecisionState.INVESTIGATE, "second")) is False

    assert written.record(equity(DecisionState.PREPARE, "moved")) is True

    records = written.history("MSFT").records

    assert [item.state for item in records] == [
        DecisionState.INVESTIGATE,
        DecisionState.PREPARE,
    ]
    assert all(item.conviction == 64 for item in records)
    assert all(item.decided_under == () for item in records)


# ── 7. the guard against a suite that tests nothing ─────────────────


def test_the_acceptance_suite_exercised_every_specimen() -> None:
    """DV5's hazard, made structural.

    An empty evidence root can turn a corpus-shaped assertion into a
    silent skip. Nothing here reads the store — but a fixture that
    stopped producing specimens would still leave the parametrised tests
    passing over an empty list, so the corpus is asserted non-empty and
    every member is asserted to have been written and read back.
    """

    assert SPECIMENS
    assert set(SPECIMENS) == {"BTC", "ETH", "TAO", "ARB"}
    assert EXERCISED == set(SPECIMENS), (
        "every specimen must be written and read back by some test above"
    )
