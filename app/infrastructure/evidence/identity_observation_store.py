"""The append-only stream of provider identity observations.

JSON Lines, one file per symbol, opened in append mode and never in
write mode — the intelligence journal's design (#111), reused because
the constraint is the point: there is no code path here that can
rewrite a line, and a store that *could* rewrite history would
eventually be asked to.

**Schema rides on every line**, following the journal precedent: this
file is never rewritten whole, so a line written under schema 1 must
stay readable beside every later line forever. A line under a schema
this reader does not know is skipped, never pooled — reading it as
though its shape were understood would be the silent cross-schema
pooling the knowledge store's contract forbids.

**Two identical looks are two lines.** The journal's honesty rule:
this platform looked twice, and the count of looks is a fact. An
acquisition that observes the same claims as yesterday's still appends,
because "the claims did not move across two funded reads" is exactly
the kind of statement only an unclipped record can support.

A fresh installation has an empty history — nothing backfills, and
SPCX's 2026-08-13 contradiction is *not* reconstructed from prose or
fixtures: it predates the stream and enters history only as the #215
measurement's citation.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.identity_observation import ProviderIdentityObservation
from app.domain.provider_identity import IdentityStanding, ProviderIdentityClaim
from app.infrastructure.evidence_root import evidence_path

#: The line format's own version, written on every line.
SCHEMA = 1


class IdentityObservationStore:
    """The stream. Appends, reads oldest-first, and nothing else."""

    def __init__(self, root: Path | str | None = None) -> None:
        # Resolved at construction, never in the signature: a default
        # evaluated at import would freeze the evidence root and ignore
        # every later redirection (#118's rule, and ruff caught three
        # stores getting it wrong).
        self._root = Path(root) if root is not None else evidence_path("identity")

    def path_for(self, symbol: str) -> Path:
        return self._root / f"{symbol.upper().strip()}.jsonl"

    # ── writing ─────────────────────────────────────────────────────

    def append(self, observation: ProviderIdentityObservation) -> None:
        """Add one observation. Only explicit funded acquisition calls this."""

        path = self.path_for(observation.symbol)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_encode(observation), sort_keys=True))
            handle.write("\n")

    # ── reading ─────────────────────────────────────────────────────

    def observations(self, symbol: str) -> tuple[ProviderIdentityObservation, ...]:
        """Every held observation for this symbol, oldest first."""

        held = sorted(self._lines(symbol), key=lambda entry: entry.captured_at)

        return tuple(held)

    def _lines(self, symbol: str) -> Iterator[ProviderIdentityObservation]:
        path = self.path_for(symbol)

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

                observation = _decode(row)

                if observation is not None:
                    yield observation


# ── the line format ─────────────────────────────────────────────────


def _encode(observation: ProviderIdentityObservation) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "symbol": observation.symbol,
        "captured_at": observation.captured_at.isoformat(),
        "broker": _claim(observation.broker),
        "vendor": _claim(observation.vendor),
        "standing": observation.standing.value,
        "first_trade_date_ms": observation.first_trade_date_ms,
        "ipo_expected_date": observation.ipo_expected_date,
    }


def _claim(claim: ProviderIdentityClaim) -> dict[str, Any]:
    return {
        "provider": claim.provider,
        "symbol": claim.symbol,
        "instrument_id": claim.instrument_id,
        "name": claim.name,
        "taxonomy": claim.taxonomy,
        "exchange": claim.exchange,
        "isin": claim.isin,
        "entity_identifier": claim.entity_identifier,
    }


def _decode(row: Any) -> ProviderIdentityObservation | None:
    if not isinstance(row, dict) or row.get("schema") != SCHEMA:
        # A schema this reader does not know is not silently pooled
        # with lines it does. Skipped, and the record keeps reading.
        return None

    try:
        return ProviderIdentityObservation(
            symbol=str(row["symbol"]),
            captured_at=_time(row["captured_at"]),
            broker=_restore_claim(row["broker"]),
            vendor=_restore_claim(row["vendor"]),
            standing=IdentityStanding(row["standing"]),
            first_trade_date_ms=_integer(row.get("first_trade_date_ms")),
            ipo_expected_date=(
                str(row["ipo_expected_date"])
                if row.get("ipo_expected_date") is not None
                else None
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _restore_claim(raw: Any) -> ProviderIdentityClaim:
    if not isinstance(raw, dict):
        raise TypeError("a claim is a mapping")

    def text(key: str) -> str | None:
        value = raw.get(key)

        return str(value) if isinstance(value, str) and value else None

    return ProviderIdentityClaim(
        provider=str(raw["provider"]),
        symbol=str(raw["symbol"]),
        instrument_id=text("instrument_id"),
        name=text("name"),
        taxonomy=text("taxonomy"),
        exchange=text("exchange"),
        isin=text("isin"),
        entity_identifier=text("entity_identifier"),
    )


def _time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value))

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _integer(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
