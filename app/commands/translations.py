"""What every governed provider crossing stands on, and what it reaches.

Read-only, no model, no fetch, and it acquires nothing: the registry is
code, so this surface is a rendering of a constant. It exists because
an inventory nobody can read is an inventory nobody checks, and because
`--markdown` regenerates the document that used to be maintained by
hand beside the code it described.

Nothing here is a score. A warrant says *why we are allowed to read a
provider's field this way*, and the census below is a statement about
this platform's evidence, not about any provider's quality.
"""

from __future__ import annotations

import textwrap

from app.domain.provider_translation import (
    DecisionRelevance,
    TranslationKind,
    TranslationWarrant,
)
from app.domain.provider_translations import (
    TRANSLATIONS,
    awaiting_warrant,
    counted,
    under,
)


class TranslationsCommand:
    async def run(self, markdown: bool = False) -> int:
        if markdown:
            print(render_markdown())

            return 0

        self._render()

        return 0

    def _render(self) -> None:
        census = counted()

        print()
        print("  GOVERNED PROVIDER TRANSLATIONS")
        print(f"  {len(TRANSLATIONS)} crossings from a provider's field to a domain")
        print("  concept, each with the authority it is performed under.")
        print()

        for warrant in TranslationWarrant:
            if warrant not in census:
                continue

            print(f"  {warrant.stated.upper()} — {census[warrant]}")
            print(f"    {warrant.because}")

            for translation in under(warrant):
                print(
                    f"      · {translation.provider_field} "
                    f"({translation.endpoint}) → {translation.domain_concept}"
                )
                print(
                    f"        {translation.answers} · "
                    f"{translation.decision_relevance.stated}"
                )

                if translation.because:
                    for line in textwrap.wrap(translation.because, 66):
                        print(f"        {line}")

            print()

        self._ranked()

    @staticmethod
    def _ranked() -> None:
        """What to repair first, ranked by reach rather than by taste."""

        awaiting = awaiting_warrant()

        gating = [
            item
            for item in awaiting
            if item.decision_relevance is DecisionRelevance.GATES_A_DECISION
        ]

        print("  AWAITING A WARRANT, BY WHAT THEY REACH")
        print(
            f"    {len(awaiting)} of {len(TRANSLATIONS)} crossings rest on this "
            "platform's"
        )
        print(f"    own reading; {len(gating)} of them move a named decision rule.")
        print()

        for position, translation in enumerate(awaiting, start=1):
            print(
                f"    {position:>2}. {translation.domain_concept} "
                f"[{translation.warrant.value}]"
            )
            print(
                f"        {translation.provider} {translation.provider_field} · "
                f"{translation.decision_relevance.stated}"
            )

        print()
        print("  Nothing here is repaired by this surface, and nothing is scored.")
        print()


def render_markdown() -> str:
    """The inventory document, generated from the live registry.

    `docs/architecture/PROVIDER_TRANSLATION_INVENTORY.md` is this
    function's output, and a test asserts the checked-in file matches.
    Editing that document by hand is therefore a test failure — which
    is the point: the audit's table and the adapters' behaviour cannot
    drift apart when one is generated from the other.
    """

    census = counted()

    lines = [
        "# The governed provider translation inventory",
        "",
        "**Generated from `app/domain/provider_translations.py` by**",
        "**`movrvest translations --markdown`. Do not edit by hand —**",
        "**`tests/test_provider_translation_inventory.py` will fail.**",
        "",
        "Every crossing from an external provider's field to a MOVRvest",
        "domain concept, with the four questions it answers and the",
        "authority it is performed under. A warrant is authority for a",
        "translation, never confidence in a value: a plausible number can",
        "stand at ASSUMED, and a reputable provider can supply an UNKNOWN",
        "semantic interpretation.",
        "",
        "## Census",
        "",
        "| Warrant | Count | Means |",
        "|---|---|---|",
    ]

    for warrant in TranslationWarrant:
        if warrant not in census:
            continue

        lines.append(f"| {warrant.stated} | {census[warrant]} | {warrant.because} |")

    lines += [
        "",
        f"Total governed crossings: **{len(TRANSLATIONS)}**.",
        "",
        "## The four questions",
        "",
        "| Kind | Question | Crossings |",
        "|---|---|---|",
    ]

    for kind in TranslationKind:
        count = len([item for item in TRANSLATIONS if kind in item.kinds])

        lines.append(f"| {kind.stated} | {kind.question} | {count} |")

    lines += [
        "",
        "A crossing may answer more than one — `^TNX` needs a semantic and",
        "a unit translation on the same field — so these do not sum to the",
        "total.",
        "",
        "## Every governed crossing",
        "",
        "| Provider | Field | Endpoint | Domain concept | Kinds | Warrant | Reaches |",
        "|---|---|---|---|---|---|---|",
    ]

    for item in sorted(TRANSLATIONS, key=lambda entry: entry.repair_rank):
        lines.append(
            f"| {item.provider} | `{item.provider_field}` | {item.endpoint} "
            f"| {item.domain_concept} | {item.answers} | {item.warrant.stated} "
            f"| {item.decision_relevance.stated} |"
        )

    lines += [
        "",
        "## Awaiting a warrant, ranked by reach",
        "",
        "What a later slice should repair first. Ranked by how far a",
        "crossing reaches — a measured fact — and never by warrant, which",
        "is not a quantity.",
        "",
    ]

    for position, item in enumerate(awaiting_warrant(), start=1):
        lines.append(
            f"{position}. **{item.domain_concept}** — {item.provider} "
            f"`{item.provider_field}`, {item.warrant.stated.lower()}, "
            f"{item.decision_relevance.stated}."
        )

        if item.because:
            lines.append(f"   {item.because}.")

    lines.append("")

    return "\n".join(lines)


async def run(markdown: bool = False) -> int:
    return await TranslationsCommand().run(markdown)
