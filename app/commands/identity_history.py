"""What each provider has claimed one instrument was, look by look.

The developer read surface over the identity observation stream —
read-only, no model, no provider call, and it appends nothing: only an
explicit funded acquisition writes an observation.
"""

from __future__ import annotations

from app.domain.identity_observation import DISCLOSURE, IdentityHistory
from app.infrastructure.evidence.identity_observation_store import (
    IdentityObservationStore,
)

__all__ = ["run"]


async def run(
    symbol: str,
    store: IdentityObservationStore | None = None,
) -> int:
    key = symbol.upper().strip()

    history = IdentityHistory(
        symbol=key,
        observations=(store or IdentityObservationStore()).observations(key),
    )

    print(render(history))

    return 0


def render(history: IdentityHistory) -> str:
    """The history as an operator reads it. Pure, for the tests."""

    lines = [
        "",
        f"IDENTITY HISTORY — {history.symbol}",
        "=" * 60,
        DISCLOSURE,
        "",
    ]

    if not history.observations:
        lines.append(
            "No identity observations are held for this symbol. The stream "
            "fills at explicit funded acquisition, and a fresh installation "
            "has empty history."
        )

        return "\n".join(lines)

    count = len(history.observations)

    lines.append(f"{count} observation(s), oldest first:")
    lines.append("")

    for observation in history.observations:
        lines.append(f"  {observation.stated}")

        # The raw tenancy fields, shown as what they are: values the
        # vendor's payload carried, retained verbatim, inferring nothing.
        raw = []

        if observation.first_trade_date_ms is not None:
            raw.append(f"firstTradeDateMilliseconds={observation.first_trade_date_ms}")

        if observation.ipo_expected_date is not None:
            raw.append(f"ipoExpectedDate={observation.ipo_expected_date}")

        if raw:
            lines.append(
                f"      raw payload fields (retained, not interpreted): "
                f"{', '.join(raw)}"
            )

    lines.append("")
    lines.append(f"Lifecycle: {history.lifecycle_stated}")

    return "\n".join(lines)
