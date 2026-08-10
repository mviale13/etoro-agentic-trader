"""How new supply enters a system, and what the rule implies from here.

The investor-facing half of S5.2's acquisition. It answers the four
questions a holder actually has about supply — how does new supply
arrive, how much can arrive, how predictable is that, and what could
change the rule — and it answers none of them with a score.

Every projection is worded *under the currently observed policy*,
carries the rule version it came from, and sits beside the mutability of
that rule. A path from a consensus-fixed schedule and a path from a
governance parameter are not the same claim about the future, and this
surface never lets them look like one.

An asset whose supply arrives by allocation release gets no rule and
says so, with the evidence that is actually missing named. Read-only:
it fetches its readings and stores nothing.
"""

from __future__ import annotations

from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.mechanical_issuance import MechanicalIssuance
from app.providers.issuance_rule_provider import IssuanceRuleProvider

#: What is missing for the assets that have no mechanical rule, named
#: rather than left blank. A silence here would read as "nothing to
#: say", and what is true is "this platform cannot reach the schedule".
_ALLOCATION_DEMAND = {
    "ARB": (
        "Arbitrum minted its whole supply at genesis, so its contract "
        "total says nothing about what is economically available. Two "
        "vendors put its circulating supply 419% apart, and which "
        "balances hold the difference — and when they release — is "
        "published by no source this platform can reach."
    ),
    "HYPE": (
        "Hyperliquid publishes its genesis allocation in full: 94,023 "
        "addresses summing to exactly one billion HYPE. It publishes who "
        "and how much, and nothing about when. The cadence for the 412.5 "
        "million allocated and not yet emitted is not reachable."
    ),
    "1INCH": (
        "No primary surface and no release schedule from any source this "
        "platform reads."
    ),
    "TAO": (
        "Bittensor's chain serves its total issuance, and the storage "
        "item holding its emission rule was looked for and not located. "
        "That is a gap in this platform's reading, not a statement about "
        "the protocol."
    ),
    "ETH": (
        "Ethereum has no maximum supply — CoinGecko states so positively "
        "rather than leaving it blank — and its net issuance is validator "
        "rewards less the burn. The burn is available from one "
        "non-primary source and the reward side is not read here, so the "
        "rule cannot be assembled."
    ),
}


class IssuanceCommand:
    def run(self, symbol: str | None = None) -> int:
        provider = IssuanceRuleProvider()

        if symbol is None:
            _render_corpus(provider)
            return 0

        normalized = symbol.upper().strip()

        rule = provider.rule(normalized)

        if rule is None:
            _render_absent(normalized)
            return 0

        _render(rule)

        return 0


def _render(rule: MechanicalIssuance) -> None:
    print(f"{rule.symbol} — how new supply enters")
    print()
    print(_wrap(f"{rule.mechanism.stated}: {rule.mechanism.described}.", "  "))
    print()

    state = rule.state

    print(
        f"  Read at            {state.position}, {state.observed_at:%Y-%m-%d %H:%M} UTC"
    )

    if state.emitted is not None:
        derived = " (computed from the rule, not published by a source)"

        print(
            f"  Supply so far      {state.emitted:,.0f} {state.unit}"
            + (derived if state.emitted_is_derived else "")
        )

    if state.remaining is not None:
        print(f"  Still to be issued {state.remaining:,.0f} {state.unit}")

    if state.current_rate is not None:
        print(f"  Issuing now at     {state.current_rate:.3%} a year")

    print()
    print("  The rule")
    print(_wrap(rule.formula, "    "))
    print()

    for parameter in rule.parameters:
        print(f"    {parameter.name:34s} {parameter.value:>18,.6f} {parameter.unit}")
        print(_wrap(f"{parameter.means} — read from {parameter.read_from}", "      "))

    print()
    print(f"  What could change it   {rule.mutability.stated}")
    print(_wrap(rule.mutability.because.capitalize() + ".", "    "))

    if rule.path:
        print()
        print("  Under the currently observed policy")
        print(
            _wrap(
                "MOVRvest's arithmetic from the rule above, not a "
                "forecast and not an observation. It holds while the rule "
                "does.",
                "    ",
            )
        )
        print()

        for step in rule.path:
            figure = (
                f"{step.issuance:>18,.2f} {step.unit}"
                if step.unit != "annual share of supply"
                else f"{step.issuance:>18.3%} a year"
            )

            print(f"    {step.horizon:52s} {figure}")

        print()
        print(f"    rule version {rule.path[0].rule_version}")

    if rule.caveats:
        print()
        print("  Worth knowing")
        for caveat in rule.caveats:
            print(_wrap(f"· {caveat}", "    "))


def _render_absent(symbol: str) -> None:
    print(f"{symbol} — how new supply enters")
    print()

    demand = _ALLOCATION_DEMAND.get(symbol)

    if demand is None:
        print(_wrap(f"{symbol} is not a digital asset this platform reads.", "  "))
        return

    print(_wrap("No mechanical issuance rule is read for this asset.", "  "))
    print()
    print(_wrap(demand, "  "))
    print()
    print(
        _wrap(
            "This is a statement about what this platform can reach, not "
            "about what the protocol discloses. Every specialist source "
            "that publishes release schedules is behind payment or a key.",
            "  ",
        )
    )


def _render_corpus(provider: IssuanceRuleProvider) -> None:
    print("How new supply enters — the corpus")
    print()
    print(
        _wrap(
            "Two kinds of supply system, and the split does not follow "
            "capped against uncapped. A rule creates supply on a schedule "
            "anyone can re-run; an allocation releases supply that already "
            "exists, on terms this platform cannot read.",
            "  ",
        )
    )
    print()

    print(f"  {'':7s} {'mechanism':22s} {'what could change it':24s} path")

    for symbol in sorted(ASSIGNMENTS):
        rule = provider.rule(symbol)

        if rule is None:
            print(f"  {symbol:7s} {'allocation release':22s} {'—':24s} not reachable")
            continue

        print(
            f"  {symbol:7s} {rule.mechanism.stated:22s} "
            f"{rule.mutability.stated:24s} "
            + ("reproducible" if rule.is_projectable else "—")
        )


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + (" " * 2 if text.startswith(("-", "·")) else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return IssuanceCommand().run(symbol)
