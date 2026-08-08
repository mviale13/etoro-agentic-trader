"""Map a Business Understanding to the playbook that analyses it.

The grounded half of the selector migration in
`docs/architecture/PLAYBOOK_SELECTION.md`, and a pure function like
`classify` and `understand` beside it. It consumes the understanding
object alone — no filing, no provider metadata, no reported industry,
no model — and either fires exactly one earned rule or refuses with the
reason worded. The industry fallback lives elsewhere on purpose: a
module that could see both routes could blend them.

Three rules, because the corpus at quorum has earned three. An
archetype describes economic structure; a playbook describes how the
investment should be analysed; each rule below states why the one
activates the other. A conclusion the tables do not hold is refused by
name — a default would be this platform's own industry taxonomy, which
is the thing being replaced.

**Two tables, because a conclusion is a pair.** A rule may key on the
leading engine alone, or on the leading engine *and its runner-up*.
BNP Paribas earned the second form and forced it: every one of its
segments earns by `services` as well as by something else, so services
covers 103% and leads — while `financial_spread`, the engine that
actually distinguishes the business, covers 89% through the two
segments that are banks. Mapping the primary alone would have sent
every service business to a bank's playbook; the pair says exactly
what was concluded and nothing wider. Pair rules are strictly more
specific, so they are consulted first, and a conclusion matches at
most one entry in each table — the mapping stays unambiguous.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.business_understanding import (
    AlternativeConclusion,
    BusinessUnderstanding,
)
from app.domain.company_archetype import Archetype, stated_archetype
from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.domain.playbook_selection import (
    ContingentSelection,
    NotSelected,
    PlaybookSelection,
    RefusedGrounding,
    SelectedBy,
    SelectionContingency,
)


@dataclass(frozen=True, slots=True)
class GroundedRule:
    """One earned mapping: an archetype, and the frame it activates."""

    kind: PlaybookKind
    rule: str

    #: Why this structure activates this analytical frame.
    why: str


#: The mapping, exactly. Keyed by the archetype the rules concluded;
#: every entry is backed by a company at quorum, and a new entry is
#: earned the same way — never added to improve coverage.
GROUNDED: dict[Archetype, GroundedRule] = {
    Archetype.MANUFACTURER: GroundedRule(
        kind=PlaybookKind.INDUSTRIAL,
        rule="manufacturer-activates-industrial",
        why=(
            "making goods runs through the leading share of measured "
            "revenue, so the questions that decide the case are a "
            "maker's questions — the margin on what is made, the "
            "capital the making consumes, and the cash it returns "
            "through a demand cycle"
        ),
    ),
    Archetype.DIVERSIFIED: GroundedRule(
        kind=PlaybookKind.DIVERSIFIED,
        rule="diversified-activates-diversified-business",
        why=(
            "no single way of earning leads, so no single-mechanism "
            "lens applies; the business is read on the whole of its "
            "ordinary accounts, because no one engine's economics can "
            "stand for the company"
        ),
    ),
}


#: The mapping where a conclusion's *pair* is what activates the frame,
#: keyed by (primary, secondary). Consulted before `GROUNDED`, because a
#: pair is strictly the more specific statement of the same conclusion.
#:
#: One entry, earned by BNP Paribas at a consensus of 11 observations.
#: The narrower key is not caution for its own sake — it is required by
#: the corpus: Caterpillar is a manufacturer with a captive lender, so
#: a rule keyed on "lending is a leading engine" would hand a maker of
#: excavators a bank's playbook. The pair says what was concluded and
#: stops there.
GROUNDED_PAIRS: dict[tuple[Archetype, Archetype], GroundedRule] = {
    (Archetype.SERVICE_BUSINESS, Archetype.LENDER): GroundedRule(
        kind=PlaybookKind.BANK,
        rule="service-business-then-lender-activates-bank",
        why=(
            "the segments that lend run through the larger part of "
            "measured revenue, and services rides alongside every one of "
            "them rather than distinguishing any — so the questions that "
            "decide the case are a bank's questions: the strength of a "
            "balance sheet that is the business rather than a support "
            "for it, what it earns on those assets, and how the lending "
            "grows"
        ),
    ),
}


def rule_for(
    primary: Archetype | None,
    secondary: Archetype | None,
) -> GroundedRule | None:
    """The earned rule this conclusion activates, or nothing at all.

    Pair first, then the leading engine alone. The order is the whole
    of the precedence: a pair rule is a statement about the same
    conclusion with one more fact in it, so where both could fire the
    more specific one is the one that was earned.
    """

    if primary is None:
        return None

    if secondary is not None:
        paired = GROUNDED_PAIRS.get((primary, secondary))

        if paired is not None:
            return paired

    return GROUNDED.get(primary)


def select_grounded(
    understanding: BusinessUnderstanding,
) -> PlaybookSelection | RefusedGrounding:
    """The grounded route: one authoritative selection, or a refusal.

    The migration rule, applied in order. Below quorum nothing here is
    authoritative; an undecided archetype carries its own reason
    through verbatim; a decided conclusion outside the earned table is
    refused by name. Only a quorate understanding whose conclusion the
    table holds produces a selection — and then exactly one, because
    the table is keyed by the single primary the rules concluded.
    """

    archetype = understanding.characteristics

    if not understanding.quorate:
        counted = (
            "1 observation"
            if understanding.observation_count == 1
            else f"{understanding.observation_count} observations"
        )

        return RefusedGrounding(
            because=(
                f"{counted}, below the quorum of {understanding.quorum} — "
                "not a consensus, and nothing decided from it is "
                "authoritative."
            )
        )

    if archetype.primary is None:
        return RefusedGrounding(
            because=archetype.undecided_because
            or (
                "The archetype rules decided nothing for this company, "
                "and no reason travelled with the absence."
            )
        )

    fired = rule_for(archetype.primary, archetype.secondary)

    if fired is None:
        return RefusedGrounding(
            because=(
                f"The rules concluded {archetype.stated!r}, and the "
                "measured corpus has not yet earned a playbook mapping "
                "for it. Serving a default instead would rebuild the "
                "industry taxonomy this selector replaces."
            )
        )

    return PlaybookSelection(
        symbol=understanding.symbol,
        playbook=PLAYBOOKS[fired.kind],
        authoritative=True,
        selected_by=SelectedBy.BUSINESS_UNDERSTANDING,
        selected_because=f"{archetype.stated}: {fired.why}.",
        rule_fired=fired.rule,
        facts_consumed=tuple(
            f"{ruling.rule}: {ruling.concluded} (read: {ruling.read})"
            for ruling in archetype.basis
        ),
        narrowest_agreement=archetype.rests_on,
        alternatives_considered=_not_selected(understanding, fired),
        contingencies=_contingencies(understanding, fired),
        fallback_reason=None,
    )


def _not_selected(
    understanding: BusinessUnderstanding,
    fired: GroundedRule,
) -> tuple[NotSelected, ...]:
    """Every earned playbook that did not fire, and why it did not.

    The reason is always the fired conclusion's own ruling: the fact
    that activated one rule is the fact that kept the other from
    firing, and wording anything else would be a second account.
    """

    concluded = "; ".join(
        ruling.concluded for ruling in understanding.characteristics.basis
    )

    return tuple(
        NotSelected(
            kind=rule.kind,
            activated_by=activates,
            not_selected_because=(
                f"its activating conclusion {activates!r} was not reached: {concluded}"
            ),
        )
        for activates, rule in _earned_rules()
        if rule.kind is not fired.kind
    )


def _earned_rules() -> tuple[tuple[str, GroundedRule], ...]:
    """Every earned rule, each with the conclusion that activates it.

    Both tables, named the way a reader sees a conclusion — so a pair
    rule is listed as "Service business, then lender" rather than as
    the leading engine it shares with a rule that is not this one.
    """

    return (
        *((stated_archetype(primary), rule) for primary, rule in GROUNDED.items()),
        *(
            (stated_archetype(primary, secondary), rule)
            for (primary, secondary), rule in GROUNDED_PAIRS.items()
        ),
    )


def _contingencies(
    understanding: BusinessUnderstanding,
    fired: GroundedRule,
) -> tuple[SelectionContingency, ...]:
    """The understanding's contingencies, carried through the mapping.

    Each observed answer's concluded archetype is looked up through the
    same `rule_for` that fired — never a display string, never a new
    evaluation — and on the answer's *whole* conclusion, pair included.
    An answer whose conclusion is unmapped or undecided selects None:
    settled that way, the grounded route would have refused, which is a
    change of selection too and is marked as one.
    """

    return tuple(
        SelectionContingency(
            claim=contingency.claim,
            agreement=contingency.agreement.stated_majority(),
            consumed=contingency.consumed,
            alternatives=tuple(
                _contingent(alternative, fired)
                for alternative in contingency.alternatives
            ),
        )
        for contingency in understanding.contingencies
    )


def _contingent(
    alternative: AlternativeConclusion,
    fired: GroundedRule,
) -> ContingentSelection:
    """One observed answer, carried through the identical mapping."""

    would_fire = rule_for(alternative.primary, alternative.secondary)

    return ContingentSelection(
        answer=alternative.answer,
        given=alternative.given,
        concludes=alternative.concludes,
        selects=would_fire.kind if would_fire is not None else None,
        changes_selection=(would_fire is None or would_fire.kind is not fired.kind),
    )
