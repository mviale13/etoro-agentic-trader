"""The owner's capital policy, validated or refused — never defaulted.

#220's ruling made `data/investor_strategy.json` the one authoritative
source for the Capital Action Envelope, and this module is that
authority given a type. Three rules carried from the ruling and from
the measurement that earned it:

**A missing limit refuses; it never defaults.** The mapper on the
decision path silently turns an absent single-position limit into
100.0 — no limit at all. Here, every sizing field is required, and the
absence of any one of them is a worded refusal of the whole policy.

**A draft authorizes nothing.** The strategy file carries a `status`,
and only `active` produces a policy. Capacity facts may still be shown
beside a refusal; a *final envelope* may not.

**The legacy sources are inadmissible.** `config/policy.yaml` remains
the old standalone `decide` path's policy and `app/config.py`'s dormant
risk fields were never consumed by anything — neither is read here, and
a test asserts the imports do not exist. Policy sources are never
silently combined.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum

from app.domain.strategic_allocation import HardLimits, StrategicAllocation


class ReducePolicy(StrEnum):
    """What a REDUCE envelope may compute. v1 has exactly one member."""

    RESTORE_TO_POLICY_CAP = "restore_to_policy_cap"


#: The strategy statuses this loader recognises at all. Anything else
#: is refused by name rather than treated as one of these.
ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class CapitalPolicy:
    """The validated v1 capital policy, with its provenance.

    Every percentage is 0–100, matching the strategy file's own
    convention. The dormant `app/config.py` family expresses fractions;
    that unit clash is one of the reasons it is inadmissible here.
    """

    starter_max_total_position_pct: float
    standard_initial_position_pct: float
    max_add_weight_change_pct: float
    max_single_position_pct: float
    max_crypto_pct: float
    target_cash_pct: float
    minimum_cash_pct: float
    price_max_age_minutes: float
    portfolio_max_age_minutes: float
    maximum_acceptable_drawdown_pct: float
    reduce_policy: ReducePolicy

    #: The security-risk maximum total positions — #234's owner ruling.
    #: Each is an explicit, separately named value even where its number
    #: equals an existing course limit, because no field may secretly
    #: serve two meanings. All three are required: a missing one refuses
    #: the whole policy exactly as every sizing field does.
    security_risk_high_max_total_pct: float
    security_risk_severe_max_total_pct: float
    security_risk_unmeasured_max_total_pct: float

    #: The owner's strategic allocation: four targets totalling 100%,
    #: each inside its own operating range, validated as one plan.
    #: Carried so allocation guidance and the funding gate read the
    #: same policy — and required, because a policy without it is the
    #: state that rendered 0/0/0/5.
    allocation: StrategicAllocation

    #: Where this policy came from and which exact decision-bearing
    #: values it carried — the pair travels with every envelope.
    source: str
    version: str

    def __post_init__(self) -> None:
        percentages = {
            "starter_max_total_position_pct": self.starter_max_total_position_pct,
            "standard_initial_position_pct": self.standard_initial_position_pct,
            "max_add_weight_change_pct": self.max_add_weight_change_pct,
            "max_single_position_pct": self.max_single_position_pct,
            "max_crypto_pct": self.max_crypto_pct,
            "target_cash_pct": self.target_cash_pct,
            "minimum_cash_pct": self.minimum_cash_pct,
            "maximum_acceptable_drawdown_pct": self.maximum_acceptable_drawdown_pct,
            "security_risk_high_max_total_pct": self.security_risk_high_max_total_pct,
            "security_risk_severe_max_total_pct": (
                self.security_risk_severe_max_total_pct
            ),
            "security_risk_unmeasured_max_total_pct": (
                self.security_risk_unmeasured_max_total_pct
            ),
        }

        for name, value in percentages.items():
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} is not a finite number")

            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{name} is outside 0..100")

        if not (
            self.starter_max_total_position_pct
            <= self.standard_initial_position_pct
            <= self.max_single_position_pct
        ):
            raise ValueError(
                "the ruling requires STARTER <= STANDARD_INITIAL <= MAX_SINGLE"
            )

        if self.max_add_weight_change_pct > self.max_single_position_pct:
            raise ValueError("the ruling requires MAX_ADD_WEIGHT_CHANGE <= MAX_SINGLE")

        for name, value in (
            ("price_max_age_minutes", self.price_max_age_minutes),
            ("portfolio_max_age_minutes", self.portfolio_max_age_minutes),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive number")

        if self.maximum_acceptable_drawdown_pct <= 0:
            raise ValueError("maximum_acceptable_drawdown_pct must be positive")

        # The security-risk ceilings must order: the harsher the reading,
        # the smaller the room. An unmeasured reading is capped no looser
        # than a HIGH one, because missing evidence must never buy a
        # larger envelope than measured evidence.
        if (
            self.security_risk_severe_max_total_pct
            > self.security_risk_high_max_total_pct
        ):
            raise ValueError(
                "the ruling requires SECURITY_RISK_SEVERE <= SECURITY_RISK_HIGH"
            )

        if (
            self.security_risk_unmeasured_max_total_pct
            > self.security_risk_high_max_total_pct
        ):
            raise ValueError(
                "the ruling requires SECURITY_RISK_UNMEASURED <= SECURITY_RISK_HIGH"
            )

        # One hard-limit authority, enforced rather than trusted. The
        # allocation's ranges were validated against `limits`, and the
        # envelope funds against `minimum_cash_pct` / `max_crypto_pct`.
        # If those ever came from two places, this refuses by name — it
        # does not pick whichever number it likes better.
        if self.allocation.limits != self.hard_limits:
            raise ValueError(
                "the allocation was validated against a different hard limit "
                "than the envelope funds against: allocation states minimum "
                f"cash {self.allocation.limits.minimum_cash_pct:g}% and "
                f"maximum crypto {self.allocation.limits.maximum_crypto_pct:g}%, "
                f"the policy states {self.minimum_cash_pct:g}% and "
                f"{self.max_crypto_pct:g}%"
            )

    @property
    def hard_limits(self) -> HardLimits:
        """The two allocation limits that block an action.

        The single authority: the CIO's guidance, the operating-range
        validation and the envelope's funding room all read this, so a
        change to the owner's strategy moves all three together or
        moves none of them.
        """

        return HardLimits(
            minimum_cash_pct=self.minimum_cash_pct,
            maximum_crypto_pct=self.max_crypto_pct,
        )

    @property
    def cash_floor_pct(self) -> float:
        """The hard minimum-cash limit, and only that.

        **This was `max(target, minimum)`**, which turned whichever
        cash number happened to be larger into a floor under every
        deployment — so the 25% strategic *destination* blocked capital
        the investor's own plan permits. The owner's ruling of
        2026-08-24 separates the two: a target is where the account is
        heading, an operating range is tactical latitude, and only a
        hard limit blocks an action.

        So funding room is measured above the hard floor. The target
        does not vanish — it is what the allocation guidance reports
        the account against — it simply stops gating.
        """

        return self.minimum_cash_pct


@dataclass(frozen=True, slots=True)
class CapitalPolicyReading:
    """A validated policy, or the worded refusal of one — never both.

    The ComparisonBasis discipline applied to policy: the two shapes
    are enforced at construction, so a reading that claims a policy and
    a refusal at once cannot exist.
    """

    policy: CapitalPolicy | None = None
    refused_because: str = ""

    def __post_init__(self) -> None:
        held = self.policy is not None
        refused = bool(self.refused_because.strip())

        if held == refused:
            raise ValueError(
                "a policy reading carries exactly one of: a policy, a refusal"
            )


#: The exact fields the version hash covers — the decision-bearing set,
#: in one place, so a hash change always means a policy change and a
#: cosmetic edit (a note, a name) never moves it.
DECISION_BEARING_FIELDS = (
    "starter_max_total_position_pct",
    "standard_initial_position_pct",
    "max_add_weight_change_pct",
    "max_single_position_pct",
    "max_crypto_pct",
    "target_cash_pct",
    "minimum_cash_pct",
    "price_max_age_minutes",
    "portfolio_max_age_minutes",
    "maximum_acceptable_drawdown_pct",
    "reduce_policy",
    "security_risk_high_max_total_pct",
    "security_risk_severe_max_total_pct",
    "security_risk_unmeasured_max_total_pct",
)


def policy_version(values: dict[str, object]) -> str:
    """A deterministic hash of the normalized decision-bearing values."""

    canonical = {
        name: (float(value) if isinstance(value, (int, float)) else str(value))
        for name, value in values.items()
        if name in DECISION_BEARING_FIELDS
    }

    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
