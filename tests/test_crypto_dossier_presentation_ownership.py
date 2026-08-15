"""One kind of information, one owner on the page.

The crypto dossier grew by composing layers that were each right on
their own, and every one of them words its own conclusions. Composed
onto a single page that produced six kinds of repetition, and the
measurement is the point: across all eight assets **every** committee
reason was byte-identical between *What can usefully be said* and *What
each committee concluded*; Bitcoin printed two lens sentences nine times
between them and Hyperliquid five sentences fifteen times; thirteen
findings each ended *"First observed on one capture."* directly beneath
a heading reading *"1 capture recorded"*.

None of that is a backend defect. `InvestorAssessment` is *supposed* to
quote a committee, the matrix is *supposed* to carry the same conclusion
in the committee's own words, and every question genuinely is asked
through a lens. The defect is that one page rendered both copies and had
no honest way to tell which was which — so the repair is provenance the
domain already held and used to discard, never a frontend rule.

These are architectural rather than per-asset, because a snapshot of
Bitcoin's page would pass again the moment a seventh kind of repetition
arrived. Fixtures are domain builders in a temporary store: **nothing
here reads acquired evidence**, which is the failure this repository has
already watched four times.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.api.models.crypto_dossier_adapter import journal_response
from app.domain.asset_class import AssetClass
from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    ApplicabilityBasis,
    CommitteeJudgment,
    Confidence,
    JudgmentState,
)
from app.domain.committee_protocol import CommitteeContract
from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.crypto_intelligence import ClaimType, EventKind
from app.domain.crypto_questions import QuestionApplicability
from app.domain.intelligence_journal import (
    Capture,
    JournalEntry,
    ObservationStatus,
    TemporalStatus,
    project,
    shared_maturity,
)
from app.infrastructure.evidence.judgment_history_store import JudgmentHistoryStore
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.investor_assessment_service import InvestorAssessmentService
from app.services.judgment_history_service import JudgmentHistoryService
from app.services.supply_governance_committee import CONTRACT as SUPPLY_GOVERNANCE
from app.services.supply_governance_committee import Verdict as SupplyVerdict
from app.services.value_capture_committee import CONTRACT as FEE_CAPTURE
from app.services.value_capture_committee import Verdict as FeeVerdict

WEB = Path(__file__).resolve().parent.parent / "apps" / "web" / "movrvest-web"
PAGE = WEB / "app" / "crypto" / "[symbol]" / "page.tsx"

NOW = datetime(2026, 8, 11, tzinfo=UTC)


# ── fixtures: every committee outcome, built rather than acquired ────

#: One asset per posture a committee can hold, so a repair that fixes
#: the answered case and forgets the three unanswered ones fails here.
#: The reasons are deliberately distinctive strings — a duplication test
#: that searched for common English would find it everywhere.
POSTURES: dict[str, dict[str, object]] = {
    "ANSWERED": {
        # Each committee owns its own verdict vocabulary and a contract
        # refuses a token outside it, so the verdict is looked up per
        # committee below rather than fixed here.
        "answers": True,
        "confidence": Confidence.MULTIPLE_OBSERVATIONS,
        "because": "Fees were paid and a mechanism directs them to holders.",
    },
    "DECLINED": {
        "applicability": Applicability.NOT_ECONOMICALLY_APPLICABLE,
        "state": JudgmentState.ABSTAINED,
        "abstained": AbstentionReason.NOT_ECONOMICALLY_APPLICABLE,
        "because": "Its fees are the budget that secures the network.",
    },
    "THIN": {
        "state": JudgmentState.ABSTAINED,
        "abstained": AbstentionReason.INSUFFICIENT_EVIDENCE,
        "because": "No mechanical issuance rule is held for this asset.",
    },
    "OFFLINE": {
        "state": JudgmentState.UNAVAILABLE,
        "unavailable": "Committee judgment is off, so no verdict was reached.",
    },
    "UNKNOWN": {
        "applicability": Applicability.UNESTABLISHED,
        "state": JudgmentState.ABSTAINED,
        "abstained": AbstentionReason.APPLICABILITY_UNESTABLISHED,
        "because": "No economic role is established for this asset.",
    },
}


VERDICTS = {
    FEE_CAPTURE.key: FeeVerdict.MECHANISM_EVIDENCED,
    SUPPLY_GOVERNANCE.key: SupplyVerdict.CONSENSUS_BOUND,
}


def _judgment(
    asset: str,
    contract: CommitteeContract,
    spec: dict[str, object],
) -> CommitteeJudgment:
    verdict = VERDICTS[contract.key] if spec.get("answers") else None

    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=spec.get("state", JudgmentState.JUDGED),  # type: ignore[arg-type]
        basis=ApplicabilityBasis(
            applicability=spec.get(  # type: ignore[arg-type]
                "applicability", Applicability.APPLICABLE
            ),
            because="fixture applicability",
            economic_role="Exchange network",
        ),
        verdict=verdict,
        confidence=spec.get("confidence"),  # type: ignore[arg-type]
        refs=("A1", "A2") if verdict else (),
        because=spec.get("because"),  # type: ignore[arg-type]
        abstained_because=spec.get("abstained"),  # type: ignore[arg-type]
        unavailable_because=spec.get("unavailable"),  # type: ignore[arg-type]
        judged_at=NOW,
    )


@pytest.fixture
def matrix(tmp_path: Path) -> CommitteeMatrixService:
    """One asset per posture, both committees, in a temporary store."""

    history = JudgmentHistoryService(store=JudgmentHistoryStore(root=tmp_path))

    for asset, spec in POSTURES.items():
        for contract in (FEE_CAPTURE, SUPPLY_GOVERNANCE):
            history.record(_judgment(asset, contract, spec), now=NOW)

    return CommitteeMatrixService(history=history)


@pytest.fixture
def page_source() -> str:
    return PAGE.read_text(encoding="utf-8")


def _without_comments(source: str) -> str:
    """The page with its prose removed, so a scan reads what it renders.

    Crude on purpose: it drops `/* … */` and `//` runs and nothing else.
    A JSX literal containing `//` would be mangled, and there is none —
    a stricter parser would need a TypeScript runtime this repository
    does not have.
    """

    without_blocks = re.sub(r"/\*.*?\*/", " ", source, flags=re.DOTALL)

    return re.sub(r"^\s*//.*$", " ", without_blocks, flags=re.MULTILINE)


def _assessment(matrix: CommitteeMatrixService, asset: str):  # type: ignore[no-untyped-def]
    # No supply reading: this file is about committee and journal
    # presentation, and a supply figure would only add noise. The
    # archetype seam takes the corpus's own resolver.
    class _NoSupply:
        def established(self, symbol: str, asset_class: AssetClass) -> None:
            return None

    return InvestorAssessmentService(
        supply=_NoSupply(),  # type: ignore[arg-type]
        matrix=matrix,
    ).for_asset(asset)


# ── 1. a committee conclusion has exactly one investor-facing owner ──


@pytest.mark.parametrize("asset", sorted(POSTURES))
def test_every_committee_statement_names_the_committee_it_quotes(
    matrix: CommitteeMatrixService,
    asset: str,
) -> None:
    """The provenance that lets a page route a conclusion to one owner.

    Exhaustive over the postures rather than over one asset, because the
    committee half of the assessment layer has four separate exits and
    the defect is one of them forgetting to say where it came from.
    """

    assessment = _assessment(matrix, asset)

    keys = {cell.committee.key for cell in matrix.for_asset(asset).assessments}

    assert keys, "the fixture must record both committees"

    for statement in assessment.statements:
        assert statement.from_committee in keys, (
            f"{asset}/{statement.subject} quotes a committee and does not "
            "say which, so a surface rendering the committees beside it "
            "cannot tell this statement from an evidence reading"
        )

    # And a silence a committee owns is marked too, or the page would
    # print "nothing useful is held about Value Capture" beside the
    # Value Capture card saying exactly why. A subset, never the whole
    # list: this fixture holds no supply reading, so the three quantity
    # subjects are silences no committee owns and must stay unmarked.
    marked = set(assessment.silent_committees)
    named = {statement.subject for statement in assessment.statements}

    assert marked <= set(assessment.silent_about)

    for cell in matrix.for_asset(asset).assessments:
        subject = cell.committee.name.replace(" Committee", "")

        assert (subject in named) ^ (subject in marked), (
            f"{asset}: {subject!r} must be named exactly once — as a "
            "statement or as a committee-owned silence, never both or "
            "neither"
        )


def test_a_committee_reason_is_rendered_by_exactly_one_section(
    matrix: CommitteeMatrixService,
) -> None:
    """Identical semantics may not travel two presentation paths.

    The measured defect: on every one of the eight assets held, the
    committee's `because` appeared verbatim in both sections. This
    asserts the *page's* two owners cannot both claim it — the assessment
    section renders what `from_committee is None` selects, and that
    selection must leave no committee reason behind.
    """

    for asset in POSTURES:
        assessment = _assessment(matrix, asset)

        owned = [s for s in assessment.statements if s.from_committee is None]

        reasons = {
            cell.because for cell in matrix.for_asset(asset).assessments if cell.because
        }

        for statement in owned:
            for text in (
                statement.stated,
                statement.qualification,
                statement.uncertainty,
            ):
                assert text not in reasons, (
                    f"{asset}: a statement the assessment section owns "
                    f"repeats a committee's own reason — {text!r}"
                )


def test_the_assessment_section_routes_by_provenance(page_source: str) -> None:
    """The page must select on the backend's mark, not on a subject name.

    A frontend that matched `"Value Capture"` against a committee name
    would be re-deriving `name.replace(" Committee", "")` in TypeScript,
    which is the mapping rule this side is forbidden to hold.
    """

    assert "statement.fromCommittee === null" in page_source
    assert "silentCommittees.includes" in page_source

    # And no name-shaped matching anywhere near it.
    assert 'Committee"' not in page_source
    assert 'replace(" Committee"' not in page_source


# ── 2. execution counts are not investment evidence ─────────────────


def test_no_execution_counter_reaches_the_investor_surface(
    page_source: str,
) -> None:
    """Neither counter survives on the page, and for different reasons.

    *Times convened* counts runs of `movrvest judge`. Across the whole
    recorded corpus no verdict has ever changed; the variation is this
    platform's judging flag being turned off and on. It is execution
    history.

    *Evidence it weighed* did not measure what it said. The count is
    captured beside the judgment by the recording command whether or not
    the committee received it, and a committee that declines a question
    returns before reading any evidence — so Bitcoin's Value Capture
    declined the question and reported weighing three findings while
    citing none of them.

    Both remain in the domain, in the store and on `movrvest committees`.
    This is about where they may be shown.
    """

    # Comments stripped first: this file explains at length *why* both
    # counters left, and a scan that could not tell an explanation from
    # a render would forbid saying so.
    code = _without_comments(page_source)

    for banned in (
        "judgmentsRecorded",
        "evidenceCount",
        "Times convened",
        "Evidence it weighed",
    ):
        assert banned not in code, f"{banned!r} is rendered by the investor surface"


def test_the_domain_still_carries_both_counters() -> None:
    """Nothing was deleted. A presentation fix that lost history would
    be a worse defect than the one it fixed."""

    from app.domain.committee_matrix import CommitteeAssessment

    fields = set(CommitteeAssessment.__dataclass_fields__)

    assert {"evidence_count", "judgments_recorded"} <= fields


# ── 3. shared lens context is rendered once, at the lens ────────────


@pytest.mark.parametrize("symbol", sorted(ASSIGNMENTS))
def test_an_asked_question_always_names_the_lens_that_asks_it(
    symbol: str,
) -> None:
    """The grouping the page rests on, asserted over the whole corpus.

    Two properties, and the page needs both: an asked question always
    names its lens (so grouping never drops a row into an unnamed
    bucket), and a lens has exactly one applicability sentence (so
    stating it once per lens loses nothing). Applicability is settled
    from the archetype alone, so this needs no acquired evidence.
    """

    playbook = CryptoPlaybookService().established(symbol, AssetClass.CRYPTO)

    assert playbook is not None

    by_lens: dict[str, set[str]] = {}

    for row in playbook.coverage:
        applicability = row.applicability

        if applicability.state is not QuestionApplicability.ASK:
            # Refused and undetermined reasons are genuinely different
            # from one another — eight distinct ones on Bitcoin — and
            # they are the reasons that must stay per row.
            assert applicability.asked_by is None

            continue

        assert applicability.asked_by is not None, (
            f"{symbol}/{row.question.key} is asked and names no lens"
        )

        by_lens.setdefault(applicability.asked_by.value, set()).add(
            applicability.because
        )

    for lens, sentences in by_lens.items():
        assert len(sentences) == 1, (
            f"{symbol}: the {lens} lens has {len(sentences)} applicability "
            "sentences, so stating it once per lens would lose one"
        )


def test_the_page_groups_asked_questions_by_lens(page_source: str) -> None:
    """And groups on the given field rather than by comparing sentences."""

    assert "function byLens(" in page_source
    assert "question.askedBy" in page_source

    # The old shape: the lens sentence printed on every row.
    assert page_source.count("{question.applicabilityBecause}") == 1


# ── 4. per-fact maturity says nothing the section already said ──────


def _entry(key: str, at: datetime, status: ObservationStatus) -> JournalEntry:
    return JournalEntry(
        capture_id=f"c-{at:%Y%m%d}",
        asset="TEST",
        captured_at=at,
        key=key,
        family=EventKind.NETWORK_ACTIVITY,
        claim_type=ClaimType.MEASURED,
        status=status,
        stated=f"{key} reads something.",
        value=1.0 if status is ObservationStatus.OBSERVED else None,
        unit="tokens" if status is ObservationStatus.OBSERVED else None,
    )


def _capture(at: datetime, entries: list[JournalEntry]) -> Capture:
    return Capture(
        capture_id=f"c-{at:%Y%m%d}",
        asset="TEST",
        captured_at=at,
        entries=tuple(entries),
    )


def _project(captures: list[Capture]):  # type: ignore[no-untyped-def]
    return project("TEST", captures, now=NOW + timedelta(hours=1))


def test_one_capture_states_its_maturity_once() -> None:
    """The measured defect, at its source.

    Thirteen findings from one capture each ended *"First observed on one
    capture."* under a heading that had already said one capture exists.
    """

    facts = _project(
        [
            _capture(
                NOW,
                [
                    _entry(f"k{index}", NOW, ObservationStatus.OBSERVED)
                    for index in range(13)
                ],
            )
        ]
    )

    assert len(facts) == 13

    shared = shared_maturity(facts)

    assert shared is not None
    assert shared.status is TemporalStatus.FIRST_OBSERVED
    assert shared.span_stated == "on one capture"

    # Every fact's own sentence still carries it — the synthesis cites
    # `stated` and it is untouched. What changed is that a second
    # sentence exists which does not.
    for fact in facts:
        assert "on one capture" in fact.stated
        assert "on one capture" not in fact.observed_stated
        assert fact.observed_stated
        assert fact.stated.startswith(fact.observed_stated)


def test_a_finding_whose_maturity_differs_keeps_it() -> None:
    """Hoisting is for what is shared. A change is never hoisted away."""

    first = NOW - timedelta(days=9)

    captures = [
        _capture(
            first,
            [_entry(key, first, ObservationStatus.OBSERVED) for key in ("a", "b")],
        ),
        _capture(
            NOW,
            [
                _entry("a", NOW, ObservationStatus.OBSERVED),
                JournalEntry(
                    capture_id=f"c-{NOW:%Y%m%d}",
                    asset="TEST",
                    captured_at=NOW,
                    key="b",
                    family=EventKind.NETWORK_ACTIVITY,
                    claim_type=ClaimType.MEASURED,
                    status=ObservationStatus.OBSERVED,
                    stated="b reads something else.",
                    value=2.0,
                    unit="tokens",
                ),
            ],
        ),
    ]

    facts = _project(captures)

    statuses = {fact.status for fact in facts}

    assert TemporalStatus.STILL_PRESENT in statuses
    assert statuses & {
        TemporalStatus.CHANGED,
        TemporalStatus.INCREASED,
        TemporalStatus.DECREASED,
    }

    assert shared_maturity(facts) is None, (
        "one finding moved and another did not, so there is no shared "
        "maturity to state and every row must keep its own"
    )


def test_an_unreadable_surface_does_not_suppress_the_shared_line() -> None:
    """An unavailable fact carries no coverage clause, so it is not asked.

    §6, and it is load-bearing rather than a convenience: five of the
    eight assets held carry one or two unavailable readings, and
    consulting them would have left every *other* finding on those pages
    repeating itself.
    """

    entries = [
        _entry(f"k{index}", NOW, ObservationStatus.OBSERVED) for index in range(4)
    ]
    entries.append(_entry("broken", NOW, ObservationStatus.UNAVAILABLE))

    facts = _project([_capture(NOW, entries)])

    shared = shared_maturity(facts)

    assert shared is not None

    unavailable = [f for f in facts if f.status is TemporalStatus.UNAVAILABLE]

    assert len(unavailable) == 1
    assert not unavailable[0].carries_span
    assert "on one capture" not in unavailable[0].stated

    # It is not spoken for, so the page renders its own sentence — the
    # one saying the failure was this platform's and not the asset's.
    assert "fact about the reading" in unavailable[0].stated


def test_nothing_but_unavailable_readings_claims_no_shared_coverage() -> None:
    """A vacuous claim of shared coverage is worse than none."""

    facts = _project(
        [
            _capture(
                NOW,
                [
                    _entry(f"k{index}", NOW, ObservationStatus.UNAVAILABLE)
                    for index in range(3)
                ],
            )
        ]
    )

    assert facts
    assert shared_maturity(facts) is None
    assert journal_response(facts, captures=1)["shared_maturity"] is None  # type: ignore[index]


def test_the_shared_sentence_never_overreaches() -> None:
    """It speaks for what it speaks for, and says so.

    *"Every finding below"* would be false about the one finding a reader
    most needs to notice — the one this platform could not read.
    """

    entries = [_entry("a", NOW, ObservationStatus.OBSERVED)]
    entries.append(_entry("broken", NOW, ObservationStatus.UNAVAILABLE))

    shared = shared_maturity(_project([_capture(NOW, entries)]))

    assert shared is not None
    assert not re.search(r"\bevery\b", shared.stated, re.IGNORECASE)
    assert "Except where a finding says otherwise" in shared.stated


def test_the_page_renders_the_reading_only_where_it_is_spoken_for(
    page_source: str,
) -> None:
    """Both halves, or the guarantee is half a guarantee."""

    assert "fact.carriesSpan" in page_source
    assert "covered ? fact.observedStated : fact.stated" in page_source
