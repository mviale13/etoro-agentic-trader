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
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.domain.knowledge_acquisition import (
    SAFE_SYMBOL,
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
        """The one file this symbol's outcomes live in, or a refusal.

        Validated, never encoded: a symbol that is not canonical is
        refused outright rather than rewritten into a filename, so two
        distinct symbols can never collide on one file and no
        path-shaping input (`../DIS`, `A/B`, whitespace) reaches the
        filesystem at all. The containment check is belt on top of
        braces — the pattern already admits no separator — and it is an
        invariant worth crashing on rather than a case worth handling.
        """

        normalized = symbol.upper().strip()

        if not SAFE_SYMBOL.fullmatch(normalized):
            raise ValueError(f"{symbol!r} is not a canonical MOVRvest symbol")

        path = self._root / f"{normalized}.jsonl"

        assert path.resolve().parent == self._root.resolve(), (
            f"{symbol!r} resolved outside the journal root"
        )

        return path

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

                declared = row.get("schema") if isinstance(row, dict) else None

                if isinstance(row, dict) and (
                    type(declared) is not int or declared != SCHEMA
                ):
                    # Refused, never pooled: reading a line whose shape
                    # this reader does not understand as though it did
                    # is the silent cross-schema read the knowledge
                    # store's own contract forbids. `type is int`
                    # rather than isinstance, because a JSON `true`
                    # decodes to a bool that *equals* 1 — and a boolean
                    # schema is not schema 1, it is a shape this reader
                    # has never written.
                    unsupported[str(declared)] = unsupported.get(str(declared), 0) + 1
                    continue

                decoded = _decode(row)

                if decoded is None or decoded.symbol != normalized:
                    # A malformed current-schema line, or another
                    # symbol's event inside this symbol's file. Both
                    # are counted, and neither is pooled: a journal
                    # keyed by symbol may not serve one symbol's
                    # history out of another's attempts.
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


def _string_or_none(value: Any) -> tuple[bool, str | None]:
    """The value exactly as stored, or a refusal. Never a repair."""

    if value is None:
        return True, None

    if type(value) is str:
        return True, value

    return False, None


def _decode(row: Any) -> KnowledgeAcquisitionEvent | None:
    """One stored line, decoded strictly or refused whole.

    **A current-schema malformed record is unreadable, not repaired.**
    The first cut of this decoder ran every field through `bool()`,
    `int()` and `str()` — which would have read a stored
    `"knowledge_usable": "false"` as `True`, because a non-empty string
    is truthy. A journal whose reader can invert a stored fact while
    "repairing" it is worse than no journal, so every field is checked
    for its exact type and an exact-schema line that fails any check is
    counted unreadable, never coerced into a plausible event.
    """

    if not isinstance(row, dict):
        return None

    symbol = row.get("symbol")

    if type(symbol) is not str or not symbol.strip():
        return None

    raw_attempted = row.get("attempted_at")

    if type(raw_attempted) is not str:
        return None

    try:
        attempted_at = datetime.fromisoformat(raw_attempted)
    except ValueError:
        return None

    if attempted_at.tzinfo is None:
        return None

    raw_state = row.get("state")

    if type(raw_state) is not str:
        return None

    try:
        state = KnowledgeState(raw_state)
    except ValueError:
        return None

    source_ok, source_key = _string_or_none(row.get("source_key"))
    usable_ok, usable_source_key = _string_or_none(row.get("usable_source_key"))

    if not source_ok or not usable_ok:
        return None

    source_published = row.get("source_published")

    if type(source_published) is not str:
        return None

    if source_published:
        try:
            date.fromisoformat(source_published)
        except ValueError:
            return None

    because = row.get("because")

    if type(because) is not str:
        return None

    knowledge_usable = row.get("knowledge_usable")
    ended_in_refusal = row.get("ended_in_refusal")

    # `type is bool`, not isinstance-and-truthiness: a stored `0` or
    # `"false"` is a record this writer never produced.
    if type(knowledge_usable) is not bool or type(ended_in_refusal) is not bool:
        return None

    observations_after = row.get("observations_after")

    # `type is int` refuses bool too — `True` is an int by inheritance
    # and a count of `True` observations is not a count.
    if type(observations_after) is not int or observations_after < 0:
        return None

    try:
        return KnowledgeAcquisitionEvent(
            symbol=symbol,
            attempted_at=attempted_at,
            state=state,
            source_key=source_key,
            source_published=source_published,
            because=because,
            knowledge_usable=knowledge_usable,
            usable_source_key=usable_source_key,
            observations_after=observations_after,
            ended_in_refusal=ended_in_refusal,
        )
    except ValueError:
        # A line whose fields are each well-typed and whose whole
        # violates the event's own invariants — refused for the same
        # reason, under the same count.
        return None
