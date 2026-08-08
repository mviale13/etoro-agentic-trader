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

from app.analysts.filing_analysts import (
    filing_balance_sheet,
    filing_cash_flow,
    filing_growth,
    filing_profitability,
    stated_value,
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


class FinancialsCommand:
    def __init__(self, store: FinancialStatementStore | None = None) -> None:
        self._store = store or JsonFinancialStatementStore()

    def run(self, symbol: str) -> int:
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

        _render(measure(normalized, held), held)

        return 0


def _render(
    understanding: FinancialUnderstanding,
    held: dict[StatementKind, FinancialStatementConsensus],
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

    print()
    print("the analysts, on these facts and nothing else")
    print()

    for named, analyst in (
        ("profitability", filing_profitability()),
        ("growth", filing_growth()),
        ("balance sheet", filing_balance_sheet()),
        ("cash flow", filing_cash_flow()),
    ):
        opinion = analyst.analyze(understanding)

        print(
            f"  {named}: {opinion.verdict.value} (confidence {opinion.confidence:.0%})"
        )

        for line in opinion.evidence:
            print(f"    + {line}")

        for line in opinion.uncertainty:
            print(f"    ? {line}")

        print()


def run(symbol: str) -> int:
    return FinancialsCommand().run(symbol)
