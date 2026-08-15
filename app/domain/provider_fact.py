"""A claim, promoted under a named translation, carrying what it is worth.

The join between what a provider reported (`ProviderClaim`) and what
this platform is allowed to read it as (`ProviderTranslation`). A
consumer holding one of these can answer *is this established, or am
I looking at an assumption* without reading a line of adapter code —
which is the property the audit found missing everywhere.

Two rules the measurements forced, both enforced here rather than
promised in prose:

**Incompatible claims cannot collapse.** Promoting two claims that
disagree about one field returns an unresolved fact, not a winner.
Yahoo's `dividendYield` is the specimen: `0.0517` from quoteSummary
and `5.17` from `/v7/finance/quote` are not one number that needs
rounding, they are two claims about what the field means, and the
compatibility value that flows on says so.

**Magnitude never establishes a unit.** A domain representation may
*reject* a value — a yield of 5.17 cannot be a decimal ratio — but it
may never *convert* one, because "5.17 looks like percent points"
is a guess about Yahoo's intent, and a guess is what got us here. So
a rejection is recorded and the value is served exactly as claimed,
with the conflict visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.provenance import Provenance
from app.domain.provider_claim import ClaimAbsence, ProviderClaim, disagreeing
from app.domain.provider_translation import (
    DomainRepresentation,
    ProviderTranslation,
    TranslationWarrant,
)

#: Ratios this platform documents as decimal fractions. A value at or
#: above this bound cannot be one, which is a statement about *our*
#: convention and never about the provider's intent.
_IMPLAUSIBLE_RATIO = 1.0


@dataclass(frozen=True, slots=True)
class ProviderFact:
    """One domain value, with the authority it actually stands on.

    `value` is the compatibility value — exactly what the pre-boundary
    adapter would have produced, so that no decision moves in this
    slice. What is new is everything beside it: which claims produced
    it, under which translation, and whether that translation
    establishes anything at all.
    """

    #: The domain concept this became — "ValuationSnapshot.forward_pe".
    concept: str

    translation: ProviderTranslation

    #: Every claim that spoke to this concept. More than one where
    #: providers or endpoints disagreed; empty for nothing reported.
    claims: tuple[ProviderClaim, ...]

    #: The value the domain consumes today. `None` where nothing was
    #: reported, or where the legacy type could carry an absence.
    value: Any = None

    #: True where the claims disagree about what the field carries and
    #: this platform holds nothing that could settle it.
    unresolved: bool = False

    #: Set where a value failed its declared domain representation.
    #: The value still flows (compatibility), the failure is recorded.
    representation_rejected: bool = False

    #: Set where the promoted value is not a measurement at all but a
    #: number the legacy type forced in place of an absence.
    compatibility_substitution: ClaimAbsence | None = None

    def __post_init__(self) -> None:
        if self.compatibility_substitution is not None and self.value is None:
            raise ValueError(
                "a compatibility substitution exists to record a value "
                "standing in for an absence; without a value there is "
                "nothing to disclose"
            )

    @property
    def warrant(self) -> TranslationWarrant:
        """The authority this value stands on.

        A disagreement between claims is not a weaker version of the
        translation's warrant — it is the state in which no reading is
        warranted at all, so it answers UNKNOWN whatever the registry
        says about the field in the ordinary case.
        """

        if self.unresolved or self.representation_rejected:
            return TranslationWarrant.UNKNOWN

        return self.translation.warrant

    @property
    def establishes_domain_fact(self) -> bool:
        """Whether a consumer may treat this as an established fact."""

        return self.warrant.establishes_domain_fact and not self.substituted

    @property
    def substituted(self) -> bool:
        """Whether this number stands in for an absence."""

        return self.compatibility_substitution is not None

    @property
    def reported(self) -> bool:
        return any(claim.reported for claim in self.claims)

    @property
    def acquisition(self) -> Provenance | None:
        """When this platform asked, from the claims beneath it."""

        readings = [claim.acquisition for claim in self.claims]

        return min(readings, key=lambda item: item.observed_at) if readings else None

    @property
    def observation(self) -> Provenance | None:
        """The provider's own observation time, where one was supplied.

        Absent for every equity-path fact today, and absent is what it
        says — the request time sitting in `acquisition` is never
        promoted into this answer.
        """

        supplied = [
            claim.observation for claim in self.claims if claim.observation is not None
        ]

        return min(supplied, key=lambda item: item.observed_at) if supplied else None

    @property
    def stated(self) -> str:
        """What this fact honestly claims, worded here once."""

        if self.substituted and self.compatibility_substitution is not None:
            return (
                f"{self.concept} is served as {self.value!r} for compatibility; "
                f"nothing was measured — {self.compatibility_substitution.stated}."
            )

        if self.unresolved:
            readings = " and ".join(
                f"{claim.raw_value!r} ({claim.endpoint})"
                for claim in self.claims
                if claim.reported
            )

            return (
                f"{self.concept}: the provider's own schemas disagree — "
                f"{readings}. No reading is established."
            )

        if self.representation_rejected:
            expected = (
                self.translation.representation.stated
                if self.translation.representation is not None
                else "its declared representation"
            )

            return (
                f"{self.concept} is served as {self.value!r}, which cannot be "
                f"{expected}. What the provider intended is not established."
            )

        if not self.reported:
            reason = next(
                (claim.absence.stated for claim in self.claims if claim.absence),
                "nothing was reported",
            )

            return f"{self.concept} is absent: {reason}."

        return f"{self.concept} = {self.value!r} — {self.translation.warrant.stated}."


def promote(
    *,
    concept: str,
    translation: ProviderTranslation,
    claims: tuple[ProviderClaim, ...],
    value: Any = None,
    compatibility_substitution: ClaimAbsence | None = None,
) -> ProviderFact:
    """Turn claims into the domain fact they are worth, and no more.

    `value` is supplied by the adapter so the compatibility path stays
    byte-identical — this function decides *standing*, never
    arithmetic. It performs no conversion, because a conversion needs
    a warrant and this layer holds none.
    """

    unresolved = disagreeing(claims)

    rejected = False

    if (
        not unresolved
        and value is not None
        and translation.representation is DomainRepresentation.DECIMAL_RATIO
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and abs(float(value)) >= _IMPLAUSIBLE_RATIO
    ):
        # The invariant may say "this is not a decimal ratio". It may
        # not say "therefore Yahoo meant percentage points" — that is
        # the provider's semantics, and inferring them from magnitude
        # is precisely the repair this boundary refuses.
        rejected = True

    return ProviderFact(
        concept=concept,
        translation=translation,
        claims=claims,
        value=value,
        unresolved=unresolved,
        representation_rejected=rejected,
        compatibility_substitution=compatibility_substitution,
    )


@dataclass(frozen=True, slots=True)
class ProviderFactLedger:
    """Every promoted fact behind one security's provider evidence.

    The reporting surface of this boundary: a reader asks it what is
    established, what rests on an assumption, and what is a
    compatibility value standing in for an absence — without opening
    an adapter.
    """

    symbol: str
    facts: tuple[ProviderFact, ...]

    def fact(self, concept: str) -> ProviderFact | None:
        return next((item for item in self.facts if item.concept == concept), None)

    @property
    def established(self) -> tuple[ProviderFact, ...]:
        return tuple(item for item in self.facts if item.establishes_domain_fact)

    @property
    def unresolved(self) -> tuple[ProviderFact, ...]:
        return tuple(item for item in self.facts if item.unresolved)

    @property
    def substituted(self) -> tuple[ProviderFact, ...]:
        """Facts whose number stands in for an absence."""

        return tuple(item for item in self.facts if item.substituted)

    def under(self, warrant: TranslationWarrant) -> tuple[ProviderFact, ...]:
        return tuple(item for item in self.facts if item.warrant is warrant)

    @property
    def stated(self) -> str:
        """The one-line summary a surface leads with."""

        return (
            f"{len(self.facts)} provider facts for {self.symbol}: "
            f"{len(self.established)} established, "
            f"{len(self.unresolved)} unresolved, "
            f"{len(self.substituted)} substituted for an absence"
        )
