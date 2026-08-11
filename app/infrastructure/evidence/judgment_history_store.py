"""An append-only record of what a committee concluded, one line at a time.

The intelligence journal's store, and deliberately its twin rather than
its subclass: JSON Lines, one file per asset, opened in append mode and
never in write mode, with the schema carried **per line** because a file
that is never rewritten cannot be migrated. A judgment written under
version 1 of a committee must stay readable beside one written under
version 2 forever — that is not a storage convenience, it is the
evidence that the committee ever held the earlier view.

**Nothing here can rewrite a judgment**, and that constraint is the
design. A store that could would eventually be asked to, and the first
request would be reasonable: *today's committee would not have said
that, so correct it*. Which is precisely the question this record exists
to answer in the other direction.

**A deleted record is a lost claim, not a recoverable one.** Nothing in
this platform can reconstruct what a committee concluded from evidence
alone — running the committee again produces today's judgment from
today's evidence, which is a different fact. Delete the file and the
ability to say *the committee previously found this* goes with it, and
that is the correct behaviour rather than a gap.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    Confidence,
    JudgmentState,
)
from app.domain.committee_protocol import CommitteeIdentity
from app.domain.judgment_history import JudgmentRecord

#: The line format's own version, written on every line.
#:
#: 3 adds the committee's own stated reason, which the assessment matrix
#: needs to tell two identical-looking abstentions apart.
#:
#: 2 adds the committee's display name and the committee's own sentence
#: for its verdict — both absent from schema 1, and both **read with a
#: fallback rather than migrated**. A schema-1 line names its committee
#: by key and its answer by token, which is less pleasant to read and
#: exactly as true. The journal's rule holds: a file that is never
#: rewritten cannot be migrated, so old lines are read as they were
#: written, forever.
SCHEMA = 3


class JudgmentHistoryStore:
    """The record. Appends, reads, and cannot do anything else."""

    def __init__(self, root: Path | str = "data/judgments") -> None:
        self._root = Path(root)

    def path_for(self, asset: str) -> Path:
        return self._root / f"{asset.upper().strip()}.jsonl"

    # ── writing ─────────────────────────────────────────────────────

    def append(self, record: JudgmentRecord) -> bool:
        """Add one judgment. Returns False if it was already recorded.

        Idempotent on `record_id`, which is derived from the committee,
        the moment and the content — so replaying one judgment is a
        no-op, while judging again later is a second event even if the
        answer is identical.

        The second behaviour is the honest one and matches the journal's
        reasoning exactly: the committee did convene twice, and a count
        of judgments is a fact `JudgmentCoverage` is built from.
        """

        if self.holds(record.asset, record.record_id):
            return False

        path = self.path_for(record.asset)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_encode(record), sort_keys=True))
            handle.write("\n")

        return True

    def holds(self, asset: str, record_id: str) -> bool:
        return any(record.record_id == record_id for record in self._records(asset))

    # ── reading ─────────────────────────────────────────────────────

    def records(
        self,
        asset: str,
        committee: str | None = None,
        limit: int | None = None,
    ) -> list[JudgmentRecord]:
        """Every judgment for this asset, oldest first.

        Filtered by committee key where one is given, because one file
        holds one asset and an asset may be asked more than one
        question — and two committees' verdicts pooled into one history
        would be the same category error as pooling two evidence
        streams. **The key is compared as a string**, so a record
        written by a committee whose code is gone is still readable and
        still filterable.
        """

        found = [
            record
            for record in self._records(asset)
            if committee is None or record.committee.key == committee
        ]

        found.sort(key=lambda record: record.judged_at)

        return found[-limit:] if limit else found

    def _records(self, asset: str) -> Iterator[JudgmentRecord]:
        path = self.path_for(asset)

        if not path.exists():
            return

        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    # One unreadable line must not cost the record.
                    continue

                record = _decode(row)

                if record is not None:
                    yield record


# ── the line format ─────────────────────────────────────────────────


def _encode(record: JudgmentRecord) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "record_id": record.record_id,
        "asset": record.asset,
        "remit": record.committee.key,
        "committee_name": record.committee.name,
        "committee_version": record.committee.version,
        "committee_fingerprint": record.committee.fingerprint,
        "judged_at": record.judged_at.isoformat(),
        "recorded_at": record.recorded_at.isoformat(),
        "applicability": record.applicability.value,
        "state": record.state.value,
        "verdict": record.verdict,
        "verdict_stated": record.verdict_stated,
        "confidence": record.confidence.value if record.confidence else None,
        "refs": list(record.refs),
        "evidence_digest": record.evidence_digest,
        "evidence_count": record.evidence_count,
        "abstained_because": (
            record.abstained_because.value if record.abstained_because else None
        ),
        "because": record.because,
        "unavailable_because": record.unavailable_because,
        "economic_role": record.economic_role,
        "model": record.model,
    }


def _decode(row: Any) -> JudgmentRecord | None:
    if not isinstance(row, dict):
        return None

    try:
        return JudgmentRecord(
            asset=str(row["asset"]),
            committee=CommitteeIdentity(
                key=str(row["remit"]),
                # Schema 1 carried no name. The key is what it was filed
                # under and is never wrong, only terser.
                name=str(row.get("committee_name") or row["remit"]),
                version=int(row["committee_version"]),
                fingerprint=str(row["committee_fingerprint"]),
            ),
            judged_at=_time(row["judged_at"]) or datetime.now(UTC),
            recorded_at=_time(row.get("recorded_at")) or datetime.now(UTC),
            applicability=Applicability(row["applicability"]),
            state=JudgmentState(row["state"]),
            verdict=str(row["verdict"]) if row.get("verdict") else None,
            verdict_stated=(
                str(row["verdict_stated"]) if row.get("verdict_stated") else None
            ),
            confidence=(
                Confidence(row["confidence"]) if row.get("confidence") else None
            ),
            refs=tuple(row.get("refs") or ()),
            evidence_digest=str(row.get("evidence_digest") or ""),
            evidence_count=int(row.get("evidence_count") or 0),
            abstained_because=(
                AbstentionReason(row["abstained_because"])
                if row.get("abstained_because")
                else None
            ),
            because=row.get("because"),
            unavailable_because=row.get("unavailable_because"),
            economic_role=row.get("economic_role"),
            model=row.get("model"),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
