"""What each provider claimed an instrument was, at the moment it was read.

The #215 measurement's finding, made storable. The fundamentals cache
keeps one latest value per security, so a cross-provider disagreement
lives exactly as long as the vendor's wording does: SPCX was UNRESOLVED
on the 2026-08-13 payload and ASSUMED on the 2026-08-19 one, and the
store that held the disagreeing claim replaced it with the agreeing one.
An observation stream remembers what a latest-value cache is built to
forget.

**One observation is one funded look.** It carries both providers'
claims verbatim — the broker's, which was never persisted anywhere
before this — the standing this platform derived from them at that
moment, and the raw tenancy fields the vendor's payload happened to
carry. It concludes nothing.

**Historical contradiction is not decision-bearing.** The owner's #215
ruling, restated here because this module is where someone would try to
change it: `IdentityStanding` keeps describing current claims only, the
current UNRESOLVED gate is unchanged, and nothing in this module or its
consumers gates anything on a past capture. The history is visible,
and that is all it is.

**Later agreement is never "resolved" and never "corrected".** #215 §5
measured the resolution-evidence classes and found none uniformly
available — `firstTradeDate` marks SPCX's tenancy boundary and fails to
mark PARA's, the dated-CIK instrument is SEC-scoped, and no provider
correction channel exists. So the lifecycle sentence for a dispute
followed by agreement says exactly what is known: *previously disputed;
current claims agree.* Whether that is a reassignment observed through
vendor lag, a correction, or drift is not derivable from the claims
alone, and wording it as any one of them would manufacture the
resolution evidence the measurement could not find.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.provider_identity import IdentityStanding, ProviderIdentityClaim

#: Stated on every read surface that shows history, verbatim, so the
#: strongest thing a reader can take from a past dispute is bounded.
DISCLOSURE = (
    "Historical contradiction is recorded evidence about past provider "
    "claims; it is not decision-bearing. The current standing is derived "
    "from current claims only."
)


@dataclass(frozen=True, slots=True)
class ProviderIdentityObservation:
    """Both identity claims, verbatim, from one funded acquisition."""

    symbol: str

    #: The moment of the funded read, from the reading's own provenance.
    captured_at: datetime

    #: The broker's account, exactly as it arrived. Persisted here and
    #: nowhere else — before this stream, half of every contradiction
    #: was unrecordable.
    broker: ProviderIdentityClaim

    #: The vendor's account, exactly as it arrived.
    vendor: ProviderIdentityClaim

    #: What `join_identity` said about these two claims at capture time.
    #: A fact about the capture, never about today.
    standing: IdentityStanding

    #: Raw tenancy fields, exactly as the vendor's payload spelled them,
    #: where it carried them at all. **They infer nothing.** #215
    #: measured the field marking SPCX's tenancy boundary and failing to
    #: mark PARA's, so a raw value is retained for a future ruling to
    #: reason over and no code reads meaning out of it.
    first_trade_date_ms: int | None = None
    ipo_expected_date: str | None = None

    @property
    def stated(self) -> str:
        """One capture, as a reader checks it."""

        return (
            f"{self.captured_at:%Y-%m-%d %H:%M UTC} — "
            f"{self.standing.stated}. {self.broker.stated} {self.vendor.stated}"
        )


#: The finite lifecycle vocabulary. Every sentence a history can produce
#: is one of these three; a test enumerates them and pins that none says
#: "resolved" or "corrected", because no resolution evidence class is
#: uniformly available to earn either word.
_CURRENTLY_DISPUTED = (
    "Currently disputed: the latest capture's claims disagree about what "
    "kind of instrument this is."
)
_PREVIOUSLY_DISPUTED = "Previously disputed; current claims agree."
_NEVER_DISPUTED = "Never disputed across the held captures."

LIFECYCLE_SENTENCES = (_CURRENTLY_DISPUTED, _PREVIOUSLY_DISPUTED, _NEVER_DISPUTED)


@dataclass(frozen=True, slots=True)
class IdentityHistory:
    """Every held observation for one symbol, oldest first.

    A projection over the stream — derived on read, storing nothing,
    deciding nothing. Its one non-trivial sentence is the lifecycle,
    built from the standings alone so the producible vocabulary stays
    finite.
    """

    symbol: str

    #: Chronological: the first funded look first.
    observations: tuple[ProviderIdentityObservation, ...]

    @property
    def latest(self) -> ProviderIdentityObservation | None:
        return self.observations[-1] if self.observations else None

    @property
    def currently_disputed(self) -> bool:
        latest = self.latest

        return latest is not None and latest.standing is IdentityStanding.UNRESOLVED

    @property
    def previously_disputed(self) -> bool:
        """A capture before the latest recorded disagreeing claims.

        This is the fact the stream exists to keep: after the vendor's
        wording drifts into agreement, the earlier dispute stays
        queryable instead of being overwritten into never-happened.
        """

        return any(
            observation.standing is IdentityStanding.UNRESOLVED
            for observation in self.observations[:-1]
        )

    @property
    def lifecycle_stated(self) -> str:
        if self.currently_disputed:
            return _CURRENTLY_DISPUTED

        if self.previously_disputed:
            return _PREVIOUSLY_DISPUTED

        return _NEVER_DISPUTED
