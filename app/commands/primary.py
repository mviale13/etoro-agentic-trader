"""Read canonical state directly, and report what it can and cannot settle.

The S4.5 authority experiment as a command. It is in the family of
`movrvest reader-stability` and `movrvest statement-shape`: a measurement
of this platform rather than of an asset. It costs a fetch, asks no
model, **stores nothing**, and decides nothing — no score, no standing
rule and no dossier is touched by running it.

What it answers is the question the S4 readiness report ended on: crypto
Asset Quality is blocked by evidence authority rather than by a shortage
of candidate metrics, so the thing worth measuring is what a fact can
*become* when it is computed from primary state.

Each figure is printed with everything needed to run it again — the
surface, the entity, the window, the inputs, the formula and the rule
version — because a deterministic computation nobody can reproduce is a
number with a story.
"""

from __future__ import annotations

from app.domain.primary_computation import MechanismEvidence, PrimaryComputation
from app.providers.primary_sources import (
    BitcoinExplorer,
    CardanoLedger,
    EthereumRpc,
    HyperliquidInfo,
)

#: Which canonical readings each security has. A security absent from
#: this table has none — a chain nobody has verified a surface for is
#: not read by resemblance to one that has been.
SUBJECTS: dict[str, str] = {
    "ETH": "Ethereum's base-fee burn, computed from block headers",
    "HYPE": "Hyperliquid's supply accounting and its Assistance Fund",
    "ADA": "Cardano's own ledger supply concepts",
    "BTC": "Bitcoin's block fees — the contrast case, not primary",
}


class PrimaryEvidenceCommand:
    def run(self, symbol: str | None = None) -> int:
        wanted = sorted(SUBJECTS) if symbol is None else [symbol.upper().strip()]

        unknown = [item for item in wanted if item not in SUBJECTS]

        if unknown:
            print(
                f"{unknown[0]} — no canonical surface has been verified for "
                "this security, so nothing is read. Resembling one that has "
                "been is not evidence about it."
            )

            return 1

        print("PRIMARY EVIDENCE — canonical state, read directly")
        print("=" * 70)
        print(
            _wrap(
                "A measurement of this platform. Nothing is stored, nothing "
                "is scored, and no standing rule changed: every figure below "
                "is a claim, and the authority line says what kind of claim.",
                "  ",
            )
        )

        failures = 0

        for item in wanted:
            print()
            print(f"{item} — {SUBJECTS[item]}")
            print("-" * 70)

            try:
                self._render(item)
            except Exception as exc:
                failures += 1
                print(_wrap(f"Not read: {exc}", "  "))

        print()

        return 1 if failures == len(wanted) else 0

    def _render(self, symbol: str) -> None:
        if symbol == "ETH":
            _computation(EthereumRpc().base_fee_burn())
            return

        if symbol == "HYPE":
            info = HyperliquidInfo()

            _computation(info.circulating_supply())
            print()
            _mechanism(info.assistance_fund())
            return

        if symbol == "ADA":
            for computation in CardanoLedger().supply_concepts():
                _computation(computation)
                print()
            return

        _computation(BitcoinExplorer().block_fees())


def _computation(item: PrimaryComputation) -> None:
    print(f"  {item.label}: {item.stated}")
    print(f"    authority   {item.authority.stated} — {item.authority.described}")
    print(f"    standing    {item.standing.stated}")
    print(f"    surface     {item.surface.name} ({item.surface.network})")
    print(
        f"                {'canonical' if item.surface.canonical else 'NOT canonical'}"
        f" — {item.surface.endpoint}"
    )
    print(_wrap(item.surface.because, "                "))
    print(f"    entity      {item.entity}")
    print(f"    window      {item.window.stated}")
    print(_wrap(f"formula     {item.formula}", "    "))
    print(f"    rule        {item.rule_version}")
    print("    inputs")

    for reference in item.inputs:
        print(f"      - {reference}")

    print(f"    repeatable  {'yes' if item.is_repeatable else 'NO'}")
    print(
        "    independently reproducible "
        + (
            "yes"
            if item.is_independently_reproducible
            else "NO — repeating this source is not checking it"
        )
    )

    if item.because:
        print(_wrap(f"why claimed  {item.because}", "    "))

    for caveat in item.caveats:
        print(_wrap(f"caveat      {caveat}", "    "))

    print(f"    corroborates by: {_wrap_inline(item.authority.corroboration)}")


def _mechanism(item: MechanismEvidence) -> None:
    print(f"  {item.label}")
    print(f"    authority   {item.authority.stated}")
    print(f"    standing    {item.standing.stated}")
    print(_wrap(f"observed    {item.observed}", "    "))
    print("    evidence")

    for reference in item.evidence:
        print(f"      - {reference}")

    print(_wrap(f"why         {item.because}", "    "))
    print("    does not establish")

    for line in item.does_not_establish:
        print(_wrap(f"- {line}", "      "))


def _wrap_inline(text: str) -> str:
    return " ".join(text.split())


def _wrap(text: str, indent: str, width: int = 88) -> str:
    """Wrapped with a hanging indent, so a continuation reads as one."""

    words = text.split()
    lines: list[str] = []
    current = indent
    hanging = indent + "    "

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = hanging

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return PrimaryEvidenceCommand().run(symbol)
