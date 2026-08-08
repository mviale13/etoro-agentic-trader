"""What the filer's own statements measure, and what the analysts make of it.

The statement stream's `movrvest understanding`: one screen showing the
canonical financial facts a company's filing establishes, the cells each
one was computed from, how firmly each is held — and then the four
financial analysts' answers over exactly those facts and nothing else.

Read-only and free. It derives from what is stored and never observes:
filling a statement quorum is `movrvest observe-statements`, which is
the explicit spend. A statement never observed says so, and that is a
fact about this platform rather than about the company.
"""

from __future__ import annotations

from app.analysts.filing_analysts import stated_value
from app.domain.financial_question import (
    FinancialModel,
    FinancialModelSelection,
    model_for,
)
from app.domain.financial_statement_consensus import (
    FinancialStatementConsensus,
    statement_consensus_of,
)
from app.domain.financial_statements import STATEMENT_NAMES, StatementKind
from app.domain.financial_understanding import FinancialUnderstanding
from app.repositories.financial_statement_store import (
    FinancialStatementStore,
    JsonFinancialStatementStore,
)
from app.services.financial_engine import measure
from app.services.financial_questions import (
    answer_questions,
    answered,
    inapplicable,
    unanswerable,
)
from app.services.playbook_selection_service import PlaybookSelectionService


class FinancialsCommand:
    def __init__(
        self,
        store: FinancialStatementStore | None = None,
        selection: PlaybookSelectionService | None = None,
    ) -> None:
        self._store = store or JsonFinancialStatementStore()
        self._selection = selection or PlaybookSelectionService()

    async def run(self, symbol: str, model: FinancialModel | None = None) -> int:
        normalized = symbol.upper().strip()

        held = {
            kind: statement_consensus_of(observations)
            for kind in StatementKind
            if (observations := self._store.latest(normalized, kind))
        }

        if not held:
            print(f"{normalized} — no statement has been read for this security.")
            print()
            print(
                "Nothing about the company follows from that. "
                f"`movrvest observe-statements {normalized}` reads one."
            )
            return 1

        if model is None:
            # The business playbook is asked what company this is; the
            # financial model follows from it until evidence earns a
            # divergence. Two classifications, one route between them.
            playbook = (await self._selection.select(normalized)).playbook.kind
            governing = model_for(playbook)
        else:
            governing = FinancialModelSelection(
                model=model,
                from_playbook=None,
                because="asked for explicitly, for inspection",
            )

        _render(measure(normalized, held), held, governing)

        return 0


def _render(
    understanding: FinancialUnderstanding,
    held: dict[StatementKind, FinancialStatementConsensus],
    governing: FinancialModelSelection,
) -> None:
    print(f"{understanding.symbol} — what its own statements measure")
    print()
    print(understanding.source)
    print(f"read: {understanding.reading.source}")

    missing = tuple(
        kind for kind in StatementKind if kind not in understanding.statements
    )

    if missing:
        # Named rather than counted: which statement is absent decides
        # which measures are absent, and an investor reading a gap is
        # owed the reason rather than a total.
        print(
            "  not yet observed: "
            + ", ".join(STATEMENT_NAMES[kind] for kind in missing)
        )

    if not understanding.quorate:
        print(
            f"  {understanding.observation_count} of the "
            f"{understanding.quorum} observations this platform wants "
            "before calling anything settled — every measure below is at "
            "that width."
        )

    for kind, consensus in held.items():
        caveat = consensus.provenance_caveat()

        if caveat is not None:
            print(f"  PROVENANCE UNCERTAIN ({STATEMENT_NAMES[kind]}): {caveat}")

    print()
    print("measured")

    for established in understanding.established:
        support = established.support

        print(f"  {established.label}: {stated_value(established)}")
        print(f"    from: {established.stated}")

        if support is not None:
            print(
                f"    narrowest figure beneath it: {support.agreeing} of "
                f"{support.readings} readings agree"
            )

    if not understanding.established:
        print("  nothing — every measure below says why.")

    print()
    print("not established")

    for absent in understanding.not_established:
        print(f"  {absent.label}: {absent.absent_because}")

    answers = answer_questions(governing.model, understanding)

    print()
    print(f"financial interpretation model: {governing.model.value}")
    print(f"  {governing.because}")
    print()
    print("  meaningful and answered")

    for answer in answered(answers):
        print(
            f"    {answer.question.value}: {answer.verdict} "
            f"(confidence {answer.confidence or 0:.0%})"
        )
        print(f"      asks: {answer.asks}")

        for line in answer.evidence:
            print(f"      + {line}")

        for line in answer.gaps:
            print(f"      ? {line}")

    if not answered(answers):
        print("    none")

    print()
    print("  meaningful, not yet answerable from established facts")

    for answer in unanswerable(answers):
        print(f"    {answer.question.value}: {answer.because}")

    if not unanswerable(answers):
        print("    none")

    print()
    print(f"  not applicable under the {governing.model.value} model")

    for answer in inapplicable(answers):
        print(f"    {answer.question.value}: {answer.because}")

        for demand in answer.needs:
            # An acquisition demand, not a missing threshold: naming what
            # would answer the question is how every other gap on this
            # platform becomes the next slice.
            print(f"      would need: {demand}")

    if not inapplicable(answers):
        print("    none")

    print()


async def run(symbol: str, model: FinancialModel | None = None) -> int:
    return await FinancialsCommand().run(symbol, model)
