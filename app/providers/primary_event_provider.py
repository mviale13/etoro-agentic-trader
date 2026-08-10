"""Events read from a register rather than from an account of one.

Two surfaces, both free, both keyless, both measured on 2026-08-10
before anything was built on them. What they have in common is the
reason they are worth having next to a news summary: **nobody wrote them
about an asset.** A release exists because a release shipped; an
incident is in the register because it happened. Neither was framed for
a reader, so neither needs decomposing — which makes them the only
events here whose facts are not somebody's sentences.

```text
DefiLlama /hacks     613 incidents, JSON, keyless. date, name, amount,
                     chain, technique, classification, source link.
                     Mapped to an asset by the chain it names.
GitHub /releases     the protocol's own release feed, keyless at 60
                     requests an hour. Mapped to an asset by repository.
```

**Neither is the whole family.** DefiLlama records exploits with a
quantified loss, so a disclosed vulnerability that cost nothing is not
in it; GitHub records that a client released, which is not the same as a
consensus change activating. Both absences are the honest shape of the
source and both are stated where the event is rendered, because a
platform that showed *"no security events"* from a register of *funded
losses only* would be reporting something it never checked.

**A chain is not a token.** DefiLlama's `chain` field names where an
exploit happened, and an exploit on Ethereum is not an exploit *of*
Ethereum — the Coinsbuy wallet drain is a custodian's failure that
happens to have moved ETH. So the event is attached to the asset with
its family and its subject intact, and the entity that was actually
exploited is carried in `entity` rather than silently becoming the
asset's own security record.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from app.domain.crypto_event import (
    CryptoEvent,
    EventFact,
    EventFamily,
    EventFeedHealth,
    EventStatus,
    SourceReport,
    SourceTier,
    anchors_in,
    identity_of,
)

TIMEOUT = 30

HEADERS = {"User-Agent": "movrvest/1.0", "Accept": "application/json"}


#: DefiLlama's own chain name for each asset's chain. An incident is
#: attached to an asset only where the chain is that asset's own — an
#: exploit on BSC is not a Bitcoin event however large it is.
INCIDENT_CHAINS = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "ADA": "Cardano",
    "ARB": "Arbitrum",
    "HYPE": "Hyperliquid",
}

#: The repository whose releases *are* this protocol's releases. Only
#: where one implementation is canonical enough that its release is the
#: protocol's news: Bitcoin Core and go-ethereum are, and a wallet or an
#: SDK is not. Hyperliquid publishes no release feed — measured, and the
#: reason its absence is not a gap.
RELEASE_REPOS = {
    "BTC": ("bitcoin/bitcoin", "Bitcoin Core"),
    "ETH": ("ethereum/go-ethereum", "go-ethereum"),
    "SOL": ("anza-xyz/agave", "Agave"),
}


class PrimaryEventProvider:
    """Security incidents and protocol releases, from their registers."""

    HACKS = "https://api.llama.fi/hacks"
    RELEASES = "https://api.github.com/repos/{repo}/releases"

    DEFILLAMA = "DefiLlama"
    GITHUB = "GitHub"

    def incidents(
        self,
        symbol: str,
        limit: int = 4,
    ) -> tuple[tuple[CryptoEvent, ...], EventFeedHealth]:
        """Exploits recorded against this asset's chain, newest first."""

        normalized = symbol.upper().strip()
        chain = INCIDENT_CHAINS.get(normalized)

        if chain is None:
            return (), EventFeedHealth(
                source=f"{self.DEFILLAMA} incidents",
                reached=False,
                because=f"no chain is mapped for {normalized}",
            )

        try:
            payload = self._get(self.HACKS)
        except Exception as exc:  # noqa: BLE001
            return (), EventFeedHealth(
                source=f"{self.DEFILLAMA} incidents",
                reached=False,
                because=f"{type(exc).__name__} reading the incident register",
            )

        if not isinstance(payload, list):
            return (), EventFeedHealth(
                source=f"{self.DEFILLAMA} incidents",
                reached=False,
                because="the incident register did not return a list",
            )

        rows = [
            row
            for row in payload
            if isinstance(row, dict) and chain in _chains(row.get("chain"))
        ]

        rows.sort(key=lambda row: _number(row.get("date")) or 0, reverse=True)

        events = [
            event
            for event in (self._incident(normalized, row) for row in rows[:limit])
            if event is not None
        ]

        return tuple(events), EventFeedHealth(
            source=f"{self.DEFILLAMA} incidents",
            reached=True,
            entries_seen=len(rows[:limit]),
            entries_parsed=len(events),
        )

    def _incident(self, symbol: str, row: dict[str, Any]) -> CryptoEvent | None:
        when = _number(row.get("date"))
        name = row.get("name")

        if when is None or not isinstance(name, str):
            return None

        occurred = datetime.fromtimestamp(when, UTC)

        amount = _number(row.get("amount"))

        technique = row.get("technique") or "an undisclosed technique"

        # The register publishes the loss in whole dollars. Read as
        # millions once — COLDCARD's $115m rendered as "$115,000,000.0m"
        # — which is the shape of error a units assumption always makes:
        # plausible, enormous, and invisible until it is printed.
        lost = _money(amount) if amount is not None else "an undisclosed amount"

        stated = (
            f"{name} lost {lost} on {chain_name(row)} via {technique}, "
            f"recorded {occurred:%-d %B %Y}."
        )

        headline = f"{name}: {lost} lost to {technique}"

        return CryptoEvent(
            identity=identity_of((symbol,), EventFamily.SECURITY, headline, occurred),
            symbols=(symbol,),
            family=EventFamily.SECURITY,
            headline=headline,
            occurred_at=occurred,
            published_at=occurred,
            observed_at=datetime.now(UTC),
            entity=name,
            reports=(
                SourceReport(
                    source=self.DEFILLAMA,
                    tier=SourceTier.PRIMARY,
                    text=stated,
                    url=_url(row.get("source")),
                    published_at=occurred,
                ),
            ),
            # A register entry is a record, not a paragraph: it is one
            # fact and it carries no reading, so nothing is decomposed.
            facts=(EventFact(stated=stated, anchors=anchors_in(stated)),),
            status=(
                EventStatus.ONGOING
                if not _number(row.get("returnedFunds"))
                else EventStatus.COMPLETED
            ),
        )

    def releases(
        self,
        symbol: str,
        limit: int = 2,
    ) -> tuple[tuple[CryptoEvent, ...], EventFeedHealth]:
        """This protocol's own releases, newest first."""

        normalized = symbol.upper().strip()
        mapped = RELEASE_REPOS.get(normalized)

        if mapped is None:
            return (), EventFeedHealth(
                source=f"{self.GITHUB} releases",
                reached=False,
                because=(
                    f"no canonical implementation is mapped for {normalized} — "
                    "which is a fact about the protocol, not a failed read"
                ),
            )

        repo, name = mapped

        try:
            payload = self._get(
                self.RELEASES.format(repo=repo), params={"per_page": "6"}
            )
        except Exception as exc:  # noqa: BLE001
            return (), EventFeedHealth(
                source=f"{self.GITHUB} releases",
                reached=False,
                because=f"{type(exc).__name__} reading {repo}",
            )

        if not isinstance(payload, list):
            return (), EventFeedHealth(
                source=f"{self.GITHUB} releases",
                reached=False,
                because=f"{repo} did not return a release list",
            )

        rows = [
            row
            for row in payload
            if isinstance(row, dict) and not row.get("prerelease")
        ]

        rows.sort(key=lambda row: str(row.get("published_at") or ""), reverse=True)

        events = [
            event
            for event in (
                self._release(normalized, name, repo, row) for row in rows[:limit]
            )
            if event is not None
        ]

        return tuple(events), EventFeedHealth(
            source=f"{self.GITHUB} releases",
            reached=True,
            entries_seen=len(rows[:limit]),
            entries_parsed=len(events),
        )

    def _release(
        self,
        symbol: str,
        name: str,
        repo: str,
        row: dict[str, Any],
    ) -> CryptoEvent | None:
        tag = row.get("tag_name")
        published = _time(row.get("published_at"))

        if not isinstance(tag, str) or published is None:
            return None

        headline = f"{name} {tag} released"

        stated = (
            f"{name} published release {tag} on {published:%-d %B %Y}. "
            "A client release is not by itself a consensus change: it is "
            "what the implementation shipped, and whether the network "
            "adopted it is a separate question this platform does not read."
        )

        return CryptoEvent(
            identity=identity_of(
                (symbol,), EventFamily.PROTOCOL_UPGRADE, headline, published
            ),
            symbols=(symbol,),
            family=EventFamily.PROTOCOL_UPGRADE,
            headline=headline,
            occurred_at=published,
            published_at=published,
            observed_at=datetime.now(UTC),
            entity=name,
            reports=(
                SourceReport(
                    source=f"{self.GITHUB}/{repo}",
                    tier=SourceTier.PRIMARY,
                    text=stated,
                    url=_url(row.get("html_url")),
                    published_at=published,
                ),
            ),
            facts=(EventFact(stated=stated, anchors=anchors_in(tag)),),
        )

    @staticmethod
    def _get(url: str, params: dict[str, str] | None = None) -> Any:
        response = requests.get(url, timeout=TIMEOUT, headers=HEADERS, params=params)

        response.raise_for_status()

        return response.json()


def chain_name(row: dict[str, Any]) -> str:
    chains = _chains(row.get("chain"))

    return ", ".join(chains) if chains else "an unnamed chain"


def _chains(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, str))

    return (value,) if isinstance(value, str) else ()


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _money(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.0f}m"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.0f}k"

    return f"${value:,.0f}"


def _url(value: Any) -> str | None:
    return value if isinstance(value, str) and value.startswith("http") else None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
