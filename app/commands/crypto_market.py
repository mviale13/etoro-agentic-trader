"""What kind of crypto market an asset is trading inside.

Two readings. Without a symbol it shows the environment: the market's
own state, its breadth, and the universes each aggregate was computed
over. With one it adds that asset's place in it — its returns, its peer
group and why that group, and the arithmetic between them.

Read-only, like every surface in this phase: it asks the store what the
last cycle left behind and stops. No provider is called, no model is
asked, nothing is stored.

**Nothing here is a verdict.** There is no band, no traffic light and no
regime label. A difference in percentage points is a measurement; what
it is worth to a decision is a question for a layer that does not exist.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_market import CryptoMarketSnapshot, MarketMetric
from app.domain.crypto_market_context import CryptoMarketContext
from app.domain.market_peer_group import PEER_GROUPS
from app.services.crypto_market_service import CryptoMarketService

#: The order the environment reads in — state, then breadth.
_SNAPSHOT_ORDER = (
    MarketMetric.TOTAL_MARKET_CAP,
    MarketMetric.MARKET_CAP_CHANGE,
    MarketMetric.MARKET_RETURN,
    MarketMetric.TOTAL_VOLUME,
    MarketMetric.VOLUME_CHANGE,
    MarketMetric.BTC_DOMINANCE,
    MarketMetric.ETH_DOMINANCE,
    MarketMetric.STABLECOIN_SHARE,
    MarketMetric.ADVANCING,
    MarketMetric.DECLINING,
    MarketMetric.TRACKED_ASSETS,
)


class CryptoMarketCommand:
    def run(self, symbol: str | None = None) -> int:
        service = CryptoMarketService()

        if symbol is None:
            snapshot = service.established()

            _render_snapshot(snapshot)

            if not snapshot.is_read:
                return 1

            _render_corpus(service)

            return 0

        normalized = symbol.upper().strip()

        context = service.context(normalized, AssetClass.CRYPTO)

        if context is None:
            print(f"{normalized} — no market context: this is not a digital asset.")
            return 1

        _render_snapshot(context.snapshot)
        _render_context(context)

        return 0 if context.is_read else 1


# ── the environment ─────────────────────────────────────────────────


def _render_snapshot(snapshot: CryptoMarketSnapshot) -> None:
    print("CRYPTO MARKET")
    print("=" * 60)

    if not snapshot.is_read:
        print()
        print(_wrap(snapshot.unavailable_because or "Nothing has been read.", "  "))
        print()
        return

    print(f"  {snapshot.source}, read {snapshot.observed_at:%Y-%m-%d %H:%M} UTC")
    print()

    for metric in _SNAPSHOT_ORDER:
        held = snapshot.observation(metric)

        if held is None:
            continue

        measure = held.measure
        mark = "·" if measure.derived else " "

        print(
            f"  {mark} {measure.label:<38}{held.interval.value:>8}  "
            f"{held.stated or held.standing.stated:>12}"
        )

    if snapshot.universes:
        print()
        print("  · computed by MOVRvest over:")

        for universe in snapshot.universes:
            print(_wrap(f"- {universe.described}", "    "))

    print()
    print(
        _wrap(
            "Every figure above is one provider's claim. A total market "
            "capitalisation is not independently reproducible — the "
            "universe is the vendor's own — so nothing here is corroborated.",
            "  ",
        )
    )
    print()


def _render_corpus(service: CryptoMarketService) -> None:
    print("RELATIVE PERFORMANCE — 24 hours, the one aligned interval")
    print("=" * 60)
    print()

    for symbol in sorted(PEER_GROUPS):
        context = service.context(symbol, AssetClass.CRYPTO)

        if context is None:
            continue

        peer = context.peer

        group = peer.group.name if peer is not None and peer.group else "—"

        against_market = context.relative_to("the crypto market")
        against_peers = (
            context.relative_to(peer.group.name)
            if peer is not None and peer.group
            else None
        )

        print(
            f"  {symbol:<6} {group:<14} "
            f"vs market {_delta(against_market):>10}   "
            f"vs peers {_delta(against_peers):>10}"
        )

    print()


def _delta(relative: object) -> str:
    delta = getattr(relative, "delta", None)

    return f"{delta:+.2f} pp" if isinstance(delta, float) else "—"


# ── one asset ───────────────────────────────────────────────────────


def _render_context(context: CryptoMarketContext) -> None:
    print(f"{context.symbol} — market context")
    print("=" * 60)

    if context.unavailable_because:
        print()
        print(_wrap(context.unavailable_because, "  "))
        print()
        return

    print()
    print("  Its own returns")

    for held in context.returns:
        print(f"    {held.interval.value:>5}  {held.stated or held.standing.stated}")

    peer = context.peer

    print()

    if peer is None or peer.group is None:
        print("  Peer group — none")
        print(
            _wrap(
                (peer.unavailable_because if peer is not None else "") or "",
                "    ",
            )
        )
    else:
        print(f"  Peer group — {peer.group.name} ({peer.group.provider})")
        print(_wrap(f"Selected because {peer.group.selected_because}", "    "))

        for caveat in peer.group.caveats:
            print(_wrap(f"Caveat: {caveat}", "    "))

        for held in context.peer_observations:
            print(
                f"    {held.measure.label:<36}{held.interval.value:>8}  "
                f"{held.stated or held.standing.stated:>12}"
            )

    if peer is not None and peer.considered:
        print()
        print("  Considered and not used")

        for considered in peer.considered:
            print(_wrap(f"- {considered.name}: {considered.rejected_because}", "    "))

    if context.relative:
        print()
        print("  Relative performance — MOVRvest arithmetic")

        for relative in context.relative:
            print(_wrap(f"- {relative.stated}", "    "))

            if relative.caveat:
                print(_wrap(f"  {relative.caveat}", "    "))

    if context.concentrations:
        print()
        print("  How much of each comparator this asset is")

        for concentration in context.concentrations:
            print(_wrap(f"- {concentration.stated}", "    "))

    if context.uncompared:
        print()
        print(
            _wrap(
                "No comparator was published at "
                + ", ".join(interval.value for interval in context.uncompared)
                + ": the provider reports asset returns at four intervals "
                "and market and category figures at one, so 24 hours is "
                "the only window where a difference means anything.",
                "  ",
            )
        )

    print()


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return CryptoMarketCommand().run(symbol)
