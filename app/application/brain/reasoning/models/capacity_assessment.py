"""Capacity reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CapacityAssessment:
    """
    How much room this account has to act, measured against its policy.

    Every figure here is a comparison between something the broker reported
    and something the investor stated. A term that cannot be measured is
    None and named in `unmeasured`, never scored — room nobody could
    measure and room measured at nothing are opposite findings.

    Headroom figures are served signed. A largest position over its limit
    is a negative headroom, which is a measurement of a breach, not an
    error to clamp away.
    """

    #: Cash as the broker reports it, and as the policy wants it. The
    #: actual share is None where the broker stated no cash figure, and
    #: the reason is named in `unmeasured`.
    cash_actual_pct: float | None
    cash_target_pct: float | None

    #: The share of the account that is cash the policy does not want held
    #: as cash — the capital available to fund a new position without
    #: selling an existing one.
    funding_room_pct: float | None
    funding_room_usd: float | None

    #: The single-position limit, the holding closest to it, and the signed
    #: distance between them in percentage points of the account.
    single_position_limit_pct: float | None
    largest_position: str | None
    largest_position_pct: float | None
    single_position_headroom_pct: float | None

    #: The policy's crypto ceiling and the signed room under it. None while
    #: any of the account is unclassified: a ceiling compared against a
    #: partly-identified portfolio understates what is already held.
    crypto_limit_pct: float | None
    crypto_actual_pct: float | None
    crypto_headroom_pct: float | None

    #: Terms the platform cannot currently measure, named rather than scored.
    unmeasured: tuple[str, ...] = field(default_factory=tuple)
