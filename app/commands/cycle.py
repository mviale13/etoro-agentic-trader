"""One explicit Daily CIO cycle: acquire, decide, record, render.

The cycle spine #217's ruling approved — an explicit command and
nothing else: no scheduler, no daemon, no notifications, no queue.
The two stages are the components that already exist, run once each;
this module adds identity, order and a durable record, never judgment.

**STARTED is on disk before the first network action.** A process
killed anywhere after that leaves a STARTED with no terminal event —
which the next render discloses as interrupted, and which nothing ever
relabels as COMPLETE, FAILED, or "nothing changed".

**The comparison base is the previous cycle's own record.** Page views
still journal decisions (#217; the surface cutover is named follow-on
work, not this slice) — but they write no cycle event, so they cannot
manufacture or mask a change here.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
from app.brain.brain import Brain
from app.domain.asset_class import AssetClass
from app.domain.capital_envelope import (
    CapitalActionEnvelope,
    EnvelopeKind,
    QualityAuthority,
    capacity_for,
    envelope_for,
    portfolio_observation_for,
    price_observation_for,
    security_risk_ceiling_for,
)
from app.domain.capital_policy import CapitalPolicyReading
from app.domain.daily_cycle import (
    NO_ACTION,
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleLog,
    CycleRecord,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    RecordedAllocation,
    RecordedHolding,
    RecordedPortfolio,
    StageOutcome,
    holdings_by_security,
    movement,
    no_action_permitted,
)
from app.domain.market_snapshot import MarketQuote
from app.domain.strategic_allocation import (
    StrategicAllocation,
    portfolio_guidance_for,
)
from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore
from app.repositories.json_event_repository import JsonEventRepository
from app.services.capital_policy_service import CapitalPolicyService
from app.services.market_acquisition_service import MarketAcquisitionService
from app.services.policy_analyzer import PolicyAnalyzer
from app.services.risk_signal_service import RiskSignalService

__all__ = ["run"]


def _failed_stage(name: str, error: Exception) -> CycleStage:
    """A stage failure, worded for the record rather than copied from it.

    Provider exceptions carry URLs, query parameters and sometimes
    credentials. What the durable record needs is which stage failed
    and what kind of failure it was — so the wording is built here from
    the stage's name and the exception's *class*, and the exception's
    own text never reaches the store or the render.
    """

    return CycleStage(
        name=name,
        outcome=StageOutcome.FAILED,
        because=f"the {name} stage failed ({type(error).__name__})",
    )


def _portfolio_weights(
    brain: Brain,
) -> tuple[dict[str, float], float | None, float | None]:
    """Per-symbol weights (percent), cash percent, and the total.

    Holdings are aggregated by stable instrument identity first — the
    broker reports one row per *trade*, and a 20.0% + 0.5% split once
    read as a compliant 20.0% — then keyed by the resolved symbol.
    An unresolved holding contributes no symbol weight and is refused
    downstream rather than guessed.
    """

    portfolio = brain.portfolio
    total = portfolio.total_value

    if total is None or total <= 0:
        return ({}, None, total)

    by_instrument: dict[int, float] = {}
    names: dict[int, str] = {}

    for holding in portfolio.holdings:
        by_instrument[holding.instrument_id] = by_instrument.get(
            holding.instrument_id, 0.0
        ) + (holding.market_value_usd or 0.0)

        if holding.is_resolved:
            names[holding.instrument_id] = holding.symbol.upper().strip()

    weights: dict[str, float] = {}

    for instrument_id, value in by_instrument.items():
        symbol = names.get(instrument_id)

        if symbol:
            weights[symbol] = weights.get(symbol, 0.0) + value / total * 100.0

    return (weights, portfolio.allocation.cash, total)


def _recorded_portfolio(
    brain: Brain,
    weights: dict[str, float],
    cash_pct: float | None,
    total_value: float | None,
    allocation: StrategicAllocation | None = None,
) -> RecordedPortfolio | None:
    """The account as this cycle read it, for a page that may not fetch.

    Built from the same reading the envelope pass already uses, so the
    record and the courses beside it describe one moment rather than
    two. Absence is preserved throughout: an unresolved holding carries
    no weight rather than a zero, and unavailable cash stays unavailable
    (#223).

    **Recorded per security, because that is what the weight measures.**
    The broker reports a position per trade, and `_portfolio_weights`
    already sums those into one share per security — so writing the rows
    unfolded printed the security's whole share beside each partial
    value. On the live account that put BTC on the page twice at 21.9%
    each and read the invested book as 79.3% of an account holding
    44.7%, against 55.3% cash. The fold is `holdings_by_security`, the
    same one the store reads through, and it is also what makes these
    holdings joinable with the per-security courses recorded beside
    them — 17 rows sat next to 14 courses drawn from the same account.
    """

    if total_value is None:
        return None

    portfolio = brain.portfolio

    holdings: list[RecordedHolding] = []

    for holding in portfolio.holdings:
        if not holding.is_resolved:
            continue

        symbol = holding.symbol.upper().strip()

        holdings.append(
            RecordedHolding(
                symbol=symbol,
                # Unrounded: the fold rounds the security's total once,
                # so a security is not the sum of its rounded trades.
                market_value_usd=holding.market_value_usd or 0.0,
                weight_pct=weights.get(symbol),
            )
        )

    allocations: tuple[RecordedAllocation, ...] = ()
    compliant: bool | None = None
    guidance_stated = ""
    guidance_refused = ""

    policy = getattr(brain, "investment_policy", None)

    if policy is not None:
        # Compared here because this is where both halves are in hand.
        # The endpoint stays a pure projection, and the page calculates
        # nothing.
        analysis = PolicyAnalyzer().analyze(portfolio, policy)

        allocations = tuple(
            RecordedAllocation(
                asset=item.asset,
                current_pct=item.current,
                target_pct=item.target,
                difference_pct=item.difference,
            )
            for item in analysis.allocations
        )
        compliant = analysis.compliant

    # The CIO's allocation guidance, composed once — here, during the
    # cycle, from this cycle's own portfolio reading and the owner's
    # active policy. It names no security, sizes nothing and reads no
    # conviction: allocation drift authorizes no trade, and the object
    # has no access to a course through which it could suggest one.
    if allocation is not None and allocations:
        # Read from the allocations just recorded rather than from the
        # portfolio a second time: one reading, one set of figures, and
        # the guidance cannot disagree with the table it sits under.
        current = {item.asset: item.current_pct for item in allocations}

        guidance = portfolio_guidance_for(allocation, current)

        guidance_stated = guidance.stated
        guidance_refused = guidance.refused_because

        by_asset = {item.asset: item for item in guidance.allocations}

        allocations = tuple(
            replace(
                recorded,
                minimum_pct=by_asset[recorded.asset].minimum_pct,
                maximum_pct=by_asset[recorded.asset].maximum_pct,
                standing=by_asset[recorded.asset].standing.value,
                stated=by_asset[recorded.asset].stated,
            )
            if recorded.asset in by_asset
            else recorded
            for recorded in allocations
        )

    return RecordedPortfolio(
        total_value=round(total_value, 2),
        available_cash_usd=portfolio.available_cash_usd,
        cash_pct=cash_pct,
        holdings=holdings_by_security(holdings),
        observed=(
            ""
            if portfolio.last_sync is None
            else (
                "eToro account response received at "
                f"{portfolio.last_sync.astimezone(UTC):%Y-%m-%d %H:%M} UTC "
                "(receipt time; eToro states no account observation time)"
            )
        ),
        allocations=allocations,
        compliant=compliant,
        allocation_guidance=guidance_stated,
        allocation_guidance_refused=guidance_refused,
    )


def _envelope(
    workspace: ExecutiveWorkspace,
    *,
    policy_reading: CapitalPolicyReading,
    brain: Brain,
    weights: dict[str, float],
    cash_pct: float | None,
    total_value: float | None,
    drawdown_pct: float | None,
    quotes: dict[str, MarketQuote],
    established_prices: frozenset[str],
    evaluated_at: datetime,
) -> CapitalActionEnvelope | None:
    """The envelope for one workspace's course, or None for non-capital ones.

    Only the pipeline's own canonical courses open an envelope — the
    course arrives as `workspace.action.kind`, never derived from a
    decision-state string. Conviction is not read here and cannot be:
    `envelope_for` has no parameter it could arrive through.

    Two clocks, and they are different kinds of fact. The price is aged
    from the exact security's own quote, which carries a provider
    observation time. The portfolio is aged from `last_sync`, which is
    **when eToro's account response was received here** — eToro states
    no account observation time, so this gate answers how recently the
    broker answered and never how old the account state is.
    `evaluated_at` is only the moment both ages are measured at.
    """

    # The caller only reaches here with both halves present; the guard
    # keeps the type checker honest and the contract explicit.
    if workspace.action is None or workspace.decision is None:
        return None

    kind = workspace.action.kind.value

    if kind not in ("open", "add", "reduce"):
        return None

    symbol = workspace.decision.symbol.upper().strip()

    if policy_reading.policy is None:
        # A draft, missing or contradictory policy refuses the final
        # envelope; the raw capacity facts stay visible in the render
        # through the refusal's wording.
        return CapitalActionEnvelope(
            symbol=symbol,
            course=kind,
            kind=EnvelopeKind.REFUSED,
            policy_source="investor_strategy.json",
            policy_version="unavailable",
            because=policy_reading.refused_because,
        )

    policy = policy_reading.policy

    portfolio_observed = portfolio_observation_for(
        last_sync=getattr(brain.portfolio, "last_sync", None),
        policy=policy,
        now=evaluated_at,
    )
    price_observed = price_observation_for(
        symbol=symbol,
        quote=quotes.get(symbol),
        policy=policy,
        now=evaluated_at,
    )

    # OPEN's zero is licensed by the course, not by absence: the
    # canonical course says the security is unheld, so a missing broker
    # row is the stated state. ADD and REDUCE act on a holding, and a
    # holding whose weight could not be resolved refuses rather than
    # pretending emptiness.
    current_weight = weights.get(symbol, 0.0) if kind == "open" else weights.get(symbol)

    capacity = capacity_for(
        policy=policy,
        total_value=total_value,
        cash_pct=cash_pct,
        current_weight_pct=current_weight,
        portfolio=portfolio_observed,
        broker_answered=total_value is not None,
    )

    # Whose account the quality score rests on — grounded where the
    # statements governed, provider where the proxy did, unavailable
    # where nothing scored. Carried apart from the canonical rationale.
    if workspace.quality is not None:
        authority = QualityAuthority.GROUNDED
    elif (
        workspace.evidence is not None and workspace.evidence.quality_score is not None
    ):
        authority = QualityAuthority.PROVIDER
    else:
        authority = QualityAuthority.UNAVAILABLE

    # #234: the security's own banded volatility and drawdown, priced
    # under the owner's security-risk policy. The bands are the risk
    # signal's own (`risk-bands@1`), read from the same reading the
    # decision already carries — the envelope bands nothing itself, and
    # a security with no reading is priced as unmeasured rather than
    # passed as calm.
    risk_reading = (
        workspace.evidence.risk_reading if workspace.evidence is not None else None
    )
    bands = RiskSignalService()
    security_risk = security_risk_ceiling_for(
        policy=policy,
        volatility_band=bands.volatility_level(
            risk_reading.volatility if risk_reading is not None else None
        ),
        drawdown_band=bands.drawdown_level(
            risk_reading.max_drawdown if risk_reading is not None else None
        ),
    )

    return envelope_for(
        symbol=symbol,
        course=kind,
        policy=policy,
        capacity=capacity,
        named_gaps=tuple(workspace.decision.missing_evidence),
        quality_authority=authority,
        security_risk=security_risk,
        # A pipeline-produced capital-asking course rests on the one
        # disposition whose gates the #219 measurement showed require
        # the whole six-family floor; a reduction does not consult it.
        hard_floor_passes=True,
        price=price_observed,
        portfolio_as_of=portfolio_observed.as_of,
        drawdown_depth_pct=drawdown_pct,
        is_equity=brain.asset_class_for(symbol) is AssetClass.STOCK,
        # Whether the crypto-native gate admitted a spot price for this
        # token, read from the acquisition's own record of what the
        # store now holds — never from `quotes`, which is the vendor's
        # and holds nothing for a token whose listing was refused.
        # It words the crypto refusal and sizes nothing.
        crypto_price_established=symbol in established_prices,
    )


def new_cycle_id() -> str:
    """Opaque, unique per invocation. Never derived from the clock alone."""

    return uuid.uuid4().hex[:12]


async def run(
    store: DailyCycleStore | None = None,
    acquisition: MarketAcquisitionService | None = None,
    brains: BrainBuilderService | None = None,
    briefings: PortfolioBriefingService | None = None,
    capital_policies: CapitalPolicyService | None = None,
    candidates: int = 0,
) -> int:
    """One cycle. `candidates` is a spend, and it defaults to none.

    Evidencing a watched-but-unheld security costs a fundamentals
    request against a rate-limited provider, and evaluating one costs a
    pipeline pass. So a cycle researches candidates only when asked for
    a budget, and every existing cycle costs exactly what it did before.
    """
    store = store or DailyCycleStore()

    # Yesterday's honesty before today's work: a cycle that started and
    # never ended is disclosed, not silently superseded.
    held = store.log()

    cycle_id = new_cycle_id()
    started = CycleStarted(cycle_id=cycle_id, started_at=datetime.now(UTC))

    # Durable before the first acquisition or network action — the one
    # write a hard kill cannot take back, and the whole reason "started
    # and interrupted" is distinguishable from "never started".
    store.append_started(started)

    stages: list[CycleStage] = []
    asked = priced = 0
    refusals: tuple[str, ...] = ()

    # Which securities the store now holds a price for. Empty until the
    # acquisition says otherwise — a failed acquisition establishes no
    # price, and an envelope must not word one it never read.
    established_prices: frozenset[str] = frozenset()

    # The exact per-security quotes this cycle's acquisition read,
    # keyed by canonical MOVRvest symbol. Empty until the acquisition
    # says otherwise, so a failed batch refuses every envelope in the
    # existing typed words rather than inventing a price.
    #
    # This used to be `brain.market.quotes` — the SPY/QQQ/IWM market
    # strip, a collection that cannot contain a holding — so every
    # capital-asking course ever recorded refused with "no market quote
    # was acquired this cycle" beside its own record saying 26 priced
    # of 26 (the golden-path acceptance's finding 1). The acquisition
    # stage owns the quotes it took; this carries them, verbatim.
    acquired_quotes: dict[str, MarketQuote] = {}

    # ── stage 1: the explicit acquisition, once ─────────────────────
    try:
        acquired = await (acquisition or MarketAcquisitionService()).acquire()
    except Exception as error:
        stages.append(_failed_stage("acquisition", error))
    else:
        asked = len(acquired.securities)
        priced = len(acquired.priced)
        # Two refusals, never one sentence for both. A security nothing
        # priced is unpriced; a security the quote vendor answered about
        # under another instrument's name has a price and no vendor
        # history, and saying "no price came back" about it was false in
        # the cycle that stored an established price for it.
        refusals = (
            *(
                f"{security.symbol}: no price came back"
                for security in acquired.unpriced
            ),
            *(
                f"{security.symbol}: {security.listing_refused}"
                for security in acquired.refused_listings
            ),
        )
        established_prices = frozenset(
            security.symbol.upper().strip() for security in acquired.priced
        )
        acquired_quotes = {
            quote.symbol.upper().strip(): quote for quote in acquired.quotes
        }
        stages.append(CycleStage(name="acquisition", outcome=StageOutcome.RAN))

    # ── stage 2: the canonical decision pass over the active book ───
    decisions: tuple[DecisionSummary, ...] = ()
    recorded_portfolio: RecordedPortfolio | None = None
    evaluated_candidates: tuple[DecisionSummary, ...] = ()

    try:
        brain = await (brains or BrainBuilderService()).build(
            candidate_limit=candidates
        )

        # The moment observation ages are measured at — never any
        # reading's own observation time, which stays the broker's or
        # the quote provider's to state.
        evaluated_at = datetime.now(UTC)

        service = briefings or PortfolioBriefingService(
            pipeline=ExecutivePipeline(
                journal=DecisionJournal(JsonEventRepository(), cycle_id=cycle_id)
            )
        )

        briefing = service.build(brain)
        workspaces = briefing.workspaces if briefing is not None else ()

        # The course comes from `workspace.action` and nowhere else —
        # the pipeline's own ExecutiveAction, carried verbatim. And no
        # security disappears: a workspace whose pass produced no
        # disposition or no course is *refused in words*, named for
        # which half was missing, rather than filtered out of the
        # cycle's account. Nothing manufactures an action and nothing
        # infers one from a decision state.
        carried: list[DecisionSummary] = []

        # The v1 Capital Action Envelope: an owner-policy-bound,
        # display-only weight consideration beside a capital-asking
        # course. Loaded once per cycle; a refused policy still lets
        # capacity facts render, and produces no final envelope.
        policy_reading = (capital_policies or CapitalPolicyService()).reading()
        weights, cash_pct, total_value = _portfolio_weights(brain)

        drawdown = getattr(brain.portfolio, "drawdown", None)
        drawdown_pct = (
            round(drawdown.current_depth * 100.0, 4) if drawdown is not None else None
        )

        # Each envelope resolves the exact security's own quote from
        # this map; no market-wide reading authorizes any of them.
        quotes = acquired_quotes

        for workspace in workspaces:
            if workspace.decision is not None and workspace.action is not None:
                carried.append(
                    DecisionSummary(
                        symbol=workspace.decision.symbol,
                        state=workspace.decision.state.value,
                        rationale=workspace.decision.rationale,
                        conviction=workspace.decision.conviction,
                        conviction_basis=workspace.decision.conviction_basis,
                        # The coverage that conviction was computed
                        # over, carried so a projection can tell whether
                        # two of them share a denominator.
                        conviction_participating=(
                            workspace.decision.conviction_participating
                        ),
                        conviction_expected=workspace.decision.conviction_expected,
                        conviction_absent_families=(
                            workspace.decision.conviction_absent_families
                        ),
                        blocker=workspace.decision.blocker,
                        evidence_as_of=(
                            workspace.decision.evidence_as_of.stated()
                            if workspace.decision.evidence_as_of is not None
                            else ""
                        ),
                        action_kind=workspace.action.kind.value,
                        action_statement=workspace.action.statement,
                        action_because=workspace.action.because,
                        asks_for_something=workspace.action.kind.asks_for_something,
                        envelope=_envelope(
                            workspace,
                            policy_reading=policy_reading,
                            brain=brain,
                            weights=weights,
                            cash_pct=cash_pct,
                            total_value=total_value,
                            drawdown_pct=drawdown_pct,
                            quotes=quotes,
                            established_prices=established_prices,
                            evaluated_at=evaluated_at,
                        ),
                    )
                )
            elif workspace.decision is None:
                refusals = refusals + (
                    f"{workspace.symbol}: the decision pass produced no "
                    "disposition; this constrains what the cycle can say "
                    "and says nothing about the business",
                )
            else:
                refusals = refusals + (
                    f"{workspace.symbol}: the decision pass produced a "
                    "disposition and no course; this constrains what the "
                    "cycle can say and says nothing about the business",
                )

        decisions = tuple(carried)

        recorded_portfolio = _recorded_portfolio(
            brain,
            weights,
            cash_pct,
            total_value,
            # The owner's strategic allocation, from the same reading
            # the envelope's policy came from — one policy, one cycle.
            allocation=(
                policy_reading.policy.allocation
                if policy_reading.policy is not None
                else None
            ),
        )

        # Watched-but-unheld securities, evaluated through the very same
        # pipeline as a holding — so their conviction means what a
        # holding's conviction means, and is comparable with it.
        #
        # Only those actually evaluated are recorded. A cycle run
        # without a candidate budget records none, and an empty tuple
        # says "none were evaluated", never "none were worth holding".
        if candidates > 0:
            held_symbols = {entry.symbol.upper().strip() for entry in decisions}

            wanted = tuple(
                dict.fromkeys(
                    candidate.symbol.upper().strip()
                    for candidate in brain.candidates
                    if candidate.symbol.strip()
                    and candidate.symbol.upper().strip() not in held_symbols
                )
            )[:candidates]

            evaluated_candidates = tuple(
                DecisionSummary(
                    symbol=workspace.decision.symbol,
                    state=workspace.decision.state.value,
                    rationale=workspace.decision.rationale,
                    conviction=workspace.decision.conviction,
                    conviction_basis=workspace.decision.conviction_basis,
                    conviction_participating=(
                        workspace.decision.conviction_participating
                    ),
                    conviction_expected=workspace.decision.conviction_expected,
                    conviction_absent_families=(
                        workspace.decision.conviction_absent_families
                    ),
                    blocker=workspace.decision.blocker,
                    evidence_as_of=(
                        workspace.decision.evidence_as_of.stated()
                        if workspace.decision.evidence_as_of is not None
                        else ""
                    ),
                    action_kind=workspace.action.kind.value,
                    action_statement=workspace.action.statement,
                    action_because=workspace.action.because,
                    asks_for_something=workspace.action.kind.asks_for_something,
                    # A funded candidate's OPEN course is a capital
                    # course, and it gets the same envelope from the
                    # same quote map as a holding's — one contract, one
                    # source of prices. A candidate the cycle never
                    # priced refuses in the existing typed words.
                    envelope=_envelope(
                        workspace,
                        policy_reading=policy_reading,
                        brain=brain,
                        weights=weights,
                        cash_pct=cash_pct,
                        total_value=total_value,
                        drawdown_pct=drawdown_pct,
                        quotes=quotes,
                        established_prices=established_prices,
                        evaluated_at=evaluated_at,
                    ),
                )
                for workspace in service.pipeline.execute_all(
                    symbols=wanted, brain=brain
                )
                if workspace.decision is not None and workspace.action is not None
            )

        stages.append(CycleStage(name="decisions", outcome=StageOutcome.RAN))
    except Exception as error:
        stages.append(_failed_stage("decisions", error))

    # ── status: which stages ran, and nothing about item coverage ───
    ran = {stage.name for stage in stages if stage.outcome is StageOutcome.RAN}

    if "decisions" not in ran or not decisions:
        # No useful decision pass. An acquisition alone fills stores
        # and answers none of the investor's five questions.
        status = CycleStatus.FAILED
    elif "acquisition" in ran:
        status = CycleStatus.COMPLETE
    else:
        status = CycleStatus.PARTIAL

    # The comparison basis, typed and persisted — never a nullable id
    # whose meaning has to be guessed. An incomplete stream refuses the
    # comparison outright: the unreadable or anomalous record may be
    # the actual previous cycle, and a disclosure beside a derived
    # change would not make the change safe.
    previous = held.latest_terminal() if held.is_complete_stream else None

    if status is CycleStatus.FAILED:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED,
            because="no useful decision pass was completed",
        )
    elif not held.is_complete_stream:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED,
            because=(
                "the held cycle stream is incomplete "
                f"({held.unreadable_records} unreadable record(s), "
                f"{held.unsupported_schemas} unsupported-schema record(s), "
                f"{held.lifecycle_anomalies} lifecycle anomaly(ies)), and an "
                "unreadable record may be the actual previous cycle"
            ),
        )
    elif previous is None:
        comparison = ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE)
    else:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.COMPARED,
            prior_cycle_id=previous.cycle_id,
        )

    if comparison.outcome is ComparisonOutcome.COMPARED and previous is not None:
        produced, changed, unchanged = movement(decisions, previous)
    else:
        produced, changed, unchanged = (), (), ()

    by_symbol = {entry.symbol: entry for entry in decisions}

    # Attention: changed dispositions, newly produced courses that ask
    # for something, refusals, and failed required stages — in that
    # order. A newly produced course that asks for nothing is still
    # newly considered, and is reported as that rather than as an
    # action.
    attention = (
        tuple(
            f"{symbol}: now {by_symbol[symbol].state} — {by_symbol[symbol].rationale}"
            for symbol in changed
        )
        + tuple(
            f"{symbol}: {by_symbol[symbol].action_statement} "
            f"({by_symbol[symbol].action_kind})"
            for symbol in produced
            if by_symbol[symbol].asks_for_something
        )
        + refusals
        + tuple(
            f"the {stage.name} stage failed — {stage.because}"
            for stage in stages
            if stage.outcome is StageOutcome.FAILED
        )
    )

    finished = CycleFinished(
        cycle_id=cycle_id,
        finished_at=datetime.now(UTC),
        status=status,
        stages=tuple(stages),
        securities_asked=asked,
        securities_priced=priced,
        refusals=refusals,
        comparison=comparison,
        decisions=decisions,
        newly_produced=produced,
        changed=changed,
        unchanged=unchanged,
        attention=attention,
        portfolio=recorded_portfolio,
        candidates=evaluated_candidates,
    )

    store.append_finished(finished)

    print(render(CycleRecord(started=started, finished=finished), held))

    return 0 if status is not CycleStatus.FAILED else 1


def _course_lines(entry: DecisionSummary) -> list[str]:
    """One course, and its capital envelope where one exists."""

    lines = [
        f"  {entry.symbol}: {entry.state} — {entry.action_statement} "
        f"({entry.action_kind})"
    ]

    envelope = entry.envelope

    if envelope is None:
        return lines

    lines.append(f"      {envelope.stated}")
    lines.append(
        "      policy: "
        f"{envelope.policy_source} @ {envelope.policy_version} · "
        f"evidence ceiling: {envelope.evidence_ceiling or 'n/a'} · "
        f"capacity ceiling: "
        + (
            f"{envelope.capacity_ceiling_pct:g}%"
            if envelope.capacity_ceiling_pct is not None
            else "not computed"
        )
        + " · final: "
        + (f"{envelope.final_pct:g}%" if envelope.final_pct is not None else "none")
    )

    if envelope.binding_constraint:
        lines.append(f"      binding constraint: {envelope.binding_constraint}")

    if envelope.named_gaps:
        lines.append(
            "      named gaps (they cap the action, not the company): "
            + "; ".join(envelope.named_gaps)
        )

    if envelope.quality_authority is not None:
        lines.append(f"      quality authority: {envelope.quality_authority.value}")

    detail = []

    if envelope.price_as_of:
        detail.append(f"price as of {envelope.price_as_of}")

    if envelope.portfolio_as_of:
        detail.append(f"portfolio as of {envelope.portfolio_as_of}")

    if detail:
        lines.append("      " + " · ".join(detail))

    lines.append(f"      {envelope.liquidity}")

    return lines


def render(record: CycleRecord, held_before: CycleLog) -> str:
    """The cycle as the investor reads it. Pure, for the tests.

    Distinguishes, in words that cannot be mistaken for each other:
    completed-and-changed, completed-and-nothing-changed,
    completed-with-gaps, partial, failed — and, from the prior log,
    started-but-never-ended. A failed cycle never says nothing changed;
    a completed one never says the evidence was complete; an absence is
    never a statement about a company; and nothing here calls a past
    dispute resolved.
    """

    lines = ["", f"DAILY CIO CYCLE — {record.cycle_id}", "=" * 60]

    # Disclosure of the stream's own limits and of interrupted runs.
    if not held_before.is_complete_stream:
        lines.append(
            "The held cycle stream is incomplete — "
            f"{held_before.unreadable_records} unreadable record(s), "
            f"{held_before.unsupported_schemas} unsupported-schema record(s), "
            f"{held_before.lifecycle_anomalies} lifecycle anomaly(ies); the "
            "lifecycle shown is derived from the readable ones only."
        )

    for dangling in held_before.dangling:
        lines.append(
            f"A previous cycle ({dangling.cycle_id}) started at "
            f"{dangling.started.started_at:%Y-%m-%d %H:%M UTC} and recorded "
            "no end — it was interrupted. Nothing is known about what it "
            "would have found."
        )

    finished = record.finished

    if finished is None:
        lines.append(
            "This cycle started and has recorded no end — it is interrupted, "
            "and no view of the day is claimed from it."
        )

        return "\n".join(lines)

    lines.append(f"Status: {finished.status.value.upper()}")

    for stage in finished.stages:
        worded = stage.outcome.value + (f" — {stage.because}" if stage.because else "")
        lines.append(f"  {stage.name}: {worded}")

    if finished.status is CycleStatus.FAILED:
        lines.append("")
        lines.append(
            "No useful decision pass was completed, so nothing can be said "
            "about what changed today. This is a failed cycle, not a quiet "
            "one."
        )

        return "\n".join(lines)

    lines.append("")
    lines.append(
        f"Acquisition: {finished.securities_priced} priced of "
        f"{finished.securities_asked} asked."
    )

    if finished.refusals:
        lines.append(
            f"Evidence gaps ({len(finished.refusals)}) — each constrains what "
            "can be said about that security, and says nothing about the "
            "business itself:"
        )
        lines.extend(f"  {refusal}" for refusal in finished.refusals)

    lines.append("")

    comparison = finished.comparison

    if comparison.outcome is ComparisonOutcome.INITIAL_BASELINE:
        lines.append(
            "Initial cycle recorded; no previous completed cycle exists for "
            "change comparison."
        )
        lines.append(
            f"Current courses ({len(finished.decisions)} securities considered):"
        )
        for entry in finished.decisions:
            lines.extend(_course_lines(entry))
    elif comparison.outcome is ComparisonOutcome.REFUSED:
        lines.append(
            f"Change comparison refused: {comparison.because}. No changed, "
            "unchanged or newly-produced classification is claimed for this "
            "cycle."
        )
        lines.append(
            f"Current courses ({len(finished.decisions)} securities considered):"
        )
        for entry in finished.decisions:
            lines.extend(_course_lines(entry))
    else:
        lines.append(
            f"Decisions (against cycle {comparison.prior_cycle_id}): "
            f"{len(finished.decisions)} securities considered — "
            f"{len(finished.newly_produced)} newly produced, "
            f"{len(finished.changed)} changed, "
            f"{len(finished.unchanged)} unchanged."
        )

        by_symbol = {entry.symbol: entry for entry in finished.decisions}

        if finished.changed:
            lines.append("Changed, with the rationale recorded at decision time:")

            for symbol in finished.changed:
                entry = by_symbol[symbol]
                lines.append(f"  {symbol}: now {entry.state} — {entry.rationale}")

        if finished.newly_produced:
            lines.append("Newly considered:")

            for symbol in finished.newly_produced:
                entry = by_symbol[symbol]
                course = (
                    f" — {entry.action_statement} ({entry.action_kind})"
                    if entry.asks_for_something
                    else f" ({entry.state}; its course asks for nothing yet)"
                )
                lines.append(f"  {symbol}{course}")

        if not finished.changed and not finished.newly_produced:
            lines.append("No recommendation changed against the previous cycle.")

    lines.append("")

    if no_action_permitted(finished):
        lines.append(NO_ACTION)
    elif finished.attention:
        lines.append("Consider today:")
        lines.extend(f"  {item}" for item in finished.attention)

    return "\n".join(lines)
