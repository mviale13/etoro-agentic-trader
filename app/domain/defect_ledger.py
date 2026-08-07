"""The reader's defects as an engineering history, not a snapshot.

The taxonomy answers "where do the reader's absences concentrate now?".
This ledger answers the question behind the unfreeze decision: *which
defects have the highest historical cost* — when each pattern first
appeared in the consensus this platform served, when it was last found,
how many claims it has ever blocked, and whether it is still being
found.

Everything here is derived. The store is append-only and every
observation is dated, so the history is replayed from it on every read
— there is no ledger file to fall out of step with the store, and a
changed rule leaves no stale history behind it. The one thing a replay
cannot derive is attribution: "resolved by PR #N" is a fact about a
pull request, and a measurement can only *confirm* it. A pattern is
resolved when a rerun stops finding it; a PR that believes it did the
resolving records a claim here, and the ledger credits the claim only
while the pattern stays unfound. It never trusts one.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.reader_defects import Claim, DefectCause


class LedgerStatus(StrEnum):
    """Whether a rerun over the store still finds the pattern."""

    #: The consensus the store serves today still carries it.
    OPEN = "open"

    #: A rerun stops finding it. Says nothing about *why*: an
    #: engineering slice, a new filing, or new observations settling a
    #: claim all read the same here, and only a credited claim below
    #: names a cause.
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class ResolutionClaim:
    """One PR's belief that it resolved a defect pattern.

    A claim, deliberately not a fact. Recording it here is how a PR
    asks to be credited; the crediting itself is done by the ledger,
    and only when the rerun stops finding the cause. A claim on a
    pattern the rerun still finds is surfaced as unconfirmed rather
    than hidden — that a PR believed itself the fix is a fact worth
    keeping even while the measurement says otherwise.
    """

    cause: DefectCause

    pull_request: int

    #: What the PR shipped, in a phrase — so the ledger can say what
    #: was done, not merely which number did it.
    shipped: str


#: Every resolution a PR has claimed, appended by the PR that claims
#: it. The ledger credits an entry here only while the rerun stops
#: finding the cause — a claim is how a PR asks, never how it is
#: believed.
CLAIMED_RESOLUTIONS: tuple[ResolutionClaim, ...] = (
    ResolutionClaim(
        cause=DefectCause.NEVER_ARRIVED,
        pull_request=51,
        shipped="an empty arrival is asked about once, by name",
    ),
)


@dataclass(frozen=True, slots=True)
class DefectInstance:
    """One blocked claim's lifetime in the served consensus.

    Keyed by what was blocked and why — symbol, segment, claim, cause —
    so a claim whose cause *changes* (a width-1 absence becoming a
    width-2 disagreement) is two instances, because it was two
    different findings. An instance that vanished and returned is one
    instance: the dates bracket its whole recorded life.
    """

    symbol: str
    segment: str
    claim: Claim
    cause: DefectCause

    #: When the served consensus first carried this defect — the date
    #: of the stored reading after which it appeared.
    first_observed: datetime

    #: The newest stored reading after which it was still found. Not
    #: "today": a pattern nothing has retested stays exactly as dated.
    last_observed: datetime

    #: Whether the consensus derived over the store as it stands now
    #: still carries it — by construction the same answer the taxonomy
    #: gives, because both walk `defects_of` over the same consensus.
    still_found: bool


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """One defect pattern's history: its cost, its dates, its status."""

    cause: DefectCause

    first_observed: datetime
    last_observed: datetime

    #: Every claim this cause has ever blocked, counted once per
    #: instance — the historical cost the entries are ranked by.
    occurrences: int

    companies: tuple[str, ...]

    #: What a rerun still finds, which is what OPEN means.
    open_claims: int
    open_companies: tuple[str, ...]

    status: LedgerStatus

    #: Every claim recorded against this cause, credited or not.
    claims: tuple[ResolutionClaim, ...]

    @property
    def credited(self) -> tuple[ResolutionClaim, ...]:
        """The claims the measurement confirms — resolved, and claimed."""

        return self.claims if self.status is LedgerStatus.RESOLVED else ()

    @property
    def unconfirmed(self) -> tuple[ResolutionClaim, ...]:
        """Claims the rerun contradicts: the pattern is still found."""

        return self.claims if self.status is LedgerStatus.OPEN else ()


@dataclass(frozen=True, slots=True)
class DefectLedger:
    """The store's defect history, replayed — never stored.

    Holds the raw instances and derives the entries on read, the same
    shape the taxonomy has: the aggregation is a property of the
    instances, and there is no second place for it to be true.
    """

    #: Every company the replay covered, defective or not.
    scanned: tuple[str, ...]

    instances: tuple[DefectInstance, ...]

    claims: tuple[ResolutionClaim, ...] = ()

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        """Patterns by historical cost: claims blocked, ever."""

        grouped: dict[DefectCause, list[DefectInstance]] = defaultdict(list)

        for instance in self.instances:
            grouped[instance.cause].append(instance)

        claimed: dict[DefectCause, list[ResolutionClaim]] = defaultdict(list)

        for claim in self.claims:
            claimed[claim.cause].append(claim)

        entries = []

        for cause, instances in grouped.items():
            still = [instance for instance in instances if instance.still_found]

            entries.append(
                LedgerEntry(
                    cause=cause,
                    first_observed=min(
                        instance.first_observed for instance in instances
                    ),
                    last_observed=max(instance.last_observed for instance in instances),
                    occurrences=len(instances),
                    companies=tuple(
                        sorted({instance.symbol for instance in instances})
                    ),
                    open_claims=len(still),
                    open_companies=tuple(
                        sorted({instance.symbol for instance in still})
                    ),
                    status=(LedgerStatus.OPEN if still else LedgerStatus.RESOLVED),
                    claims=tuple(claimed.get(cause, ())),
                )
            )

        return tuple(
            sorted(
                entries,
                key=lambda entry: (
                    -entry.occurrences,
                    -len(entry.companies),
                    entry.cause.value,
                ),
            )
        )

    @property
    def unadjudicated(self) -> tuple[ResolutionClaim, ...]:
        """Claims on causes the replay never recorded.

        The ledger cannot credit what it never saw: history reaches
        only as far as the store's current schema restores, so a claim
        against a pattern whose readings a migration rewrote has
        nothing to be measured against, and saying so beats silently
        dropping it.
        """

        recorded = {instance.cause for instance in self.instances}

        return tuple(claim for claim in self.claims if claim.cause not in recorded)
