"""An issuance rule once a day, behind the platform's two doors.

`CachedPrimarySupplyProvider`'s shape, and its reason. A committee's
`evidence()` is read by a surface, and a surface that fetched would make
opening a page an acquisition — so the reading committee gets a
`stored()` door that asks the cache and stops, while `movrvest judge`
holds the door that may go and look.

**The whole rule is cached, not a summary of it.** A record keeping only
the fields today's committee happens to read would be a second
representation of an issuance rule, and the next reader of it would have
to guess which fields were dropped because they did not matter and which
because nobody needed them yet. The provenance encoder is the primary
supply cache's own, reused rather than reimplemented: a rule and a
figure are judged by the same gate and there is no reason for two
spellings of the same evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.evidence_authority import EvidenceAuthority
from app.domain.evidence_standing import EvidenceStanding
from app.domain.mechanical_issuance import (
    IssuanceMechanism,
    IssuanceState,
    MechanicalIssuance,
    ProjectedIssuance,
    RuleMutability,
    RuleParameter,
)
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache
from app.infrastructure.evidence_root import evidence_path
from app.providers.issuance_rule_provider import IssuanceRuleProvider
from app.providers.primary_supply_provider import (
    _decode_provenance,
    _encode_provenance,
)

#: The record's own version. 1, because this store is new — and it
#: carries a version from its first line for the reason S5.2 established:
#: ten of eleven stores were unversioned and the eleventh is the one
#: nobody remembers to add.
SCHEMA = 1


class CachedIssuanceRuleProvider:
    """This platform's reading of an issuance rule, held for a day."""

    def __init__(
        self,
        provider: IssuanceRuleProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or IssuanceRuleProvider()
        self._cache = cache or JsonCache(
            evidence_path("cache", "issuance_rules"), schema=SCHEMA
        )
        self._acquires = acquires

    @classmethod
    def stored(cls, cache: JsonCache | None = None) -> CachedIssuanceRuleProvider:
        """What has already been read, and nothing else."""

        return cls(cache=cache, acquires=False)

    def rule(self, symbol: str) -> MechanicalIssuance | None:
        """This asset's issuance rule, or None where none is held.

        `None` is deliberately the same answer for *this protocol has no
        mechanical rule* and *nothing has been acquired yet*. The
        committee above decides what that absence means, and it has more
        to read than this provider does — a provider that guessed would
        be making the committee's judgment for it in the cheapest
        possible place.
        """

        key = symbol.upper().strip()

        entry = self._cache.read(key)

        held = _restore(entry) if entry is not None else None

        if entry is not None and (not self._acquires or entry.is_from_today()):
            return held

        if not self._acquires:
            return None

        try:
            rule = self._provider.rule(key)
        except Exception:
            return held

        # An asset with no mechanism is written as an empty record rather
        # than left unwritten, so a later read can tell *we looked and
        # there is no rule* from *we have not looked*.
        self._cache.write(key, {"rule": _encode(rule) if rule else None})

        return rule


def _restore(entry: CachedEntry) -> MechanicalIssuance | None:
    payload = entry.value if isinstance(entry.value, dict) else {}

    return _decode(payload.get("rule"))


# ── the record format ───────────────────────────────────────────────


def _encode(rule: MechanicalIssuance) -> dict[str, Any]:
    return {
        "symbol": rule.symbol,
        "mechanism": rule.mechanism.value,
        "formula": rule.formula,
        "mutability": rule.mutability.value,
        "authority": rule.authority.value,
        "standing": rule.standing.value,
        "source": rule.source,
        "because": rule.because,
        "caveats": list(rule.caveats),
        "provenance": _encode_provenance(rule.provenance),
        "state": {
            "unit": rule.state.unit,
            "position": rule.state.position,
            "observed_at": rule.state.observed_at.isoformat(),
            "emitted": rule.state.emitted,
            "emitted_is_derived": rule.state.emitted_is_derived,
            "remaining": rule.state.remaining,
            "current_rate": rule.state.current_rate,
        },
        "parameters": [
            {
                "name": parameter.name,
                "value": parameter.value,
                "unit": parameter.unit,
                "read_from": parameter.read_from,
                "means": parameter.means,
            }
            for parameter in rule.parameters
        ],
        "path": [
            {
                "horizon": step.horizon,
                "issuance": step.issuance,
                "unit": step.unit,
                "share_of_emitted": step.share_of_emitted,
                "rule_version": step.rule_version,
            }
            for step in rule.path
        ],
    }


def _decode(row: Any) -> MechanicalIssuance | None:
    if not isinstance(row, dict):
        return None

    provenance = _decode_provenance(row.get("provenance"))

    if provenance is None:
        # The gate reads provenance. A rule restored without it would be
        # judged on evidence that is not there.
        return None

    try:
        state = row["state"]

        return MechanicalIssuance(
            symbol=str(row["symbol"]),
            mechanism=IssuanceMechanism(row["mechanism"]),
            state=IssuanceState(
                unit=str(state["unit"]),
                position=str(state["position"]),
                observed_at=_time(state.get("observed_at")) or datetime.now(UTC),
                emitted=_number(state.get("emitted")),
                emitted_is_derived=bool(state.get("emitted_is_derived")),
                remaining=_number(state.get("remaining")),
                current_rate=_number(state.get("current_rate")),
            ),
            formula=str(row["formula"]),
            parameters=tuple(
                RuleParameter(
                    name=str(parameter["name"]),
                    value=float(parameter["value"]),
                    unit=str(parameter["unit"]),
                    read_from=str(parameter["read_from"]),
                    means=str(parameter["means"]),
                )
                for parameter in row.get("parameters") or ()
            ),
            mutability=RuleMutability(row["mutability"]),
            provenance=provenance,
            authority=EvidenceAuthority(row["authority"]),
            standing=EvidenceStanding(row["standing"]),
            source=str(row["source"]),
            path=tuple(
                ProjectedIssuance(
                    horizon=str(step["horizon"]),
                    issuance=float(step["issuance"]),
                    unit=str(step["unit"]),
                    share_of_emitted=float(step["share_of_emitted"]),
                    rule_version=str(step["rule_version"]),
                )
                for step in row.get("path") or ()
            ),
            because=row.get("because"),
            caveats=tuple(row.get("caveats") or ()),
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


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
