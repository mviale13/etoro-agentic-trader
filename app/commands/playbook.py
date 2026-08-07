"""Show which playbook analyses a business, and everything that decided it.

The surface of the selector migration: the playbook, then which route
selected it and why, then — on the grounded route — the consensus
claims it rests on, the earned playbooks that did not fire, and every
observed answer that would have selected differently. A fallback
selection is rendered as fully as an authoritative one, because the
question a reader has when the industry route serves is *why the
grounded route did not*, and the refusal is the answer.
"""

from __future__ import annotations

from app.domain.playbook_selection import PlaybookSelection, SelectedBy
from app.services.playbook_selection_service import PlaybookSelectionService


class PlaybookCommand:
    async def run(self, symbol: str) -> int:
        _render(await PlaybookSelectionService().select(symbol))

        return 0


def _render(selection: PlaybookSelection) -> None:
    standing = "authoritative" if selection.authoritative else "not authoritative"

    print(f"{selection.symbol} — {selection.playbook.name} ({standing})")

    if selection.selected_by is SelectedBy.BUSINESS_UNDERSTANDING:
        print(f"  selected from business understanding — rule: {selection.rule_fired}")
    else:
        print("  selected from the reported industry, the pre-existing route")

    print(f"  because {selection.selected_because}")
    print()

    if selection.fallback_reason is not None:
        print("the grounded route refused:")
        print(f"  {selection.fallback_reason}")
        print()

    print("how it is analysed:")
    print(f"  {selection.playbook.explanation}")

    for priority in selection.playbook.priorities:
        print(f"    {priority}")

    for exclusion in selection.playbook.excluded:
        print(f"  declined: {exclusion.analyst.value} — {exclusion.reason}")

    print()

    if selection.facts_consumed:
        print("facts consumed (consensus claims only):")

        for fact in selection.facts_consumed:
            print(f"  {fact}")

        if selection.narrowest_agreement is not None:
            print(f"  resting on {selection.narrowest_agreement}")

        print()
    else:
        print("no consensus claim was consumed; nothing above traces to a filing.")
        print()

    if selection.alternatives_considered:
        print("considered, not selected:")

        for alternative in selection.alternatives_considered:
            print(f"  {alternative.kind.value} — {alternative.not_selected_because}")

        print()

    if not selection.contingencies:
        return

    print("what could change this selection:")

    for contingency in selection.contingencies:
        standing = (
            "consumed as settled"
            if contingency.consumed
            else "excluded — no answer carries a strict majority"
        )
        print(f"  {contingency.claim} — {contingency.agreement} ({standing})")

        for contingent in contingency.alternatives:
            if not contingent.changes_selection:
                selected = "unchanged"
            elif contingent.selects is not None:
                selected = f"would select {contingent.selects.value}"
            else:
                selected = (
                    "would refuse — no earned mapping, and the selection "
                    "would fall back"
                )

            print(
                f"    {contingent.given}× {contingent.answer} → "
                f"{contingent.concludes} → {selected}"
            )

        if not contingency.could_change_selection:
            print(
                "    every observed answer leaves the selection unchanged "
                "— the gap does not bear on it"
            )


async def run(symbol: str) -> int:
    return await PlaybookCommand().run(symbol)
