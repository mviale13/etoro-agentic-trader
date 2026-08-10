"""Which investment questions a token is asked, and which it is not.

Two readings of the same layer. With a symbol it shows one security:
the archetype and what grounds it, the questions with their
applicability and their evidence, the declines with their reasons, and
each mapped entity's value chain from use to the token. Without one it
shows the corpus as a matrix — the roadmap view, where a column of
*evidence insufficient* is a list of things worth acquiring and a column
of *not applicable* is a list of things that would be wrong to.

Read-only, like every surface in this phase: it asks the stores what
they hold and stops. No provider is called, no model is asked, nothing
is stored, and nothing here is an answer.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.crypto_playbook import CryptoPlaybook, QuestionCell
from app.domain.crypto_questions import QuestionApplicability
from app.domain.evidence_standing import EvidenceStanding
from app.domain.token_value_flow import ValueChain
from app.services.crypto_playbook_service import CryptoPlaybookService

_CELL_MARK = {
    QuestionCell.ASK: "ASK",
    QuestionCell.ASK_EVIDENCE_INSUFFICIENT: "ask?",
    QuestionCell.NOT_APPLICABLE: "n/a",
    QuestionCell.UNDETERMINED: "—",
}


class CryptoPlaybookCommand:
    def run(self, symbol: str | None = None) -> int:
        service = CryptoPlaybookService()

        if symbol is None:
            _render_matrix(service)
            return 0

        normalized = symbol.upper().strip()

        playbook = service.established(normalized, AssetClass.CRYPTO)

        if playbook is None:
            print(f"{normalized} — no crypto playbook: this is not a digital asset.")
            return 1

        _render(playbook)

        return 0


# ── one security ────────────────────────────────────────────────────


def _render(playbook: CryptoPlaybook) -> None:
    assignment = playbook.assignment
    definition = assignment.definition

    print(f"{playbook.symbol} — {definition.name}")
    print(f"  {assignment.confidence.stated}")
    print()
    print(_wrap(definition.explanation, "  "))
    print()
    print(_wrap(f"Why this archetype: {assignment.because}", "  "))

    if assignment.rests_on:
        print()
        print("  Rests on")
        for line in assignment.rests_on:
            print(_wrap(f"- {line}", "    "))

    if assignment.does_not_establish:
        print()
        print("  Does not establish")
        for line in assignment.does_not_establish:
            print(_wrap(f"- {line}", "    "))

    if assignment.alternatives:
        print()
        print("  Considered and not chosen")
        for alternative in assignment.alternatives:
            print(
                _wrap(
                    f"- {alternative.archetype.value}: "
                    f"{alternative.not_chosen_because}",
                    "    ",
                )
            )

    if assignment.not_classified_from:
        print()
        print("  Held here and not used to classify")
        for line in assignment.not_classified_from:
            print(_wrap(f"- {line}", "    "))

    print()
    print("  Read through")
    for capability in assignment.capabilities:
        print(_wrap(f"- {capability.label}: {capability.reads}", "    "))

    if definition.unmodelled:
        print()
        print("  Its own questions, which this platform has not modelled")
        for line in definition.unmodelled:
            print(_wrap(f"- {line}", "    "))

    _render_questions(playbook)
    _render_chains(playbook)


def _render_questions(playbook: CryptoPlaybook) -> None:
    print()
    print("  Questions")

    for item in playbook.coverage:
        if item.cell is QuestionCell.NOT_APPLICABLE:
            continue

        print()
        print(f"    [{item.cell.stated}] {item.question.label}")
        print(_wrap(item.question.asks, "      "))

        if item.applicability.state is QuestionApplicability.UNDETERMINED:
            print(_wrap(item.applicability.because, "      "))
            continue

        for covered in item.covered:
            if covered.is_met:
                entity = f" [{covered.entity}]" if covered.entity else ""
                source = f", {covered.source}" if covered.source else ""
                stated = (
                    f"{covered.stated} ({covered.standing.stated}{source})"
                    if covered.stated
                    else f"{covered.standing.stated}{source}"
                )

                print(
                    _wrap(
                        f"· {covered.demand.stated}: {stated}{entity}",
                        "      ",
                    )
                )
            else:
                print(_wrap(f"· needs: {covered.demand.stated}", "      "))

    declined = playbook.declined

    if declined:
        print()
        print("  Not asked of this kind of asset")

        for item in declined:
            print()
            print(f"    {item.question.label}")
            print(_wrap(item.applicability.because, "      "))


def _render_chains(playbook: CryptoPlaybook) -> None:
    if playbook.unmapped_because:
        print()
        print("  Value chain")
        print(_wrap(playbook.unmapped_because, "    "))
        return

    if not playbook.chains:
        return

    print()
    print("  Value chain — one per economic entity, never summed")

    for chain in playbook.chains:
        _render_chain(chain)


def _render_chain(chain: ValueChain) -> None:
    print()
    print(f"    {chain.entity.name} ({chain.entity.kind.stated})")
    print(_wrap(chain.entity.measures, "      "))

    for link in chain.links:
        if link.standing.serves_value and link.value is not None:
            window = f" / {link.window}" if link.window else ""
            stated = f"{_money(link.value)}{window} ({link.standing.stated})"
        else:
            stated = link.availability.stated

        print(f"      {link.stage.label:<22} {stated}")

        if link.methodology:
            print(_wrap(f'source: "{link.methodology}"', "        "))

    print()
    print(f"      Mechanism: {chain.mechanism.stated}")
    print(_wrap(chain.because, "        "))


# ── the corpus ──────────────────────────────────────────────────────


def _render_matrix(service: CryptoPlaybookService) -> None:
    symbols = sorted(ASSIGNMENTS)

    playbooks = [
        playbook
        for symbol in symbols
        if (playbook := service.established(symbol, AssetClass.CRYPTO)) is not None
    ]

    print("Crypto investment questions — applicability across the corpus")
    print()
    print("  ASK   applies, and something established answers it")
    print("  ask?  applies, and nothing established answers it yet")
    print("  n/a   the wrong question for this kind of asset")
    print("  —     no archetype established, so applicability is unknown")
    print()

    width = 26
    header = "".join(f"{playbook.symbol:>8}" for playbook in playbooks)
    print(f"{'':<{width}}{header}")

    print(
        f"{'archetype':<{width}}"
        + "".join(
            f"{_abbreviate(playbook.assignment.archetype.value):>8}"
            for playbook in playbooks
        )
    )
    print()

    for index, item in enumerate(playbooks[0].coverage):
        row = "".join(
            f"{_CELL_MARK[playbook.coverage[index].cell]:>8}" for playbook in playbooks
        )
        print(f"{item.question.label:<{width}}{row}")

    print()
    _render_counts(playbooks)


def _render_counts(playbooks: list[CryptoPlaybook]) -> None:
    print("Where the evidence stands, over every question that applies")
    print()

    for playbook in playbooks:
        asked = playbook.asked

        established = sum(
            1 for item in asked if item.best_standing is EvidenceStanding.ESTABLISHED
        )
        claimed = sum(
            1 for item in asked if item.best_standing is EvidenceStanding.CLAIMED
        )
        conflicted = sum(1 for item in asked if item.conflicts)
        absent = sum(
            1 for item in asked if item.best_standing is EvidenceStanding.ABSENT
        )

        print(
            f"  {playbook.symbol:<6} asked {len(asked):>2}   "
            f"established {established:>2}   claimed {claimed:>2}   "
            f"conflicted {conflicted:>2}   absent {absent:>2}   "
            f"declined {len(playbook.declined):>2}"
        )


def _abbreviate(archetype: str) -> str:
    return "".join(part[0] for part in archetype.split("_")).upper()


def _money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    if value >= 1_000:
        return f"${value / 1_000:,.1f}k"

    return f"${value:,.0f}"


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + (" " * 2 if text.startswith(("-", "·")) else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return CryptoPlaybookCommand().run(symbol)
