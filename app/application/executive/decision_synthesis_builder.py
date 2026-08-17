"""Compose the conclusion from canonical objects, and invent nothing.

Deterministic and total. Given the same decision, thesis and
understanding it produces the same synthesis, and every string it emits
is either carried through verbatim from a canonical object or is one of
this module's own worded absences. No model is asked, no provider is
called, nothing is scored and the decision is not touched.

The ordering rules are the only judgment here, and they are judgments
about *evidence class*, never about the company: a figure read out of an
audited filing outranks an analyst's reading of market data, and a
condition that names what it would change outranks one that only names
a gap. Which facts exist is the pipeline's business; this decides the
order they are read in.
"""

from __future__ import annotations

from app.domain.business_understanding import BusinessUnderstanding
from app.domain.committee.panel import Panel
from app.domain.decision_state import DecisionState
from app.domain.executive.decision_synthesis import (
    CommitteeUncertainty,
    DecisionSynthesis,
    Deliberation,
    FactOrigin,
    ReviewCondition,
    SynthesisFact,
)
from app.domain.executive_decision import ExecutiveDecision
from app.domain.financial_understanding import FinancialUnderstanding
from app.services.company_understanding_service import CompanyUnderstanding

#: How many facts a part of the conclusion carries.
#:
#: Three for the supporting case, because a reader weighing a
#: recommendation reads the top of a list and stops. Two against,
#: because the opposing case is what an investor is being invited to
#: act on and a long list reads as hedging rather than as candour.
SUPPORTING = 3
OPPOSING = 2
CONDITIONS = 3


def synthesise(
    decision: ExecutiveDecision,
    understanding: CompanyUnderstanding | None = None,
) -> DecisionSynthesis:
    """The decision, stated so an investor can argue with it."""

    established = _established(understanding)

    panel = Panel(opinions=decision.opinions)

    uncertainty = _uncertainty(decision)

    return DecisionSynthesis(
        symbol=decision.symbol,
        state=decision.state,
        conviction=decision.conviction,
        because=_because(decision),
        because_absent=_because_absent(decision),
        despite=_despite(decision, understanding),
        despite_absent=_despite_absent(decision, understanding),
        review_if=_review_if(decision, understanding),
        review_if_absent=_review_if_absent(decision, understanding),
        uncertainty=uncertainty,
        uncertainty_absent=_uncertainty_absent(decision, uncertainty),
        deliberation=_deliberation(decision, panel),
        established=established,
    )


# ── what argues for it ──────────────────────────────────────────────


def _because(decision: ExecutiveDecision) -> tuple[SynthesisFact, ...]:
    """The security's own favourable findings, as the decision recorded them.

    Only `key_strengths`, which the evidence builder already separated
    from the portfolio's strengths and the market's opportunities — the
    ones that are identical under every symbol. Nothing from the
    understanding is promoted into this part: the filing establishes
    what a business *is*, and calling any of it a reason to buy would be
    a polarity judgment nobody made.
    """

    return tuple(
        SynthesisFact(
            statement=statement,
            origin=FactOrigin.ASSESSED,
            committee=_committee_for(decision, statement, supporting=True),
        )
        for statement in decision.key_strengths[:SUPPORTING]
    )


def _because_absent(decision: ExecutiveDecision) -> str | None:
    if decision.key_strengths:
        return None

    return (
        "No finding was recorded as arguing for this security. That is a "
        "gap in what has been read, not a judgment that the case is weak."
    )


# ── what argues against it ──────────────────────────────────────────


def _despite(
    decision: ExecutiveDecision,
    understanding: CompanyUnderstanding | None,
) -> tuple[SynthesisFact, ...]:
    """The strongest facts arguing against the case — things that were read.

    Adverse findings, then a claim the readings disagreed on. A missing
    measurement is deliberately *not* here: not knowing something is not
    a reason against a case, it is the thing that would settle it, and
    it belongs under the conditions for review. Putting it in both
    places printed the identical sentence twice under opposite headings
    and read as two findings when it was one.
    """

    against = [
        SynthesisFact(
            statement=statement,
            origin=FactOrigin.ASSESSED,
            committee=_committee_for(decision, statement, supporting=False),
        )
        for statement in decision.key_risks[:OPPOSING]
    ]

    for narrow in _narrow_support(understanding):
        if len(against) >= OPPOSING:
            break

        against.append(narrow)

    return tuple(against)


def _narrow_support(
    understanding: CompanyUnderstanding | None,
) -> tuple[SynthesisFact, ...]:
    """Established claims the readings did not agree on.

    A conclusion resting on three readings of five is a real reservation
    about the platform's own knowledge, and it is the only kind of
    opposing fact this platform can state as *established* — the
    disagreement was measured.
    """

    if understanding is None or understanding.business is None:
        return ()

    business = understanding.business
    narrowest = business.characteristics.narrowest

    if narrowest is None or narrowest.settled:
        return ()

    archetype = business.characteristics.primary

    if archetype is None:
        return ()

    return (
        SynthesisFact(
            statement=(
                f"Reading this business as {archetype.value} rests on a claim "
                f"{narrowest.agreeing} of {narrowest.readings} readings agreed "
                "on, so the platform's own account of it is not settled."
            ),
            origin=FactOrigin.ESTABLISHED,
        ),
    )


def _despite_absent(
    decision: ExecutiveDecision,
    understanding: CompanyUnderstanding | None,
) -> str | None:
    if _despite(decision, understanding):
        return None

    if decision.missing_evidence:
        return (
            "No adverse finding was recorded about this security. What holds "
            "the case back is what has not been measured, which is listed "
            "below as the condition for reviewing it."
        )

    return (
        "No finding was recorded as arguing against this security. Nothing "
        "here is evidence that no risk exists — only that none was read."
    )


# ── what would change it ────────────────────────────────────────────


def _review_if(
    decision: ExecutiveDecision,
    understanding: CompanyUnderstanding | None,
) -> tuple[ReviewCondition, ...]:
    """Named conditions about this security, strongest first.

    Deliberately not `thesis.invalidation_conditions`. Those are the
    account's weaknesses and the market's risks — the same strings the
    dossier already shows, correctly labelled, as portfolio context, and
    identical under every symbol. Offering them here would answer *what
    would change this decision* with something that is not about the
    company.
    """

    conditions: list[ReviewCondition] = []

    if decision.next_trigger:
        conditions.append(
            ReviewCondition(
                condition=decision.next_trigger,
                origin=FactOrigin.ASSESSED,
            )
        )

    conditions.extend(_contingencies(understanding))

    # Where a measurement is missing, taking it is what would move the
    # case — which makes it a condition for review rather than a fact
    # against the company. This is the only place it appears.
    for statement in decision.missing_evidence:
        if len(conditions) >= CONDITIONS:
            break

        conditions.append(
            ReviewCondition(
                condition=statement,
                origin=FactOrigin.ASSESSED,
                would_change=("Measuring it is what would let this case progress."),
            )
        )

    return tuple(conditions[:CONDITIONS])


def _contingencies(
    understanding: CompanyUnderstanding | None,
) -> tuple[ReviewCondition, ...]:
    """Claims whose settling the other way would change the conclusion.

    The one genuinely company-specific review condition this platform
    computes: the understanding engine already evaluates every narrow or
    unsettled claim against its *observed* answers through the identical
    rules, so a contingency that could conclude differently is a named,
    checked condition under which the platform's own account changes.
    """

    if understanding is None or understanding.business is None:
        return ()

    return tuple(
        ReviewCondition(
            condition=(
                f"{contingency.claim} settles differently — it stands at "
                f"{contingency.agreement.agreeing} of "
                f"{contingency.agreement.readings}"
            ),
            origin=FactOrigin.ESTABLISHED,
            would_change=_would_conclude(contingency),
        )
        for contingency in understanding.business.contingencies
        if contingency.could_change_conclusion
    )


def _would_conclude(contingency: object) -> str | None:
    """What the alternative concludes, in the rules' own words."""

    alternatives = getattr(contingency, "alternatives", ())
    stands = getattr(contingency, "as_it_stands", None)

    for alternative in alternatives:
        if alternative.concludes != stands:
            return (
                f"{alternative.given} readings answered so, and the rules "
                f"then conclude {alternative.concludes} rather than {stands}."
            )

    return None


def _review_if_absent(
    decision: ExecutiveDecision,
    understanding: CompanyUnderstanding | None,
) -> str | None:
    """Say plainly that nothing would trigger a review, where nothing would.

    The honest answer to the question the dossier could not previously
    answer. It names what the thesis does carry, so a reader who sees
    conditions elsewhere on the page knows why they are not here.
    """

    if _review_if(decision, understanding):
        return None

    return (
        "No condition specific to this security is recorded for review. "
        "The conditions listed against the thesis are the account's and "
        "the market's, shown on this page as portfolio context; they "
        "would apply to any security and are not reasons to revisit this "
        "one."
    )


# ── who said it ─────────────────────────────────────────────────────


def _committee_for(
    decision: ExecutiveDecision,
    statement: str,
    *,
    supporting: bool,
) -> str | None:
    """Which committee stood on this finding, where one did.

    Resolved through the decision's own ledger rather than matched on
    wording: the committee recorded a reference, the ledger holds the
    statement that reference addresses, and this only walks between
    them. A statement no committee's remit covers — or a case built
    before opinions were recorded — attributes to nobody, and says so
    by being None rather than by guessing.
    """

    for opinion in decision.opinions:
        refs = opinion.supporting if supporting else opinion.opposing

        if statement in decision.findings.statements_for(refs):
            return opinion.committee

    return None


# ── what is not yet known ───────────────────────────────────────────


def _uncertainty(decision: ExecutiveDecision) -> tuple[CommitteeUncertainty, ...]:
    """Every committee's unresolved uncertainty, attributed and deduplicated.

    Carried through verbatim from the committees. Nothing is reworded
    on the way, so the sentence an investor reads here is the sentence
    the layer that found the gap wrote — two surfaces describing one
    absence differently is how a reader comes to believe there are two.
    """

    seen: set[str] = set()

    attributed: list[CommitteeUncertainty] = []

    for opinion in decision.opinions:
        for item in opinion.uncertainty:
            if item.about in seen:
                continue

            seen.add(item.about)

            attributed.append(
                CommitteeUncertainty(
                    committee=opinion.committee,
                    uncertainty=item,
                )
            )

    return tuple(attributed)


def _uncertainty_absent(
    decision: ExecutiveDecision,
    uncertainty: tuple[CommitteeUncertainty, ...],
) -> str | None:
    """Say plainly that nothing is outstanding, where nothing is.

    Distinguished from *no committee looked*: an empty list under a
    panel that never sat would read as a fully evidenced case, which is
    the most flattering possible misreading of having read nothing.
    """

    if uncertainty:
        return None

    if not decision.opinions:
        return (
            "No committee reviewed this case, so nothing is recorded as "
            "unresolved. That is an absence of review, not a complete "
            "picture."
        )

    return (
        "Every input the committees asked for was measured. Nothing here "
        "says the picture is complete — only that nothing they asked for "
        "is outstanding."
    )


# ── why this conclusion and not the other ───────────────────────────


def _deliberation(
    decision: ExecutiveDecision,
    panel: Panel,
) -> Deliberation | None:
    """The conclusion set against the position that did not carry.

    Composed entirely from counts and from rules already named by the
    committees and the CIO. It states no argument of its own: every
    clause here is either a number of committees, a stance one of them
    recorded, or the decision's own rationale carried through.
    """

    if not panel.spoke:
        return None

    # A conviction is named only where one was reached. Where it was
    # withheld the decision still stands and is still stated — what is
    # absent is the number, and "at conviction None/100" would be the
    # evidence-free precision this withholding exists to remove.
    prevailed = (
        f"The Artificial CIO decided {decision.state.value} at conviction "
        f"{decision.conviction}/100. {decision.rationale}"
        if decision.conviction is not None
        else (
            f"The Artificial CIO decided {decision.state.value}, without "
            f"putting a conviction on it. {decision.rationale}"
        )
    )

    return Deliberation(
        agreement=panel.stated(),
        prevailed=prevailed,
        over=_dissent(decision, panel),
        because=_because_outweighed(decision, panel),
    )


def _dissent(decision: ExecutiveDecision, panel: Panel) -> str | None:
    """The position that did not carry, named with the committee holding it.

    Only a genuine contradiction counts. A positive committee beside a
    neutral one is a difference of degree, and reporting it as a dissent
    would tell an investor there was an argument where there was none.
    """

    if not panel.is_divided:
        return None

    # Which side the decision took, and therefore which side lost.
    #
    # `RECOMMEND` is the only state in which this platform acts on the
    # bullish case; there the dissent is whoever was negative. Every
    # other state declines to act now — including `PREPARE`, which is a
    # case held back rather than a case taken — so the position that did
    # not carry is the positive one. Reading this off
    # `belongs_to_watchlist` named the wrong committee for four of the
    # five states: that property is true for everything but `REJECT`.
    acted_on_the_case = decision.state is DecisionState.RECOMMEND

    against = panel.negative if acted_on_the_case else panel.positive

    if not against:
        return None

    dissenting = against[0]

    stance = dissenting.stance

    return (
        f"The {dissenting.committee} is "
        f"{stance.stated if stance is not None else 'silent'} on this "
        f"security, by rule {dissenting.decided_by}. That position did not "
        "carry, and it is recorded rather than dropped."
    )


def _because_outweighed(decision: ExecutiveDecision, panel: Panel) -> str:
    """Why the prevailing side prevailed — in counts and named rules only.

    The honest answer on this platform is procedural, and it is stated
    as procedural. The Artificial CIO does not weigh committee stances:
    it gates on measured scores, and the committees' positions are the
    evidence beside that judgment rather than an input to it. Writing a
    sentence here that implied the stances had been tallied would
    describe a deliberation that did not happen.
    """

    spoke = len(panel.spoke)

    abstained = len(panel.abstained)

    positions = (
        f"{spoke} committee(s) took a position and {abstained} abstained"
        if abstained
        else f"{spoke} committee(s) took a position"
    )

    if panel.is_divided:
        return (
            f"{positions}, and they disagree. The Artificial CIO does not "
            "count committee stances: it gated on the measured scores, and "
            f"reached {decision.state.value} on the rule stated above. The "
            "dissent is preserved so it can be weighed against that gate "
            "rather than hidden by it."
        )

    return (
        f"{positions}. The Artificial CIO gated on the measured scores "
        f"rather than on those positions, and reached {decision.state.value} "
        "on the rule stated above; the committees' agreement is corroboration, "
        "not the thing that decided."
    )


# ── what the filing establishes ─────────────────────────────────────


def _established(
    understanding: CompanyUnderstanding | None,
) -> tuple[SynthesisFact, ...]:
    """What the company's own filing establishes, marked as unconsumed.

    Carried into the conclusion rather than left further down the page
    because it answers the questions a conclusion is read for — what
    kind of company this is, how it earns, how to read its statements —
    and because the decision above was reached without any of it. Saying
    both at once is the whole point.
    """

    if understanding is None:
        return ()

    facts: list[SynthesisFact] = []

    if understanding.business is not None:
        facts.extend(_business_facts(understanding.business))

    if understanding.financial is not None:
        facts.extend(_financial_facts(understanding.financial))

    return tuple(facts)


def _business_facts(business: BusinessUnderstanding) -> list[SynthesisFact]:
    facts = [SynthesisFact(statement=business.engine, origin=FactOrigin.ESTABLISHED)]

    archetype = business.characteristics.primary

    if archetype is not None:
        facts.append(
            SynthesisFact(
                statement=(
                    f"Its settled facts read as {archetype.value}, over "
                    f"{business.observation_count} readings of its filing."
                ),
                origin=FactOrigin.ESTABLISHED,
            )
        )

    return facts


def _financial_facts(financial: FinancialUnderstanding) -> list[SynthesisFact]:
    facts: list[SynthesisFact] = []

    established = financial.language

    if established is not None and established.markers:
        printed = [marker for marker in established.markers if marker.is_established]

        if printed:
            facts.append(
                SynthesisFact(
                    statement=(
                        f"Its income statement speaks a "
                        f"{established.language.value} financial language."
                    ),
                    origin=FactOrigin.ESTABLISHED,
                )
            )

    for measure in financial.established[:SUPPORTING]:
        facts.append(
            SynthesisFact(
                statement=f"{measure.label}: {measure.stated}",
                origin=FactOrigin.ESTABLISHED,
            )
        )

    return facts
