"""What the provider actually reported, before anything interprets it.

The smallest typed representation preserving a provider's own words.
It exists because the audit's three failures all destroyed information
*at the crossing*, and no downstream layer could recover it:

- Yahoo's `dividendYield` arrives from two endpoints at two scales.
  Merged into one dict by the client library, the two claims become
  one number and the scale becomes unknowable.
- `eps` may be `trailingEps` or `forwardEps` depending on which key
  the payload happened to carry. The stored record keeps one `eps`
  field, so the corpus cannot be re-classified after the fact.
- Every reading is stamped with the moment MOVRvest asked, because
  that is the only timestamp the adapter ever had — and a request
  time worn as an observation time is a claim about the world that
  nobody made.

A claim fixes that by refusing to forget. It carries the endpoint as
part of its identity, the raw value exactly as it arrived, and the
request time and the provider's own observation time in **separate
fields that never fall back to one another**.

**Nothing here is manufactured.** A provider that declares no unit
gets `declared_unit=None`, not a guess; a provider that states no
observation time gets `provider_observed_at=None`, not the request
time. Absence is the honest answer and the whole reason this object
is worth building.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.domain.provenance import Provenance


class ClaimAbsence(StrEnum):
    """Why a provider supplied no usable value.

    Absence is not one state, and collapsing the five into a single
    `None` — or worse, into `0.0` — is how "acquisition failed" became
    "the security did not move today". Each member is a different fact
    about the world or about this platform, and the momentum signal
    would word all five differently if it could see them.
    """

    #: The provider's payload had no such key at all.
    FIELD_ABSENT = "field_absent"

    #: The key was present and explicitly null.
    REPORTED_NULL = "reported_null"

    #: The provider answered, but with too little to compute the
    #: figure — a price history shorter than the window a change needs.
    INSUFFICIENT_HISTORY = "insufficient_history"

    #: A stored value could not be read back as the type it must be.
    MALFORMED_STORED_VALUE = "malformed_stored_value"

    #: The provider could not be reached, or refused.
    PROVIDER_UNAVAILABLE = "provider_unavailable"

    @property
    def stated(self) -> str:
        return _ABSENCE_LABELS[self]

    @property
    def is_measurement(self) -> bool:
        """Whether this absence says anything about the instrument.

        None of them do. The property exists to be read rather than
        remembered: acquisition failure is not a measurement of zero,
        and neither is a short history.
        """

        return False


_ABSENCE_LABELS = {
    ClaimAbsence.FIELD_ABSENT: "the provider reports no such field",
    ClaimAbsence.REPORTED_NULL: "the provider reported no value",
    ClaimAbsence.INSUFFICIENT_HISTORY: (
        "the provider returned too little history to compute it"
    ),
    ClaimAbsence.MALFORMED_STORED_VALUE: ("the stored reading could not be read back"),
    ClaimAbsence.PROVIDER_UNAVAILABLE: "the provider did not answer",
}


@dataclass(frozen=True, slots=True)
class ProviderClaim:
    """One thing a provider reported, as it reported it.

    Constructed at the adapter, before any conversion, and never
    edited afterwards — a claim that could be revised would stop being
    a record of what was said.
    """

    provider: str

    #: Which endpoint or schema served it. Part of the claim's
    #: identity: two claims for one field name from two endpoints are
    #: two claims, and this field is what keeps them apart.
    endpoint: str

    #: The provider's own field name, spelled exactly as it arrives.
    field: str

    #: When MOVRvest asked. Always known, because we did the asking.
    requested_at: datetime

    #: The value exactly as it arrived — no cast, no scaling, no
    #: rounding. `None` where the provider supplied nothing, in which
    #: case `absence` says which kind of nothing.
    raw_value: Any = None

    #: Which kind of nothing, where there is one.
    absence: ClaimAbsence | None = None

    #: When the *provider* says the figure was true. Almost never
    #: supplied on this platform's equity path, and left absent when
    #: it is not — never defaulted to `requested_at`, which would
    #: manufacture an observation the provider never made.
    provider_observed_at: datetime | None = None

    #: The unit the provider itself declares, where it declares one.
    #: Never inferred from magnitude.
    declared_unit: str | None = None

    #: The vocabulary token the provider itself supplies, where it
    #: does — a currency code, a type name, a category label.
    declared_vocabulary: str | None = None

    def __post_init__(self) -> None:
        if self.raw_value is None and self.absence is None:
            raise ValueError(
                f"{self.provider}'s {self.field} carries no value and no "
                "reason; an unexplained absence is the state that let a "
                "failed acquisition read as a measurement"
            )

        if self.raw_value is not None and self.absence is not None:
            raise ValueError(
                f"{self.provider}'s {self.field} carries both a value and "
                "an absence reason; one of them is not true"
            )

    @property
    def reported(self) -> bool:
        """Whether the provider supplied a value at all."""

        return self.raw_value is not None

    @property
    def key(self) -> tuple[str, str, str]:
        """What identifies this claim's origin: provider, endpoint, field."""

        return (self.provider, self.endpoint, self.field)

    @property
    def acquisition(self) -> Provenance:
        """When this platform asked, as a reading.

        Named `acquisition` rather than `observation` on purpose. The
        existing `Provenance` is exactly right for "who answered and
        when did we ask", which is all the equity path has ever known;
        what it must never be allowed to imply is that the provider
        asserted the figure was true at that moment.
        """

        return Provenance(source=self.provider, observed_at=self.requested_at)

    @property
    def observation(self) -> Provenance | None:
        """The provider's own assertion of when it was true, if any.

        `None` is the honest and overwhelmingly common answer on this
        path. A caller wanting *something* to date the reading by must
        reach for `acquisition` explicitly and thereby say what it is
        using.
        """

        if self.provider_observed_at is None:
            return None

        return Provenance(source=self.provider, observed_at=self.provider_observed_at)

    @property
    def stated(self) -> str:
        """The claim as a ledger prints it, worded here once."""

        if not self.reported:
            reason = self.absence.stated if self.absence is not None else "unknown"

            return (
                f"{self.provider} ({self.endpoint}) reported no {self.field}: {reason}."
            )

        unit = f" {self.declared_unit}" if self.declared_unit else ""

        return (
            f"{self.provider} ({self.endpoint}) reported "
            f"{self.field} = {self.raw_value!r}{unit}."
        )

    @classmethod
    def absent(
        cls,
        *,
        provider: str,
        endpoint: str,
        field: str,
        requested_at: datetime,
        absence: ClaimAbsence,
    ) -> ProviderClaim:
        """A claim recording that nothing was reported, and why."""

        return cls(
            provider=provider,
            endpoint=endpoint,
            field=field,
            requested_at=requested_at,
            absence=absence,
        )


def claims_for_field(
    claims: tuple[ProviderClaim, ...],
    field: str,
) -> tuple[ProviderClaim, ...]:
    """Every claim carrying this field name, whatever endpoint served it.

    The `dividendYield` reader: one field name, two endpoints, two
    scales. A caller asking for "the" claim would get whichever the
    payload merge happened to leave, which is the defect.
    """

    return tuple(claim for claim in claims if claim.field == field)


def disagreeing(claims: tuple[ProviderClaim, ...]) -> bool:
    """Whether these claims carry materially different raw values.

    Compared as reported, without scaling — the point is to notice
    that two endpoints said different things, not to decide which was
    right. Two absences are not a disagreement, and an absence beside
    a value is not one either: that is a provider outage, which
    `ClaimAbsence` already describes.
    """

    reported = [claim.raw_value for claim in claims if claim.reported]

    if len(reported) < 2:
        return False

    first = reported[0]

    return any(value != first for value in reported[1:])
