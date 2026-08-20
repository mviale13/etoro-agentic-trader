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

from app.domain.capital_envelope import (
    CapitalActionEnvelope,
    EnvelopeKind,
    QualityAuthority,
)
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
    RecordedAllocation,
    RecordedHolding,
    RecordedPortfolio,
    StageOutcome,
    holdings_by_security,
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
                "decisions": [_encode_decision(entry) for entry in finished.decisions],
                "newly_produced": list(finished.newly_produced),
                "changed": list(finished.changed),
                "unchanged": list(finished.unchanged),
                "attention": list(finished.attention),
                # Optional and backward-compatible under the same
                # schema, exactly as the envelope was: a record
                # written before these existed lacks the keys and
                # decodes as no portfolio and no candidates.
                "portfolio": _encode_portfolio(finished.portfolio),
                "candidates": [
                    _encode_decision(entry) for entry in finished.candidates
                ],
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
        unreadable = 0
        unsupported = 0
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
                        # Malformed JSON is unreadable.
                        unreadable += 1
                        continue

                    if isinstance(row, dict) and row.get("schema") != SCHEMA:
                        # Valid JSON under an unknown schema is refused,
                        # never misread — and never called unreadable.
                        unsupported += 1
                        continue

                    if not isinstance(row, dict):
                        unreadable += 1
                        continue

                    decoded = _decode(row)

                    if decoded is None:
                        # A current-schema record whose shape does not
                        # decode — a contradictory comparison basis
                        # included — is unreadable.
                        unreadable += 1
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
            unreadable_records=unreadable,
            unsupported_schemas=unsupported,
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
                    _decode_decision(entry) for entry in row.get("decisions", [])
                ),
                newly_produced=tuple(
                    str(item) for item in row.get("newly_produced", [])
                ),
                changed=tuple(str(item) for item in row.get("changed", [])),
                unchanged=tuple(str(item) for item in row.get("unchanged", [])),
                attention=tuple(str(item) for item in row.get("attention", [])),
                portfolio=_decode_portfolio(row.get("portfolio")),
                candidates=tuple(
                    _decode_decision(entry) for entry in row.get("candidates", [])
                ),
            )

        return None
    except (KeyError, TypeError, ValueError):
        return None


def _comparison(raw: Any) -> ComparisonBasis:
    """The stored basis, or a raised refusal to read a contradictory one.

    `ComparisonBasis` enforces its own shape at construction, so a
    stored combination the vocabulary forbids — a baseline carrying a
    prior id, a comparison without one, a refusal without a reason —
    raises here, `_decode` returns None, and the whole record counts as
    unreadable rather than decoding into a lifecycle or participating
    in movement.
    """

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


def _encode_decision(entry: DecisionSummary) -> dict[str, Any]:
    """One decision's stored shape — shared by holdings and candidates.

    Candidates went through the same pipeline as holdings, so they are
    stored in the same shape. One encoder means the two can never drift
    into meaning different things by the same key.
    """

    return {
        "symbol": entry.symbol,
        "state": entry.state,
        "rationale": entry.rationale,
        "conviction": entry.conviction,
        "evidence_as_of": entry.evidence_as_of,
        "action_kind": entry.action_kind,
        "action_statement": entry.action_statement,
        "action_because": entry.action_because,
        "asks_for_something": entry.asks_for_something,
        # Optional and backward-compatible under the same schema: a
        # pre-envelope record simply lacks the key and decodes exactly
        # as it always did.
        "envelope": _encode_envelope(entry.envelope),
    }


def _decode_decision(entry: dict[str, Any]) -> DecisionSummary:
    return DecisionSummary(
        symbol=str(entry["symbol"]),
        state=str(entry["state"]),
        rationale=str(entry.get("rationale", "")),
        conviction=(
            int(entry["conviction"]) if entry.get("conviction") is not None else None
        ),
        evidence_as_of=str(entry.get("evidence_as_of", "")),
        action_kind=str(entry.get("action_kind", "")),
        action_statement=str(entry.get("action_statement", "")),
        action_because=str(entry.get("action_because", "")),
        asks_for_something=bool(entry.get("asks_for_something", False)),
        envelope=_decode_envelope(entry.get("envelope")),
    )


def _encode_portfolio(portfolio: RecordedPortfolio | None) -> dict[str, Any] | None:
    if portfolio is None:
        return None

    return {
        "total_value": portfolio.total_value,
        "available_cash_usd": portfolio.available_cash_usd,
        "cash_pct": portfolio.cash_pct,
        "observed": portfolio.observed,
        "compliant": portfolio.compliant,
        "holdings": [
            {
                "symbol": holding.symbol,
                "market_value_usd": holding.market_value_usd,
                "weight_pct": holding.weight_pct,
            }
            for holding in portfolio.holdings
        ],
        "allocations": [
            {
                "asset": item.asset,
                "current_pct": item.current_pct,
                "target_pct": item.target_pct,
                "difference_pct": item.difference_pct,
            }
            for item in portfolio.allocations
        ],
    }


def _decode_portfolio(raw: Any) -> RecordedPortfolio | None:
    """Absent means a pre-field record; malformed refuses the record.

    Null and absent both decode as "this cycle recorded no portfolio",
    which is the honest reading of a record written before the field
    existed. A present-but-unreadable one raises, and the caller counts
    the whole record unreadable rather than silently dropping an
    account.

    **Holdings are folded on read, through the same function that folds
    them on write.** A line written before the composition folded
    carries the broker's *position* rows — two BTC trades as two
    entries, each stating the security's whole share of the account.
    Every figure on such a line is true; what was wrong is the reading
    that one row is one security. Summing the values of rows that state
    the same share is arithmetic over the line's own numbers, and the
    precondition is checked rather than assumed: rows of one security
    that disagree about the share raise, and the record is counted
    unreadable. This is not a schema change — the line format is
    unchanged, and no stored line is rewritten.
    """

    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise ValueError("a recorded portfolio is a mapping")

    return RecordedPortfolio(
        total_value=float(raw["total_value"]),
        available_cash_usd=(
            float(raw["available_cash_usd"])
            if raw.get("available_cash_usd") is not None
            else None
        ),
        cash_pct=(float(raw["cash_pct"]) if raw.get("cash_pct") is not None else None),
        observed=str(raw.get("observed", "")),
        compliant=(
            bool(raw["compliant"]) if raw.get("compliant") is not None else None
        ),
        holdings=holdings_by_security(
            RecordedHolding(
                symbol=str(item["symbol"]),
                market_value_usd=float(item["market_value_usd"]),
                weight_pct=(
                    float(item["weight_pct"])
                    if item.get("weight_pct") is not None
                    else None
                ),
            )
            for item in raw.get("holdings", [])
        ),
        allocations=tuple(
            RecordedAllocation(
                asset=str(item["asset"]),
                current_pct=(
                    float(item["current_pct"])
                    if item.get("current_pct") is not None
                    else None
                ),
                target_pct=float(item["target_pct"]),
                difference_pct=(
                    float(item["difference_pct"])
                    if item.get("difference_pct") is not None
                    else None
                ),
            )
            for item in raw.get("allocations", [])
        ),
    )


def _encode_envelope(
    envelope: CapitalActionEnvelope | None,
) -> dict[str, Any] | None:
    if envelope is None:
        return None

    return {
        "symbol": envelope.symbol,
        "course": envelope.course,
        "kind": envelope.kind.value,
        "policy_source": envelope.policy_source,
        "policy_version": envelope.policy_version,
        "evidence_ceiling": envelope.evidence_ceiling,
        "capacity_ceiling_pct": envelope.capacity_ceiling_pct,
        "final_pct": envelope.final_pct,
        "binding_constraint": envelope.binding_constraint,
        "because": envelope.because,
        "named_gaps": list(envelope.named_gaps),
        "quality_authority": (
            envelope.quality_authority.value
            if envelope.quality_authority is not None
            else None
        ),
        "starter_capped": envelope.starter_capped,
        "price_as_of": envelope.price_as_of,
        "portfolio_as_of": envelope.portfolio_as_of,
        "liquidity": envelope.liquidity,
    }


def _decode_envelope(raw: Any) -> CapitalActionEnvelope | None:
    """Absent means a pre-envelope record; malformed refuses the record.

    A `None` or missing key is the old contract and decodes as it
    always did. A present-but-unreadable envelope raises, which the
    caller counts as an unreadable record — never a silently dropped
    field on an otherwise-trusted line.
    """

    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise ValueError("an envelope is a mapping")

    return CapitalActionEnvelope(
        symbol=str(raw["symbol"]),
        course=str(raw["course"]),
        kind=EnvelopeKind(raw["kind"]),
        policy_source=str(raw["policy_source"]),
        policy_version=str(raw["policy_version"]),
        evidence_ceiling=str(raw.get("evidence_ceiling", "")),
        capacity_ceiling_pct=(
            float(raw["capacity_ceiling_pct"])
            if raw.get("capacity_ceiling_pct") is not None
            else None
        ),
        final_pct=(
            float(raw["final_pct"]) if raw.get("final_pct") is not None else None
        ),
        binding_constraint=str(raw.get("binding_constraint", "")),
        because=str(raw.get("because", "")),
        named_gaps=tuple(str(gap) for gap in raw.get("named_gaps", [])),
        quality_authority=(
            QualityAuthority(raw["quality_authority"])
            if raw.get("quality_authority") is not None
            else None
        ),
        starter_capped=bool(raw.get("starter_capped", False)),
        price_as_of=str(raw.get("price_as_of", "")),
        portfolio_as_of=str(raw.get("portfolio_as_of", "")),
        liquidity=str(raw.get("liquidity", "")),
    )


def _time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value))

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
