"""The append-only stream of company-knowledge acquisition outcomes.

JSON Lines, one file per canonical MOVRvest symbol, opened in append
mode and never in write mode — the intelligence journal's design (#111)
by way of the identity stream (#216), reused because the constraint is
the point: there is no code path here that can rewrite a line, and a
store that *could* rewrite an outcome would eventually be asked to.

**Schema rides on every line.** The file is never rewritten whole, so a
line written under schema 1 must stay readable beside every later line
forever, and a line under a schema this reader does not know is skipped
rather than pooled.

**Two identical attempts are two lines.** *This platform tried twice*
is a fact, and only an unclipped record supports it.

**A fresh installation has an empty journal.** Nothing backfills.
Historical refusal states are not inferred from missing files, and an
old-schema knowledge document that cannot be restored is **not** a
document refusal — it is a knowledge-store fact with its own separate
meaning, and guessing otherwise would manufacture exactly the
distinction this stream exists to stop guessing at.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.knowledge_acquisition import (
    KnowledgeAcquisitionEvent,
    KnowledgeOutcomeHistory,
)
from app.domain.knowledge_state import KnowledgeState
from app.infrastructure.evidence_root import evidence_path

#: The line format's own version, written on every line.
SCHEMA = 1


class KnowledgeOutcomeStore:
    """The stream. Appends, reads oldest-first, and nothing else."""

    def __init__(self, root: Path | str | None = None) -> None:
        # Resolved at construction, never in the signature: a default
        # evaluated at import would freeze the evidence root and ignore
        # every later redirection (#118's rule).
        self._root = (
            Path(root) if root is not None else evidence_path("knowledge_outcomes")
        )

    def path_for(self, symbol: str) -> Path:
        return self._root / f"{symbol.upper().strip()}.jsonl"

    # ── writing ─────────────────────────────────────────────────────

    def append(self, event: KnowledgeAcquisitionEvent) -> None:
        """One terminal event, after the outcome is known.

        Called last on every acquisition path, so a process that dies
        between the knowledge write and this line leaves the knowledge
        usable and invents no attempt outcome. There is deliberately no
        `finally` anywhere upstream: a hard kill must produce no
        manufactured terminal event.
        """

        path = self.path_for(event.symbol)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(_encode(event), sort_keys=True) + "\n")

    # ── reading ─────────────────────────────────────────────────────

    def history(self, symbol: str) -> KnowledgeOutcomeHistory:
        """Every readable outcome for one symbol, oldest first.

        Counts **every non-empty stored line that did not decode** —
        unreadable lines and unsupported schemas separately, the latter
        tallied by the schema value each declared. A caller learns
        whether it may make a complete claim about the lifecycle, and
        never mistakes a skipped line for an absent attempt.
        """

        normalized = symbol.upper().strip()
        path = self.path_for(normalized)

        events: list[KnowledgeAcquisitionEvent] = []
        unreadable = 0
        unsupported: dict[str, int] = {}

        if not path.exists():
            return KnowledgeOutcomeHistory(symbol=normalized)

        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    unreadable += 1
                    continue

                if isinstance(row, dict) and row.get("schema") != SCHEMA:
                    # Refused, never pooled: reading a line whose shape
                    # this reader does not understand as though it did
                    # is the silent cross-schema read the knowledge
                    # store's own contract forbids.
                    declared = str(row.get("schema"))
                    unsupported[declared] = unsupported.get(declared, 0) + 1
                    continue

                decoded = _decode(row)

                if decoded is None:
                    unreadable += 1
                    continue

                events.append(decoded)

        return KnowledgeOutcomeHistory(
            symbol=normalized,
            events=tuple(events),
            unreadable_records=unreadable,
            unsupported_schemas=tuple(sorted(unsupported.items())),
        )


def _encode(event: KnowledgeAcquisitionEvent) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "symbol": event.symbol,
        "attempted_at": event.attempted_at.isoformat(),
        "state": event.state.value,
        "source_key": event.source_key,
        "source_published": event.source_published,
        "because": event.because,
        "knowledge_usable": event.knowledge_usable,
        "usable_source_key": event.usable_source_key,
        "observations_after": event.observations_after,
        "ended_in_refusal": event.ended_in_refusal,
    }


def _decode(row: Any) -> KnowledgeAcquisitionEvent | None:
    if not isinstance(row, dict):
        return None

    try:
        return KnowledgeAcquisitionEvent(
            symbol=str(row["symbol"]),
            attempted_at=datetime.fromisoformat(str(row["attempted_at"])),
            state=KnowledgeState(str(row["state"])),
            source_key=(
                str(row["source_key"]) if row.get("source_key") is not None else None
            ),
            source_published=str(row.get("source_published", "")),
            because=str(row.get("because", "")),
            knowledge_usable=bool(row.get("knowledge_usable", False)),
            usable_source_key=(
                str(row["usable_source_key"])
                if row.get("usable_source_key") is not None
                else None
            ),
            observations_after=int(row.get("observations_after", 0)),
            ended_in_refusal=bool(row.get("ended_in_refusal", False)),
        )
    except (KeyError, TypeError, ValueError):
        return None
