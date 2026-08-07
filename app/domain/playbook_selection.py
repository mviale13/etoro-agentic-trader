"""Which playbook analyses this business, and everything that decided it.

The record of one selection under the migration rule in
`docs/architecture/PLAYBOOK_SELECTION.md`. Two routes can produce it and
they never blend: the grounded route consumes a quorate
`BusinessUnderstanding` and nothing else, and marks its selection
authoritative; the industry route is the pre-existing selector serving
as recorded fallback, consuming no consensus claim at all — its
`facts_consumed` is empty by invariant, not by omission.

Uncertainty travels with the selection the way it travels with the
understanding: the narrowest claim beneath the conclusion is worded
beside the playbook, and every observed minority answer is mapped
through the identical rules and marked with whether it would have
selected differently. A selection that would flip under a 2/5 answer
says so where the playbook is named, never below the fold.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.playbook import InvestmentPlaybook, PlaybookKind


class SelectedBy(StrEnum):
    """Which selector produced the result. Exactly one ever did."""

    #: The grounded route: quorate understanding, one rule fired.
    BUSINESS_UNDERSTANDING = "business_understanding"

    #: The pre-existing route: the provider-reported industry, serving
    #: because the grounded route refused — never alongside it.
    REPORTED_INDUSTRY = "reported_industry"


@dataclass(frozen=True, slots=True)
class NotSelected:
    """A playbook the mapping holds and did not select, with the reason.

    Only playbooks the corpus has earned appear here — the point is to
    answer "why not the other one?", and the answer is always the fired
    conclusion's own ruling, because the fact that activated one rule is
    the fact that kept the other from firing.
    """

    kind: PlaybookKind

    #: The archetype conclusion that would have activated it.
    activated_by: str

    not_selected_because: str


@dataclass(frozen=True, slots=True)
class ContingentSelection:
    """What one observed answer would have selected, through the rules."""

    #: The observed answer, verbatim.
    answer: str

    #: How many observations gave it.
    given: int

    #: What the archetype rules conclude with that answer settled.
    concludes: str

    #: What the mapping then selects — None where the conclusion is
    #: unmapped or undecided, in which case the selection would have
    #: fallen back rather than chosen differently.
    selects: PlaybookKind | None

    #: Whether this answer, settled, would change the selection.
    changes_selection: bool


@dataclass(frozen=True, slots=True)
class SelectionContingency:
    """One narrow or unsettled claim, mapped through to the selection.

    The understanding's contingency, carried one level further: not
    only what the rules would conclude at each observed answer, but
    what this selector would select. Observed answers only, verbatim —
    the no-synthesis rule reaches the selection layer intact.
    """

    #: The claim, in the same words the consensus uses.
    claim: str

    #: Its agreement, worded with the count.
    agreement: str

    #: Whether the claim participates in the standing conclusion at
    #: all — an excluded claim was not resolved, and cannot control the
    #: selection as it stands.
    consumed: bool

    alternatives: tuple[ContingentSelection, ...]

    @property
    def could_change_selection(self) -> bool:
        """Whether any observed answer would select differently."""

        return any(alternative.changes_selection for alternative in self.alternatives)


@dataclass(frozen=True, slots=True)
class PlaybookSelection:
    """One playbook selection, and the full account of it."""

    symbol: str

    playbook: InvestmentPlaybook

    #: Whether this selection may steer anything. True only on the
    #: grounded route: quorate understanding, exactly one rule fired.
    authoritative: bool

    selected_by: SelectedBy

    #: Why this playbook, in one sentence — the structural fact and the
    #: analytical frame it activates, or the honest statement that the
    #: reported industry chose it.
    selected_because: str

    #: The mapping rule that fired. None on the fallback route, which
    #: runs no mapping rule.
    rule_fired: str | None

    #: The consensus claims the selection rests on, worded — each one a
    #: ruling the archetype engine fired, auditable back to the filing.
    #: Empty on the fallback route by invariant: the industry selector
    #: consumes no consensus claim, and listing none is the proof.
    facts_consumed: tuple[str, ...]

    #: What the conclusion beneath this selection rests on — quorum and
    #: narrowest consumed claim, worded with its count. None on
    #: fallback, where no conclusion was consumed.
    narrowest_agreement: str | None

    #: The earned playbooks that did not fire, each with why not.
    alternatives_considered: tuple[NotSelected, ...]

    #: Every narrow or unsettled claim, mapped through to what it would
    #: have selected.
    contingencies: tuple[SelectionContingency, ...]

    #: The grounded route's refusal, verbatim, where it refused. None
    #: exactly when the selection is authoritative.
    fallback_reason: str | None

    @property
    def could_change(self) -> bool:
        """Whether any observed answer would select differently."""

        return any(
            contingency.could_change_selection for contingency in self.contingencies
        )


@dataclass(frozen=True, slots=True)
class RefusedGrounding:
    """The grounded route declining, with the reason.

    A first-class outcome, not an error. The reason travels verbatim
    into the fallback selection's `fallback_reason`, so the reader of a
    fallback always knows why the grounded route did not serve.
    """

    because: str
