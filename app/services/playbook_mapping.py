"""Map a Business Understanding to the playbook that analyses it.

The grounded half of the selector migration in
`docs/architecture/PLAYBOOK_SELECTION.md`, and a pure function like
`classify` and `understand` beside it. It consumes the understanding
object alone — no filing, no provider metadata, no reported industry,
no model — and either fires exactly one earned rule or refuses with the
reason worded. The industry fallback lives elsewhere on purpose: a
module that could see both routes could blend them.

Two rules, because the corpus at quorum has earned two. An archetype
describes economic structure; a playbook describes how the investment
should be analysed; each rule below states why the one activates the
other. A conclusion the table does not hold is refused by name — a
default would be this platform's own industry taxonomy, which is the
thing being replaced.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.business_understanding import BusinessUnderstanding
from app.domain.company_archetype import Archetype
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

    fired = GROUNDED.get(archetype.primary)

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
            activated_by=archetype.stated,
            not_selected_because=(
                f"its activating conclusion {archetype.stated!r} was not "
                f"reached: {concluded}"
            ),
        )
        for archetype, rule in GROUNDED.items()
        if rule.kind is not fired.kind
    )


def _contingencies(
    understanding: BusinessUnderstanding,
    fired: GroundedRule,
) -> tuple[SelectionContingency, ...]:
    """The understanding's contingencies, carried through the mapping.

    Each observed answer's concluded archetype is looked up in the same
    table that fired — never a display string, never a new evaluation.
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
                ContingentSelection(
                    answer=alternative.answer,
                    given=alternative.given,
                    concludes=alternative.concludes,
                    selects=(
                        GROUNDED[alternative.primary].kind
                        if alternative.primary in GROUNDED
                        else None
                    ),
                    changes_selection=(
                        alternative.primary not in GROUNDED
                        or GROUNDED[alternative.primary].kind is not fired.kind
                    ),
                )
                for alternative in contingency.alternatives
            ),
        )
        for contingency in understanding.contingencies
    )
