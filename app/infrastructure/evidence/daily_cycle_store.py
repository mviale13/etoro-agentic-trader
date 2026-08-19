"""The append-only cycle log: two lines per cycle, derived on read.

JSON Lines in one file, opened in append mode and never write mode —
the journal pattern (#111), because a log that could rewrite a lifecycle
would eventually be asked to. Schema rides on every line; a line under
a schema this reader does not know is **counted and skipped, never
pooled** — a future cycle format must not decode as today's, and a log
holding lines it cannot read does not claim a complete lifecycle.

STARTED is appended before the first network action and flushed by the
close of its own file handle, so a process killed mid-cycle leaves the
one honest record of the interruption: a STARTED nothing followed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.daily_cycle import (
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleLog,
    CycleRecord,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    StageOutcome,
)
from app.infrastructure.evidence_root import evidence_path

#: The line format's own version, written on every line.
SCHEMA = 1


class DailyCycleStore:
    """Appends cycle events, reads the derived lifecycle, nothing else."""

    def __init__(self, root: Path | str | None = None) -> None:
        # Resolved at construction, never in the signature (#118).
        self._root = Path(root) if root is not None else evidence_path("cycles")

    @property
    def path(self) -> Path:
        return self._root / "cycles.jsonl"

    # ── writing ─────────────────────────────────────────────────────

    def append_started(self, started: CycleStarted) -> None:
        self._append(
            {
                "schema": SCHEMA,
                "kind": "started",
                "cycle_id": started.cycle_id,
                "at": started.started_at.isoformat(),
            }
        )

    def append_finished(self, finished: CycleFinished) -> None:
        self._append(
            {
                "schema": SCHEMA,
                "kind": "finished",
                "cycle_id": finished.cycle_id,
                "at": finished.finished_at.isoformat(),
                "status": finished.status.value,
                "stages": [
                    {
                        "name": stage.name,
                        "outcome": stage.outcome.value,
                        "because": stage.because,
                    }
                    for stage in finished.stages
                ],
                "securities_asked": finished.securities_asked,
                "securities_priced": finished.securities_priced,
                "refusals": list(finished.refusals),
                "comparison": {
                    "outcome": finished.comparison.outcome.value,
                    "prior_cycle_id": finished.comparison.prior_cycle_id,
                    "because": finished.comparison.because,
                },
                "decisions": [
                    {
                        "symbol": entry.symbol,
                        "state": entry.state,
                        "rationale": entry.rationale,
                        "conviction": entry.conviction,
                        "evidence_as_of": entry.evidence_as_of,
                        "action_kind": entry.action_kind,
                        "action_statement": entry.action_statement,
                        "action_because": entry.action_because,
                        "asks_for_something": entry.asks_for_something,
                    }
                    for entry in finished.decisions
                ],
                "newly_produced": list(finished.newly_produced),
                "changed": list(finished.changed),
                "unchanged": list(finished.unchanged),
                "attention": list(finished.attention),
            }
        )

    def _append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    # ── reading ─────────────────────────────────────────────────────

    def log(self) -> CycleLog:
        """Every valid cycle oldest first, and every departure counted.

        A valid lifecycle is one STARTED followed — in file order — by
        at most one FINISHED for the same cycle_id. Everything else is
        a **lifecycle anomaly**: a FINISHED with no earlier STARTED
        (orphan or terminal-before-start — from a reader's seat the
        same defect), a second STARTED for one id, a second FINISHED
        for one id. Anomalous events are counted and never pooled into
        a valid record — a byte-identical duplicate is still a second
        lifecycle event, and no recovery precedence is invented for it.
        Any anomaly makes the stream incomplete, which refuses
        historical movement upstream.
        """

        started: dict[str, CycleStarted] = {}
        order: list[str] = []
        finished: dict[str, CycleFinished] = {}
        skipped = 0
        anomalies = 0

        if self.path.exists():
            with self.path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        skipped += 1
                        continue

                    if not isinstance(row, dict) or row.get("schema") != SCHEMA:
                        skipped += 1
                        continue

                    decoded = _decode(row)

                    if decoded is None:
                        skipped += 1
                    elif isinstance(decoded, CycleStarted):
                        if decoded.cycle_id in started:
                            # A second STARTED for one cycle_id.
                            anomalies += 1
                        else:
                            started[decoded.cycle_id] = decoded
                            order.append(decoded.cycle_id)
                    else:
                        if decoded.cycle_id not in started:
                            # Terminal with no start seen yet: an orphan
                            # FINISHED or a terminal-before-start. Not
                            # paired later — the ordering is the
                            # lifecycle, and this event broke it.
                            anomalies += 1
                        elif decoded.cycle_id in finished:
                            # A second FINISHED for one cycle_id.
                            anomalies += 1
                        else:
                            finished[decoded.cycle_id] = decoded

        records = tuple(
            CycleRecord(started=started[cycle_id], finished=finished.get(cycle_id))
            for cycle_id in order
        )

        return CycleLog(
            records=records,
            skipped_records=skipped,
            lifecycle_anomalies=anomalies,
        )


# ── the line format ─────────────────────────────────────────────────


def _decode(row: dict[str, Any]) -> CycleStarted | CycleFinished | None:
    try:
        if row["kind"] == "started":
            return CycleStarted(
                cycle_id=str(row["cycle_id"]),
                started_at=_time(row["at"]),
            )

        if row["kind"] == "finished":
            return CycleFinished(
                cycle_id=str(row["cycle_id"]),
                finished_at=_time(row["at"]),
                status=CycleStatus(row["status"]),
                stages=tuple(
                    CycleStage(
                        name=str(stage["name"]),
                        outcome=StageOutcome(stage["outcome"]),
                        because=str(stage.get("because", "")),
                    )
                    for stage in row.get("stages", [])
                ),
                securities_asked=int(row.get("securities_asked", 0)),
                securities_priced=int(row.get("securities_priced", 0)),
                refusals=tuple(str(item) for item in row.get("refusals", [])),
                comparison=_comparison(row.get("comparison")),
                decisions=tuple(
                    DecisionSummary(
                        symbol=str(entry["symbol"]),
                        state=str(entry["state"]),
                        rationale=str(entry.get("rationale", "")),
                        conviction=(
                            int(entry["conviction"])
                            if entry.get("conviction") is not None
                            else None
                        ),
                        evidence_as_of=str(entry.get("evidence_as_of", "")),
                        action_kind=str(entry.get("action_kind", "")),
                        action_statement=str(entry.get("action_statement", "")),
                        action_because=str(entry.get("action_because", "")),
                        asks_for_something=bool(entry.get("asks_for_something", False)),
                    )
                    for entry in row.get("decisions", [])
                ),
                newly_produced=tuple(
                    str(item) for item in row.get("newly_produced", [])
                ),
                changed=tuple(str(item) for item in row.get("changed", [])),
                unchanged=tuple(str(item) for item in row.get("unchanged", [])),
                attention=tuple(str(item) for item in row.get("attention", [])),
            )

        return None
    except (KeyError, TypeError, ValueError):
        return None


def _comparison(raw: Any) -> ComparisonBasis:
    if not isinstance(raw, dict):
        return ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED,
            because="the record carries no comparison basis",
        )

    return ComparisonBasis(
        outcome=ComparisonOutcome(raw["outcome"]),
        prior_cycle_id=str(raw.get("prior_cycle_id", "")),
        because=str(raw.get("because", "")),
    )


def _time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value))

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
