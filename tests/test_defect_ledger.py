"""The ledger replays the store; status is measured, credit is confirmed."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
)
from app.domain.defect_ledger import (
    DefectInstance,
    DefectLedger,
    LedgerStatus,
    ResolutionClaim,
)
from app.domain.provenance import Provenance
from app.domain.reader_defects import Claim, DefectCause
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.defect_ledger_service import DefectLedgerService
from app.services.reader_defect_service import ReaderDefectService
from tests.test_playbook_mapping import MFG, SOURCE, segment

EPOCH = datetime(2026, 8, 7, tzinfo=UTC)


def undescribed(name: str, *, share: float) -> BusinessSegment:
    """A segment with its size settled and its description absent."""

    return replace(
        segment(name, share=share),
        undescribed_because=(
            f"The description of '{name}' arrived with no words at all."
        ),
    )


def observation(
    segments: tuple[BusinessSegment, ...],
    *,
    hour: int,
    source=SOURCE,
) -> CompanyKnowledgeObservation:
    return CompanyKnowledgeObservation(
        symbol=source.symbol,
        description="What the company says it does.",
        segments=segments,
        source=source,
        reading=Provenance(
            source="10-K via SEC EDGAR, read by stub-1",
            observed_at=EPOCH + timedelta(hours=hour),
        ),
    )


class FakeStore:
    """Documents per symbol, shaped exactly as the real store serves them."""

    def __init__(
        self,
        entries: dict[str, tuple[tuple[CompanyKnowledgeObservation, ...], ...]],
    ) -> None:
        self._entries = entries

    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def documents(
        self, symbol: str
    ) -> tuple[tuple[CompanyKnowledgeObservation, ...], ...]:
        return tuple(
            sorted(
                self._entries.get(symbol, ()),
                key=lambda observations: observations[0].source.published_on,
            )
        )

    def latest(self, symbol: str) -> tuple[CompanyKnowledgeObservation, ...]:
        documents = self.documents(symbol)

        return documents[-1] if documents else ()


# ── the replay ──────────────────────────────────────────────────────


def test_a_defect_that_settles_with_width_is_resolved_with_its_dates() -> None:
    """One reading's absence, outvoted by two described readings: the
    ledger keeps the whole life — the absence at width one, the
    disagreement at width two, both no longer found — and the final
    state carries no open instance, exactly as the taxonomy says."""

    absent = undescribed("Compute", share=0.9)
    described = segment("Compute", share=0.9, earns=MFG)

    ledger = DefectLedgerService(
        store=FakeStore(
            {
                "NVDA": (
                    (
                        observation((absent,), hour=0),
                        observation((described,), hour=1),
                        observation((described,), hour=2),
                    ),
                )
            }
        )
    ).ledger()

    by_cause = {instance.cause: instance for instance in ledger.instances}

    never = by_cause[DefectCause.NEVER_ARRIVED]

    assert never.claim is Claim.DESCRIPTION
    assert never.first_observed == EPOCH
    assert never.last_observed == EPOCH
    assert not never.still_found

    disagreement = by_cause[DefectCause.UNSETTLED]

    assert disagreement.first_observed == EPOCH + timedelta(hours=1)
    assert not disagreement.still_found

    assert all(entry.status is LedgerStatus.RESOLVED for entry in ledger.entries)


def test_a_persistent_defect_stays_open_and_dates_its_last_finding() -> None:
    absent = undescribed("Markets", share=0.8)

    ledger = DefectLedgerService(
        store=FakeStore(
            {
                "NVDA": (
                    (
                        observation((absent,), hour=0),
                        observation((absent,), hour=3),
                    ),
                )
            }
        )
    ).ledger()

    (entry,) = tuple(
        entry for entry in ledger.entries if entry.cause is DefectCause.NEVER_ARRIVED
    )

    assert entry.status is LedgerStatus.OPEN
    assert entry.first_observed == EPOCH
    assert entry.last_observed == EPOCH + timedelta(hours=3)
    assert entry.open_claims == 1
    assert entry.open_companies == ("NVDA",)


def test_a_newer_filing_resolves_what_it_supersedes() -> None:
    """The replay serves what `latest` would have served: once a newer
    filing is read, the older document's defects stop being found."""

    older = replace(
        SOURCE,
        key="older-filing",
        identifier="10-K older",
        published_on=SOURCE.published_on - timedelta(days=365),
    )

    ledger = DefectLedgerService(
        store=FakeStore(
            {
                "NVDA": (
                    (
                        observation(
                            (undescribed("Compute", share=0.9),),
                            hour=0,
                            source=older,
                        ),
                    ),
                    (
                        observation(
                            (segment("Compute", share=0.9, earns=MFG),),
                            hour=1,
                        ),
                    ),
                )
            }
        )
    ).ledger()

    (instance,) = ledger.instances

    assert instance.cause is DefectCause.NEVER_ARRIVED
    assert not instance.still_found


def test_reading_an_older_filing_late_never_replays_as_current() -> None:
    """The rule `latest` applies, applied through time: an older
    document read after a newer one was never the current word, so its
    defects never entered the served consensus at all."""

    older = replace(
        SOURCE,
        key="older-filing",
        identifier="10-K older",
        published_on=SOURCE.published_on - timedelta(days=365),
    )

    ledger = DefectLedgerService(
        store=FakeStore(
            {
                "NVDA": (
                    (
                        observation(
                            (segment("Compute", share=0.9, earns=MFG),),
                            hour=0,
                        ),
                    ),
                    (
                        observation(
                            (undescribed("Compute", share=0.9),),
                            hour=1,
                            source=older,
                        ),
                    ),
                )
            }
        )
    ).ledger()

    assert ledger.instances == ()
    assert ledger.scanned == ("NVDA",)


def test_the_ledgers_open_instances_are_the_taxonomys_defects() -> None:
    """The claim the ledger stakes: derived state that never disagrees
    with the store. Same fake store, both measurements — what the
    replay still finds is exactly what the taxonomy classifies."""

    store = FakeStore(
        {
            "ONE": (
                (
                    observation((undescribed("A", share=0.5),), hour=0),
                    observation((undescribed("A", share=0.5),), hour=1),
                ),
            ),
            "TWO": (
                (
                    observation((undescribed("A", share=0.5),), hour=0),
                    observation((segment("A", share=0.5, earns=MFG),), hour=1),
                    observation((segment("A", share=0.5, earns=MFG),), hour=2),
                ),
            ),
        }
    )

    still_found = {
        (instance.symbol, instance.segment, instance.claim, instance.cause)
        for instance in DefectLedgerService(store=store).ledger().instances
        if instance.still_found
    }

    classified = {
        (defect.symbol, defect.segment, defect.claim, defect.cause)
        for defect in ReaderDefectService(store=store).taxonomy().defects
    }

    assert still_found == classified


# ── credit, confirmed and never trusted ─────────────────────────────


def instance(
    cause: DefectCause,
    *,
    symbol: str = "NVDA",
    still_found: bool,
    hour: int = 0,
) -> DefectInstance:
    return DefectInstance(
        symbol=symbol,
        segment="Compute",
        claim=Claim.DESCRIPTION,
        cause=cause,
        first_observed=EPOCH + timedelta(hours=hour),
        last_observed=EPOCH + timedelta(hours=hour),
        still_found=still_found,
    )


def test_a_claim_is_credited_only_when_the_rerun_stops_finding_it() -> None:
    resolved_claim = ResolutionClaim(
        cause=DefectCause.NEVER_ARRIVED,
        pull_request=52,
        shipped="the reader asks for absent descriptions once more",
    )
    premature_claim = ResolutionClaim(
        cause=DefectCause.MISAPPLIED,
        pull_request=53,
        shipped="ownership widened",
    )

    ledger = DefectLedger(
        scanned=("NVDA",),
        instances=(
            instance(DefectCause.NEVER_ARRIVED, still_found=False),
            instance(DefectCause.MISAPPLIED, still_found=True),
        ),
        claims=(resolved_claim, premature_claim),
    )

    by_cause = {entry.cause: entry for entry in ledger.entries}

    never = by_cause[DefectCause.NEVER_ARRIVED]

    assert never.status is LedgerStatus.RESOLVED
    assert never.credited == (resolved_claim,)
    assert never.unconfirmed == ()

    misapplied = by_cause[DefectCause.MISAPPLIED]

    assert misapplied.status is LedgerStatus.OPEN
    assert misapplied.credited == ()
    assert misapplied.unconfirmed == (premature_claim,)


def test_a_claim_on_a_pattern_never_recorded_is_unadjudicated() -> None:
    claim = ResolutionClaim(
        cause=DefectCause.UNGROUNDED,
        pull_request=54,
        shipped="grounding tightened",
    )

    ledger = DefectLedger(
        scanned=("NVDA",),
        instances=(instance(DefectCause.NEVER_ARRIVED, still_found=True),),
        claims=(claim,),
    )

    assert ledger.unadjudicated == (claim,)
    assert all(entry.claims == () for entry in ledger.entries)


def test_entries_rank_by_historical_cost() -> None:
    ledger = DefectLedger(
        scanned=("A", "B", "C"),
        instances=(
            instance(DefectCause.NEVER_ARRIVED, symbol="A", still_found=False),
            instance(DefectCause.NEVER_ARRIVED, symbol="B", still_found=True),
            instance(DefectCause.MISAPPLIED, symbol="C", still_found=True),
        ),
    )

    causes = tuple(entry.cause for entry in ledger.entries)

    assert causes == (DefectCause.NEVER_ARRIVED, DefectCause.MISAPPLIED)

    never = ledger.entries[0]

    assert never.occurrences == 2
    assert never.companies == ("A", "B")
    assert never.open_claims == 1
    assert never.open_companies == ("B",)


# ── the store's side of the replay ──────────────────────────────────


def test_the_store_serves_documents_oldest_filing_first(tmp_path) -> None:
    store = JsonCompanyKnowledgeStore(directory=tmp_path)

    older = replace(
        SOURCE,
        key="older-filing",
        identifier="10-K older",
        published_on=SOURCE.published_on - timedelta(days=365),
    )

    store.append(observation((segment("Compute", share=0.9, earns=MFG),), hour=1))
    store.append(observation((segment("Compute", share=0.8),), hour=0, source=older))
    store.append(observation((segment("Compute", share=0.9, earns=MFG),), hour=2))

    documents = store.documents("NVDA")

    assert tuple(entry[0].source.key for entry in documents) == (
        "older-filing",
        SOURCE.key,
    )
    assert tuple(len(entry) for entry in documents) == (1, 2)

    assert store.documents("ABSENT") == ()
