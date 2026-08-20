"""The Capital Action Envelope: display-only, normalized, deterministic.

What a maximum portfolio-weight change the investor *might consider* —
never an order, a currency amount, a target, an instruction, or an
automatic action. The #220 ruling's v1, encoded:

**Capacity is not position size.** `PortfolioCapacity` is the hard
room under cash and concentration constraints; the envelope is the
smaller owner-policy-bound consideration inside it, and the final
figure is a minimum over ceilings — which is what makes every required
monotonicity property true by construction: a gap can only add a
ceiling, and removing evidence can never increase permitted capital.

**Conviction is not an input.** It appears in no signature here, so a
conviction change cannot alter any envelope field.

**Liquidity is unmeasured for equities** and is disclosed as exactly
that on every envelope — never manufactured from market capitalization,
company size or fame, and never described as adequate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.domain.capital_policy import CapitalPolicy
from app.domain.market_snapshot import MarketQuote

#: Disclosed verbatim on every envelope. No equity volume, ADV or
#: spread figure exists on this platform, so no liquidity ceiling can
#: be computed — and an undisclosed hole would read as adequacy.
LIQUIDITY_UNMEASURED = (
    "Liquidity is unmeasured for equities on this platform; nothing here "
    "describes it as adequate."
)


class QualityAuthority(StrEnum):
    """Whose account the quality score rests on — #219's invisible axis."""

    GROUNDED = "grounded"
    PROVIDER = "provider"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class PortfolioObservation:
    """How recently eToro answered — or why that cannot be established.

    **This is a response-receipt clock, and it is named as one.** The
    reading aged here is `last_sync`, the moment MOVRvest received a
    successful account response. It is not the moment eToro observed
    the account: no eToro route states one (the read-only MCP
    acceptance measured this on 2026-08-20 — `ClientPortfolio` carries
    thirteen top-level properties and none is temporal).

    So this gate answers *how long since the broker last answered us*,
    which is an operational availability question and a useful one. It
    does **not** answer how old eToro's underlying account state is,
    and no sentence built from it may imply that it does.

    Ageing `last_sync` rather than the Brain-assembly moment still
    matters: assembly happens immediately before every read, so gating
    on it was vacuous by construction.
    """

    fresh: bool = False
    as_of: str = ""
    refused_because: str = ""

    def __post_init__(self) -> None:
        if self.fresh == bool(self.refused_because.strip()):
            raise ValueError(
                "a portfolio observation is exactly one of: fresh, or refused in words"
            )

        if self.fresh and not self.as_of.strip():
            raise ValueError(
                "a fresh portfolio observation names its response receipt time"
            )


def portfolio_observation_for(
    *,
    last_sync: datetime | None,
    policy: CapitalPolicy,
    now: datetime,
) -> PortfolioObservation:
    """Age the account-response receipt time against the policy limit.

    An absent, naive or future timestamp refuses rather than being
    replaced by the evaluation clock — substituting `now` for a missing
    receipt time is exactly the vacuous gate this function exists to
    prevent. A refused observation may still carry `as_of` where the
    receipt time itself was readable (the stale case), so the render can
    say *when eToro last answered* while refusing to build on it.
    """

    if last_sync is None:
        return PortfolioObservation(
            refused_because=(
                "no eToro account response has been recorded with a receipt "
                "time, so how recently the broker answered cannot be "
                "established"
            )
        )

    if last_sync.tzinfo is None or last_sync.utcoffset() is None:
        return PortfolioObservation(
            refused_because=(
                "the eToro account response's receipt time carries no "
                "timezone, so its age cannot be established"
            )
        )

    if last_sync > now:
        return PortfolioObservation(
            refused_because=(
                "the eToro account response's receipt time is in the "
                "future, which is a clock fault rather than a fresh reading"
            )
        )

    stated = (
        "eToro account response received at "
        f"{last_sync.astimezone(UTC):%Y-%m-%d %H:%M} UTC "
        "(receipt time; eToro states no account observation time)"
    )
    age_minutes = (now - last_sync).total_seconds() / 60.0

    if age_minutes > policy.portfolio_max_age_minutes:
        return PortfolioObservation(
            as_of=stated,
            refused_because=(
                "the last eToro account response was received longer ago "
                f"than the policy's {policy.portfolio_max_age_minutes:g}-minute "
                "limit"
            ),
        )

    return PortfolioObservation(fresh=True, as_of=stated)


@dataclass(frozen=True, slots=True)
class PriceObservation:
    """The exact security's own quote verdict — never a neighbour's.

    Freshness, provenance and the figure all belong to the one quote
    resolved for the decision's own symbol. A market-wide reading or a
    fresh price for another symbol authorizes nothing here, which is
    why this type exists instead of a boolean a caller could derive
    from either.
    """

    fresh: bool = False
    as_of: str = ""
    refused_because: str = ""

    def __post_init__(self) -> None:
        if self.fresh == bool(self.refused_because.strip()):
            raise ValueError(
                "a price observation is exactly one of: fresh, or refused in words"
            )

        if self.fresh and not self.as_of.strip():
            raise ValueError("a fresh price observation names its quote's provenance")


def price_observation_for(
    *,
    symbol: str,
    quote: MarketQuote | None,
    policy: CapitalPolicy,
    now: datetime,
) -> PriceObservation:
    """The exact quote's own authority to price this symbol, or a refusal.

    Reads only the quote's own fields — its symbol, its price, its
    reading's `observed_at` and `last_known` — and words `as_of` from
    that reading's own provenance. Degradation is not age: a last-known
    reading refuses however recent it is, because the source did not
    answer and recency cannot repair that.
    """

    wanted = symbol.upper().strip()

    if quote is None:
        return PriceObservation(
            refused_because=(
                f"no market quote for {wanted} was acquired this cycle, "
                "and another security's price cannot stand in for it"
            )
        )

    if quote.symbol.upper().strip() != wanted:
        return PriceObservation(
            refused_because=(
                f"the resolved quote names {quote.symbol.upper().strip()}, "
                f"not {wanted}, and another security's price cannot stand "
                "in for it"
            )
        )

    if quote.reading is None:
        return PriceObservation(
            refused_because=(
                f"the {wanted} quote carries no provenance, and an undated "
                "price cannot pass a freshness gate"
            )
        )

    if quote.reading.last_known:
        return PriceObservation(
            refused_because=(
                f"the price source did not answer and the {wanted} figure "
                "is a last-known reading; recency cannot repair a degraded "
                "reading"
            )
        )

    observed_at = quote.reading.observed_at

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        return PriceObservation(
            refused_because=(
                f"the {wanted} price's observation time carries no "
                "timezone, so its age cannot be established"
            )
        )

    if observed_at > now:
        return PriceObservation(
            refused_because=(
                f"the {wanted} price's observation time is in the future, "
                "which is a clock fault rather than a fresh reading"
            )
        )

    if not math.isfinite(quote.price) or quote.price <= 0:
        return PriceObservation(
            refused_because=(
                f"the {wanted} quote's price is not a positive finite "
                "figure, and no envelope rests on an unusable price"
            )
        )

    if quote.reading.age(now).total_seconds() / 60.0 > policy.price_max_age_minutes:
        return PriceObservation(
            refused_because=(
                f"the {wanted} price is older than the policy's "
                f"{policy.price_max_age_minutes:g}-minute limit"
            )
        )

    return PriceObservation(fresh=True, as_of=quote.reading.stated(now))


class EnvelopeKind(StrEnum):
    """What the envelope object is saying. Finite, and each worded apart."""

    #: A maximum upward weight change the investor might consider.
    UPWARD_BOUNDED = "upward_bounded"

    #: Eligible, and the portfolio has no room — the binding constraint
    #: is named, and nothing follows about the company.
    ZERO_CAPACITY = "zero_capacity"

    #: The minimum reduction that would restore the policy cap. A
    #: floor: never a maximum, a target, or an exit judgment.
    REDUCTION_FLOOR = "reduction_floor"

    #: A REDUCE course on a holding that is not overweight — v1 has no
    #: policy-derived magnitude for a thesis-driven reduction.
    NO_POLICY_MAGNITUDE = "no_policy_magnitude"

    #: No capital envelope is available, for the named reason. The
    #: existing non-capital course stands unchanged.
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class PortfolioCapacity:
    """The hard maximum room, or the worded refusal to compute one.

    Refusal here is about the *portfolio reading* — the broker did not
    answer, the total is unusable, the snapshot is stale — and is kept
    apart from the envelope's own refusals so a broker outage is never
    read as an empty account.
    """

    funding_room_pct: float | None = None
    concentration_room_pct: float | None = None
    capacity_pct: float | None = None
    current_weight_pct: float | None = None
    refused_because: str = ""

    def __post_init__(self) -> None:
        held = self.capacity_pct is not None
        refused = bool(self.refused_because.strip())

        if held == refused:
            raise ValueError("capacity carries exactly one of: a ceiling, a refusal")

    @property
    def binding(self) -> str:
        if self.capacity_pct is None:
            return ""

        if (self.funding_room_pct or 0.0) <= (self.concentration_room_pct or 0.0):
            return "the cash floor (funding room)"

        return "the single-position concentration cap"


def capacity_for(
    *,
    policy: CapitalPolicy,
    total_value: float | None,
    cash_pct: float | None,
    current_weight_pct: float | None,
    portfolio: PortfolioObservation,
    broker_answered: bool,
) -> PortfolioCapacity:
    """The hard room for one security, or a refusal in the reading's words.

    `funding_room = max(0, cash_weight − max(target_cash, minimum_cash))`
    `concentration_room = max(0, max_single − current_weight)`
    `capacity = min(funding_room, concentration_room)`

    A broker that did not answer, an unusable total, an unusable
    snapshot clock, an unreadable cash allocation or an unresolved held
    weight each refuse — an absent reading is never converted to zero,
    because zero is a measured empty account and that is a different
    statement. The freshness verdict arrives as the broker snapshot's
    own aged timestamp, so its refusal keeps that reading's words.
    """

    if not broker_answered:
        return PortfolioCapacity(
            refused_because=(
                "the broker did not answer, and an unanswered account is not "
                "an empty one"
            )
        )

    if total_value is None or total_value <= 0:
        return PortfolioCapacity(
            refused_because=(
                "the portfolio's total value is unavailable or non-positive, "
                "so no weight can be computed against it"
            )
        )

    if not portfolio.fresh:
        return PortfolioCapacity(refused_because=portfolio.refused_because)

    if cash_pct is None:
        return PortfolioCapacity(
            refused_because=(
                "the account's cash allocation could not be read, and "
                "capacity is refused rather than guessed"
            )
        )

    if current_weight_pct is None:
        return PortfolioCapacity(
            refused_because=(
                "the held weight for this security could not be resolved "
                "from the broker's own rows, and capacity is refused rather "
                "than guessed"
            )
        )

    funding = max(0.0, cash_pct - policy.cash_floor_pct)
    concentration = max(0.0, policy.max_single_position_pct - current_weight_pct)

    return PortfolioCapacity(
        funding_room_pct=round(funding, 4),
        concentration_room_pct=round(concentration, 4),
        capacity_pct=round(min(funding, concentration), 4),
        current_weight_pct=round(current_weight_pct, 4),
    )


@dataclass(frozen=True, slots=True)
class CapitalActionEnvelope:
    """One course's envelope, with everything the ruling says it must name."""

    symbol: str
    course: str
    kind: EnvelopeKind

    policy_source: str
    policy_version: str

    #: Which owner ceiling bounded the evidence side: "starter",
    #: "standard_initial", "max_add_change" — or "" where none applies.
    evidence_ceiling: str = ""

    #: The hard room, where it was computable — carried even beside a
    #: refusal so the raw capacity facts stay visible.
    capacity_ceiling_pct: float | None = None

    #: The final normalized figure: an upward bound, or a reduction
    #: floor. None for refusals, zero-capacity and no-magnitude cases.
    final_pct: float | None = None

    binding_constraint: str = ""
    because: str = ""

    #: The named gaps that capped this envelope, verbatim from the
    #: decision's own missing-evidence ledger. Carried apart from the
    #: canonical rationale, which is not rewritten.
    named_gaps: tuple[str, ...] = ()
    quality_authority: QualityAuthority | None = None
    starter_capped: bool = False

    price_as_of: str = ""
    portfolio_as_of: str = ""

    liquidity: str = LIQUIDITY_UNMEASURED

    def __post_init__(self) -> None:
        """Contradictory shapes cannot be written or accepted from storage.

        The same rule at both doors: a fresh construction and a stored
        line decode through this constructor, so an envelope whose kind
        and fields disagree raises here — and the store's decoder
        already counts a raising line as an unreadable record.
        """

        for label, value in (
            ("capacity ceiling", self.capacity_ceiling_pct),
            ("final figure", self.final_pct),
        ):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(
                    f"an envelope's {label} must be finite and non-negative"
                )

        if self.starter_capped and self.evidence_ceiling != "starter":
            raise ValueError(
                "starter_capped is compatible only with the starter evidence ceiling"
            )

        upward = self.course in ("open", "add")

        if self.kind is EnvelopeKind.UPWARD_BOUNDED:
            if not upward:
                raise ValueError("an upward bound belongs to an open or add course")

            if self.final_pct is None or self.final_pct <= 0:
                raise ValueError("an upward bound carries a positive final figure")

            if self.capacity_ceiling_pct is None:
                raise ValueError("an upward bound names its capacity ceiling")

            if not self.evidence_ceiling:
                raise ValueError("an upward bound names its evidence ceiling")

            if not self.binding_constraint:
                raise ValueError("an upward bound names its binding constraint")
        elif self.kind is EnvelopeKind.ZERO_CAPACITY:
            if not upward:
                raise ValueError("zero capacity belongs to an open or add course")

            if self.final_pct is not None:
                raise ValueError("zero capacity carries no final figure")

            if not self.binding_constraint:
                raise ValueError("zero capacity names its binding constraint")
        elif self.kind is EnvelopeKind.REDUCTION_FLOOR:
            if self.course != "reduce":
                raise ValueError("a reduction floor belongs to a reduce course")

            if self.final_pct is None or self.final_pct <= 0:
                raise ValueError("a reduction floor carries a positive final figure")
        elif self.kind is EnvelopeKind.NO_POLICY_MAGNITUDE:
            if self.course != "reduce":
                raise ValueError("no-policy-magnitude belongs to a reduce course")

            if self.final_pct is not None:
                raise ValueError("no-policy-magnitude carries no final figure")
        elif self.kind is EnvelopeKind.REFUSED:
            if not self.because.strip():
                raise ValueError("a refusal carries its reason in words")

            if self.final_pct is not None:
                raise ValueError("a refusal carries no final figure")

    @property
    def stated(self) -> str:
        """The investor sentence, per kind. Finite shapes, none reusable."""

        if self.kind is EnvelopeKind.REFUSED:
            return (
                f"No capital envelope is available because {self.because}. "
                "The existing non-capital course remains unchanged."
            )

        if self.kind is EnvelopeKind.ZERO_CAPACITY:
            return (
                f"The investment case remains {self.course.upper()}, but the "
                "portfolio currently has no additional capacity because "
                f"{self.binding_constraint} leaves no room."
            )

        if self.kind is EnvelopeKind.REDUCTION_FLOOR:
            return (
                f"At least {self.final_pct:g}% of portfolio weight would need "
                "to be reduced to restore the "
                "single-position cap. This is a compliance floor, not a "
                "target or exit recommendation."
            )

        if self.kind is EnvelopeKind.NO_POLICY_MAGNITUDE:
            return (
                "v1 has no policy-derived reduction magnitude for this "
                "thesis course; the holding is within the single-position "
                "cap."
            )

        if self.starter_capped:
            return (
                f"MOVRvest's course is {self.course.upper()}. Named "
                "uncertainty limits this consideration to at most a "
                f"{self.final_pct:g}% total portfolio weight. The limit "
                "constrains the action, not the company's quality."
            )

        return (
            f"MOVRvest's course is {self.course.upper()}. The current policy "
            f"permits consideration up to a {self.final_pct:g}% portfolio "
            "weight, subject to the binding portfolio-capacity constraint "
            f"({self.binding_constraint})."
        )


def envelope_for(
    *,
    symbol: str,
    course: str,
    policy: CapitalPolicy,
    capacity: PortfolioCapacity,
    named_gaps: tuple[str, ...],
    quality_authority: QualityAuthority,
    hard_floor_passes: bool,
    price: PriceObservation,
    portfolio_as_of: str,
    drawdown_depth_pct: float | None,
    is_equity: bool,
) -> CapitalActionEnvelope:
    """The v1 envelope for one OPEN, ADD or REDUCE course.

    Deterministic; conviction is not a parameter and cannot become one
    without changing this signature, which is the test's hook. Every
    ceiling is a minimum, so information can only preserve or reduce
    the result — the ruling's monotonicity, by construction. The price
    input is the exact security's own quote verdict, so a refusal here
    keeps that quote's words and a market-wide reading has no way in.
    """

    def refused(because: str) -> CapitalActionEnvelope:
        return CapitalActionEnvelope(
            symbol=symbol,
            course=course,
            kind=EnvelopeKind.REFUSED,
            policy_source=policy.source,
            policy_version=policy.version,
            capacity_ceiling_pct=capacity.capacity_pct,
            because=because,
            named_gaps=named_gaps,
            quality_authority=quality_authority,
            price_as_of=price.as_of,
            portfolio_as_of=portfolio_as_of,
        )

    if not is_equity:
        # Crypto remains outside the equity envelope: its own gate
        # family, its own policy cap, and pretending one contract
        # covers both would blur which rules bound the action.
        return refused("crypto remains outside the equity capital envelope")

    if course == "reduce":
        # REDUCE stays available through drawdown and does not consult
        # the upward-side gates: its v1 magnitude is compliance
        # arithmetic over the held weight alone.
        if capacity.current_weight_pct is None:
            return refused(capacity.refused_because or "the held weight is unknown")

        # Branch on the figure the envelope will carry: the constructor
        # requires a reduction floor to be positive, so the rounded
        # value decides which shape exists rather than being applied
        # after the choice.
        overweight = round(
            capacity.current_weight_pct - policy.max_single_position_pct, 4
        )

        if overweight > 0:
            return CapitalActionEnvelope(
                symbol=symbol,
                course=course,
                kind=EnvelopeKind.REDUCTION_FLOOR,
                policy_source=policy.source,
                policy_version=policy.version,
                capacity_ceiling_pct=capacity.capacity_pct,
                final_pct=overweight,
                binding_constraint="the single-position policy cap",
                named_gaps=named_gaps,
                quality_authority=quality_authority,
                price_as_of=price.as_of,
                portfolio_as_of=portfolio_as_of,
            )

        return CapitalActionEnvelope(
            symbol=symbol,
            course=course,
            kind=EnvelopeKind.NO_POLICY_MAGNITUDE,
            policy_source=policy.source,
            policy_version=policy.version,
            capacity_ceiling_pct=capacity.capacity_pct,
            named_gaps=named_gaps,
            quality_authority=quality_authority,
            price_as_of=price.as_of,
            portfolio_as_of=portfolio_as_of,
        )

    if course not in ("open", "add"):
        raise ValueError(f"no envelope is defined for the course {course!r}")

    # ── the upward-side refusals, in the ruling's order ─────────────
    if not hard_floor_passes:
        return refused("a hard safety prerequisite is unresolved")

    if capacity.capacity_pct is None:
        return refused(capacity.refused_because)

    if not price.fresh:
        return refused(price.refused_because)

    if drawdown_depth_pct is None:
        # An absent reading is not zero: without a drawdown measurement
        # the loss-budget gate cannot be evaluated, and a gate that
        # cannot be evaluated fails (S5.1's rule, applied to capital).
        return refused(
            "the portfolio's drawdown is unmeasured, so the loss-budget "
            "gate cannot be evaluated"
        )

    if drawdown_depth_pct >= policy.maximum_acceptable_drawdown_pct:
        budget = policy.maximum_acceptable_drawdown_pct

        return refused(
            f"the portfolio is at or beyond its {budget:g}% drawdown "
            "budget; new capital is not considered while it stands"
        )

    # ── the evidence ceiling: STARTER under any named uncertainty ───
    limited = bool(named_gaps) or quality_authority is not QualityAuthority.GROUNDED

    current = capacity.current_weight_pct or 0.0

    if limited:
        ceiling_name = "starter"
        # STARTER is a maximum TOTAL position under named uncertainty:
        # room up to it, never a fresh increment on top of it.
        room = max(0.0, policy.starter_max_total_position_pct - current)
    elif course == "open":
        ceiling_name = "standard_initial"
        room = policy.standard_initial_position_pct
    else:
        ceiling_name = "max_add_change"
        room = policy.max_add_weight_change_pct

    # Branch on the figure the envelope will carry — the constructor
    # requires an upward bound to be positive, so the rounded value
    # decides which shape exists.
    final = round(min(room, capacity.capacity_pct), 4)

    if final <= 0:
        binding = (
            "the STARTER total-position ceiling"
            if limited and room <= capacity.capacity_pct
            else capacity.binding
        )

        return CapitalActionEnvelope(
            symbol=symbol,
            course=course,
            kind=EnvelopeKind.ZERO_CAPACITY,
            policy_source=policy.source,
            policy_version=policy.version,
            evidence_ceiling=ceiling_name,
            capacity_ceiling_pct=capacity.capacity_pct,
            binding_constraint=binding,
            named_gaps=named_gaps,
            quality_authority=quality_authority,
            starter_capped=limited,
            price_as_of=price.as_of,
            portfolio_as_of=portfolio_as_of,
        )

    return CapitalActionEnvelope(
        symbol=symbol,
        course=course,
        kind=EnvelopeKind.UPWARD_BOUNDED,
        policy_source=policy.source,
        policy_version=policy.version,
        evidence_ceiling=ceiling_name,
        capacity_ceiling_pct=capacity.capacity_pct,
        final_pct=final,
        binding_constraint=(
            "the evidence ceiling"
            if room <= capacity.capacity_pct
            else capacity.binding
        ),
        named_gaps=named_gaps,
        quality_authority=quality_authority,
        starter_capped=limited,
        price_as_of=price.as_of,
        portfolio_as_of=portfolio_as_of,
    )
