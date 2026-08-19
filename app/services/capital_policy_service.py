"""Load the owner's capital policy from the one authoritative source.

Reads `investor_strategy.json` under the evidence root, validates it
against the #220 ruling's contract, and answers with a
`CapitalPolicyReading` — a policy or a worded refusal, never a default.
It does not touch the decision engine's own policy inputs: the envelope
consumes the authoritative capital policy separately, and the legacy
`config/policy.yaml` and `app/config.py` sources are not read here.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.capital_policy import (
    ACTIVE,
    CapitalPolicy,
    CapitalPolicyReading,
    ReducePolicy,
    policy_version,
)
from app.infrastructure.evidence_root import evidence_path

SOURCE = "investor_strategy.json"

#: field name → the strategy-file section it must appear in.
_REQUIRED = {
    "starter_max_total_position_pct": "capital_envelope",
    "standard_initial_position_pct": "capital_envelope",
    "max_add_weight_change_pct": "capital_envelope",
    "price_max_age_minutes": "capital_envelope",
    "portfolio_max_age_minutes": "capital_envelope",
    "reduce_policy": "capital_envelope",
    "maximum_single_position_pct": "portfolio_policy",
    "maximum_crypto_pct": "portfolio_policy",
    "target_cash_pct": "portfolio_policy",
    "minimum_cash_pct": "portfolio_policy",
    "maximum_acceptable_drawdown_pct": "objectives",
}


class CapitalPolicyService:
    """One reader, one source, one answer shape."""

    def __init__(self, path: Path | str | None = None) -> None:
        # Resolved at construction, never in the signature (#118).
        self._path = Path(path) if path is not None else evidence_path(SOURCE)

    def reading(self) -> CapitalPolicyReading:
        try:
            raw = json.loads(self._path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            return CapitalPolicyReading(
                refused_because=(
                    "the owner strategy could not be read "
                    f"({type(error).__name__}), and no capital envelope can "
                    "rest on a policy this platform cannot read"
                )
            )

        if not isinstance(raw, dict):
            return CapitalPolicyReading(
                refused_because="the owner strategy is not a policy document"
            )

        status = str(raw.get("status", "")).strip().lower()

        if status != ACTIVE:
            named = status or "unstated"

            return CapitalPolicyReading(
                refused_because=(
                    f"the owner strategy's status is {named}, and a {named} "
                    "strategy cannot authorize a capital envelope"
                )
            )

        rules = raw.get("decision_rules", {})

        if rules.get("automatic_trading_enabled") is not False:
            return CapitalPolicyReading(
                refused_because=(
                    "the policy does not state automatic_trading_enabled: "
                    "false, which the ruling requires preserved"
                )
            )

        if rules.get("require_human_approval") is not True:
            return CapitalPolicyReading(
                refused_because=(
                    "the policy does not state require_human_approval: true, "
                    "which the ruling requires preserved"
                )
            )

        values: dict[str, object] = {}

        for field, section in _REQUIRED.items():
            block = raw.get(section)
            value = block.get(field) if isinstance(block, dict) else None

            if value is None:
                # A missing limit always refuses. No numeric default, no
                # fallback to any other source.
                return CapitalPolicyReading(
                    refused_because=(
                        f"the owner strategy does not state {section}.{field}, "
                        "and a missing sizing limit refuses rather than "
                        "defaults"
                    )
                )

            values[field] = value

        try:
            reduce_policy = ReducePolicy(str(values["reduce_policy"]))
        except ValueError:
            return CapitalPolicyReading(
                refused_because=(
                    f"reduce_policy {values['reduce_policy']!r} is not in the "
                    "v1 vocabulary"
                )
            )

        hashed = {
            "starter_max_total_position_pct": values["starter_max_total_position_pct"],
            "standard_initial_position_pct": values["standard_initial_position_pct"],
            "max_add_weight_change_pct": values["max_add_weight_change_pct"],
            "max_single_position_pct": values["maximum_single_position_pct"],
            "max_crypto_pct": values["maximum_crypto_pct"],
            "target_cash_pct": values["target_cash_pct"],
            "minimum_cash_pct": values["minimum_cash_pct"],
            "price_max_age_minutes": values["price_max_age_minutes"],
            "portfolio_max_age_minutes": values["portfolio_max_age_minutes"],
            "maximum_acceptable_drawdown_pct": values[
                "maximum_acceptable_drawdown_pct"
            ],
            "reduce_policy": reduce_policy.value,
        }

        try:
            policy = CapitalPolicy(
                starter_max_total_position_pct=float(
                    values["starter_max_total_position_pct"]  # type: ignore[arg-type]
                ),
                standard_initial_position_pct=float(
                    values["standard_initial_position_pct"]  # type: ignore[arg-type]
                ),
                max_add_weight_change_pct=float(
                    values["max_add_weight_change_pct"]  # type: ignore[arg-type]
                ),
                max_single_position_pct=float(
                    values["maximum_single_position_pct"]  # type: ignore[arg-type]
                ),
                max_crypto_pct=float(values["maximum_crypto_pct"]),  # type: ignore[arg-type]
                target_cash_pct=float(values["target_cash_pct"]),  # type: ignore[arg-type]
                minimum_cash_pct=float(values["minimum_cash_pct"]),  # type: ignore[arg-type]
                price_max_age_minutes=float(
                    values["price_max_age_minutes"]  # type: ignore[arg-type]
                ),
                portfolio_max_age_minutes=float(
                    values["portfolio_max_age_minutes"]  # type: ignore[arg-type]
                ),
                maximum_acceptable_drawdown_pct=float(
                    values["maximum_acceptable_drawdown_pct"]  # type: ignore[arg-type]
                ),
                reduce_policy=reduce_policy,
                source=SOURCE,
                version=policy_version(hashed),
            )
        except (TypeError, ValueError) as error:
            return CapitalPolicyReading(
                refused_because=f"the owner strategy is contradictory: {error}"
            )

        return CapitalPolicyReading(policy=policy)
