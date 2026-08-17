"""Re-examine stored statement readings against the filings they came from.

The operator half of targeted supersession. Read-only by default: it
classifies every stored reading and prints what it found, and changes
nothing. `--supersede` is the explicit maintenance action that records
the withdrawals.

It costs a fetch per company, asks no model, and spends nothing. Nothing
here reads a score, a band or a factor — see `app.services.statement_audit`
for the rule and the test that pins it.
"""

from __future__ import annotations

import glob
import os
from collections import Counter

from app.domain.financial_statements import StatementKind
from app.domain.primary_source import PrimarySourceUnavailable
from app.infrastructure.evidence_root import evidence_path
from app.providers.primary_source_provider import PrimarySourceResolver
from app.repositories.financial_statement_store import (
    FinancialStatementStore,
    JsonFinancialStatementStore,
)
from app.services.statement_audit import (
    AuditVerdict,
    ObservationRuling,
    audit_observation,
)


class StatementAuditCommand:
    def __init__(
        self,
        store: FinancialStatementStore | None = None,
        sources: PrimarySourceResolver | None = None,
    ) -> None:
        self._store = store or JsonFinancialStatementStore()
        self._sources = sources or PrimarySourceResolver()

    def run(self, symbol: str | None, supersede: bool) -> int:
        symbols = [symbol.upper().strip()] if symbol else self._stored_symbols()

        if not symbols:
            print("No statement readings are stored, so there is nothing to audit.")
            return 1

        print(
            "Statement audit — every stored reading against the filing it was "
            "read from."
        )
        print(
            "Read-only; nothing is withdrawn."
            if not supersede
            else "Superseding: refuted readings will lose authority and stay stored."
        )
        print()

        tally: Counter[AuditVerdict] = Counter()
        withdrawn = 0

        for name in symbols:
            rulings = self._audit(name)

            if rulings is None:
                continue

            for ruling in rulings:
                tally[ruling.verdict] += 1

            _render(name, rulings)

            if supersede:
                withdrawn += self._record(name, rulings)

        print()
        print("corpus:", "  ".join(f"{v.value}={n}" for v, n in sorted(tally.items())))

        if supersede:
            print(f"readings newly superseded: {withdrawn}")
        elif any(verdict.supersedes for verdict in tally):
            print(
                "Nothing was changed. Re-run with --supersede to record these "
                "withdrawals."
            )

        return 0

    # ── the work ────────────────────────────────────────────────────

    def _audit(self, symbol: str) -> tuple[ObservationRuling, ...] | None:
        try:
            source, provider = self._sources.resolve(symbol)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            print(f"{symbol}: not audited — {unavailable}")
            print()
            return None

        held = [
            (position, observation)
            for position, observation in enumerate(self._entry(symbol, source.key))
        ]

        if not held:
            return ()

        return tuple(
            audit_observation(observation, document, symbol, source.key, position)
            for position, observation in held
        )

    def _entry(self, symbol: str, key: str) -> tuple:  # type: ignore[type-arg]
        """Every reading of this filing, in the store's own order.

        The audit addresses readings by position in the entry, so it
        reads the entry whole rather than one statement at a time.
        """

        return tuple(
            observation
            for kind in StatementKind
            for observation in self._store.read(symbol, key, kind)
        )

    def _record(self, symbol: str, rulings: tuple[ObservationRuling, ...]) -> int:
        refuted = {
            ruling.position: ruling.because() for ruling in rulings if ruling.supersedes
        }

        if not refuted:
            return 0

        key = rulings[0].key

        return self._store.supersede(symbol, key, refuted)

    @staticmethod
    def _stored_symbols() -> list[str]:
        directory = evidence_path("statements")

        return sorted(
            {
                os.path.basename(path).split(".")[0]
                for path in glob.glob(str(directory / "*.json"))
            }
        )


def _render(symbol: str, rulings: tuple[ObservationRuling, ...]) -> None:
    if not rulings:
        print(f"{symbol}: no stored readings.")
        print()
        return

    counted: Counter[AuditVerdict] = Counter(ruling.verdict for ruling in rulings)
    summary = "  ".join(f"{v.value}={n}" for v, n in sorted(counted.items()))

    print(f"{symbol} — {len(rulings)} stored reading(s): {summary}")

    reasons: dict[str, int] = {}

    for ruling in rulings:
        if not ruling.supersedes:
            continue
        reasons[ruling.because()] = reasons.get(ruling.because(), 0) + 1

    for because, times in reasons.items():
        print(f"    {times}x refuted — {because}")

    print()


def run(symbol: str | None, supersede: bool) -> int:
    return StatementAuditCommand().run(symbol, supersede)
