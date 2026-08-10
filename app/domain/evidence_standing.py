"""How far a claim can be trusted — one vocabulary, every evidence family.

Introduced with the token-facts gate and shared from here once protocol
fundamentals became a second family. "Established" must mean the same
thing about a market value and about a protocol's fees, or a surface
showing both side by side is quietly grading them on two scales.

`TokenFactStanding` remains an alias of this enum, so the token-facts
contract frozen after PR #101 is untouched.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceStanding(StrEnum):
    """How far one claim can be trusted, and why.

    The distinction the Zero Fake Numbers contract needs: a surface that
    cannot tell an established fact from an uncorroborated claim will
    print both with the same authority, and the claim will borrow it.
    """

    #: Survived validation: identity confirmed, semantics understood,
    #: internally coherent, and independently corroborated. Agreement
    #: inside one provider is not corroboration.
    ESTABLISHED = "established"

    #: A source reports it and nothing this platform holds can either
    #: corroborate or refute it. Served as the source's claim, never as
    #: a measurement, and consumed by no score.
    CLAIMED = "claimed"

    #: Two sources make coherent, incompatible claims. Neither is
    #: served as fact; both are retained.
    CONFLICTED = "conflicted"

    #: A claim failed validation. The value is not served; the claim
    #: and its rejection reason are retained in the ledger.
    REJECTED = "rejected"

    #: Nobody reports it. Absent evidence is reported as absent.
    ABSENT = "absent"

    @property
    def stated(self) -> str:
        """The standing as a surface labels it, worded here once."""

        return _STANDINGS[self]

    @property
    def serves_value(self) -> bool:
        """Whether a value may be shown beside this standing at all."""

        return self in (EvidenceStanding.ESTABLISHED, EvidenceStanding.CLAIMED)


_STANDINGS = {
    EvidenceStanding.ESTABLISHED: "Established",
    EvidenceStanding.CLAIMED: "Provider claim",
    EvidenceStanding.CONFLICTED: "Sources conflict",
    EvidenceStanding.REJECTED: "Rejected",
    EvidenceStanding.ABSENT: "Not reported",
}
