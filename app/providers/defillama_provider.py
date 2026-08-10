"""Read an economic system's figures from DefiLlama, once a day.

The first protocol-fundamentals claimant. Its payloads terminate here:
what leaves this module is a `ProtocolClaimSet` — entity key, metric,
value, window, the provider's own methodology sentence — and nothing
downstream knows a slug, a `dataType` or an endpoint shape.

Three things the S2 measurement established about this source, all of
which this adapter encodes rather than assumes:

- **Its entities are not interchangeable.** `hyperliquid` is a *parent*
  protocol aggregating three books; `hyperliquid-l1` is the chain. The
  slug map below is per canonical entity, hand-verified, and a wrong
  entry produces the wrong business by two orders of magnitude rather
  than a visible error.
- **Methodology lives on the children.** The parent publishes none, so
  the child adapters' own sentences are read and carried — that text is
  what says 99% of Hyperliquid's fees buy HYPE.
- **Its cumulative fields lie about levels.** For open interest,
  `total1y` is a sum of daily snapshots and means nothing. Only the
  level and its changes are read.

Keyless and free. Its derivatives *volume* endpoints answer 402; open
interest does not, which corrected an earlier classification.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

from app.domain.protocol_fundamentals import ProtocolMetric
from app.domain.provenance import Provenance
from app.infrastructure.cache.json_cache import CachedEntry, JsonCache


class ProtocolFactsUnavailable(LookupError):
    """Nothing could be read, and the reason is worded for a caller."""


@dataclass(frozen=True, slots=True)
class ProtocolMetricClaim:
    """One provider figure for one metric, unjudged."""

    metric: ProtocolMetric
    value: float
    window: str | None

    #: The provider's own definition for this entity, verbatim.
    methodology: str | None = None

    #: Day-over-day movement, where the provider publishes one.
    change_24h: float | None = None


@dataclass(frozen=True, slots=True)
class ProtocolClaimSet:
    """One provider's claims about one economic entity.

    The adapter boundary. A second protocol-data source produces this
    same object and joins the pool; nothing canonical changes.
    """

    entity_key: str
    source: str
    read: Provenance
    claims: tuple[ProtocolMetricClaim, ...]

    #: The metrics this provider publishes a *definition* for on this
    #: entity, whether or not it reported a value.
    #:
    #: The difference between two absences that look identical.
    #: DefiLlama's methodology for Bitcoin defines fees and revenue and
    #: says nothing about holder revenue — because the concept does not
    #: exist for that chain, not because today's figure was missing. A
    #: metric the source never defines here is a question that does not
    #: apply; one it defines and did not answer is a gap.
    defines: frozenset[ProtocolMetric] = frozenset()

    def claim(self, metric: ProtocolMetric) -> ProtocolMetricClaim | None:
        for item in self.claims:
            if item.metric is metric:
                return item

        return None


#: The provider's slug for each canonical entity, hand-verified.
_SLUGS = {
    "hyperliquid-protocol": "hyperliquid",
    "hyperliquid-l1-chain": "hyperliquid-l1",
    "ethereum-chain": "ethereum",
    "solana-chain": "solana",
    "cardano-chain": "cardano",
    "arbitrum-chain": "arbitrum",
    "bitcoin-chain": "bitcoin",
    "bittensor-chain": "bittensor",
    "1inch-protocol": "1inch",
}

#: Which entities have a TVL worth reading, and under which shape.
#: A chain's TVL comes from the chain list; a protocol's from its own
#: endpoint. Asking the wrong one returns another entity's capital.
_CHAIN_TVL_NAMES = {
    "hyperliquid-l1-chain": "Hyperliquid L1",
    "ethereum-chain": "Ethereum",
    "solana-chain": "Solana",
    "cardano-chain": "Cardano",
    "arbitrum-chain": "Arbitrum",
    "bitcoin-chain": "Bitcoin",
    "bittensor-chain": "Bittensor",
}

_PROTOCOL_TVL_SLUGS = {
    "hyperliquid-protocol": "hyperliquid",
}

#: The entities whose own spot venue this platform reads a volume for.
#:
#: 1inch is deliberately absent. It is an aggregator: it routes trades
#: to other venues rather than running a book, so its "volume" is a
#: different concept from a venue's own. The provider's DEX list holds
#: *1inch Aqua* — a separate product this platform has not mapped —
#: and reading that under the aggregator's name would attribute one
#: business's activity to another.
_DEX_SLUGS = {
    "hyperliquid-protocol": "hyperliquid-spot-orderbook",
}

#: The entities with a derivatives book whose open interest is free.
_OPEN_INTEREST_SLUGS = {
    "hyperliquid-protocol": "hyperliquid-perps",
}

_FEE_TYPES = (
    (ProtocolMetric.FEES, "dailyFees"),
    (ProtocolMetric.PROTOCOL_REVENUE, "dailyRevenue"),
    (ProtocolMetric.HOLDER_REVENUE, "dailyHoldersRevenue"),
)

#: Where an aggregate entity's definitions actually live.
#:
#: A parent protocol publishes figures and no methodology; its children
#: publish the sentences. Those sentences are the evidence — "99% of
#: fees go to Assistance Fund for buying HYPE tokens" is the
#: value-accrual mechanism, in the source's own words — so they are
#: read from the children and carried with the child named.
_METHODOLOGY_CHILDREN = {
    "hyperliquid-protocol": (
        "hyperliquid-perps",
        "hyperliquid-spot-orderbook",
        "hyperliquid-hlp",
    ),
}

#: Which methodology key describes which metric, in the provider's
#: own vocabulary.
_METHODOLOGY_KEYS = {
    ProtocolMetric.FEES: "Fees",
    ProtocolMetric.PROTOCOL_REVENUE: "Revenue",
    ProtocolMetric.HOLDER_REVENUE: "HoldersRevenue",
    ProtocolMetric.DEX_VOLUME: "Fees",
    ProtocolMetric.OPEN_INTEREST: "Fees",
}


class DefiLlamaProvider:
    """One entity's economic figures, or a worded refusal."""

    SOURCE = "DefiLlama"

    BASE = "https://api.llama.fi"

    TIMEOUT = 40

    #: The provider is keyless and generous; this is courtesy pacing
    #: for a batch, not a rate limit anyone imposed.
    PACE = 1.2

    def claims(self, entity_key: str) -> ProtocolClaimSet:
        slug = _SLUGS.get(entity_key)

        if slug is None:
            raise ProtocolFactsUnavailable(
                f"{self.SOURCE} is not asked about {entity_key}: this "
                "platform has not verified which entity it means by it."
            )

        collected: list[ProtocolMetricClaim] = []
        defines: set[ProtocolMetric] = set()
        observed_at = datetime.now(UTC)

        # An aggregate entity's definitions live on its children.
        inherited = self._child_methodology(entity_key)

        for metric, data_type in _FEE_TYPES:
            payload = self._get(f"/summary/fees/{slug}?dataType={data_type}")

            if payload is None:
                continue

            # What the source *defines* here, read once from the first
            # payload that carries a methodology: it is the entity's,
            # not the data type's.
            defines |= self._defined_metrics(payload)

            claim = self._fee_claim(payload, metric, inherited.get(metric))

            if claim is not None:
                collected.append(claim)

                if claim.methodology:
                    defines.add(metric)

        tvl = self._tvl_claim(entity_key)

        if tvl is not None:
            collected.append(tvl)

        for metric, slugs, path in (
            (ProtocolMetric.DEX_VOLUME, _DEX_SLUGS, "dexs"),
            (ProtocolMetric.OPEN_INTEREST, _OPEN_INTEREST_SLUGS, "open-interest"),
        ):
            venue = slugs.get(entity_key)

            if venue is None:
                continue

            claim = self._venue_claim(venue, metric, path)

            if claim is not None:
                collected.append(claim)
                defines.add(metric)

        if not collected:
            raise ProtocolFactsUnavailable(
                f"{self.SOURCE} publishes nothing this platform reads for {entity_key}."
            )

        # TVL is defined for every entity this platform asks about it.
        if any(item.metric is ProtocolMetric.TVL for item in collected):
            defines.add(ProtocolMetric.TVL)

        return ProtocolClaimSet(
            entity_key=entity_key,
            source=self.SOURCE,
            read=Provenance(source=self.SOURCE, observed_at=observed_at),
            claims=tuple(collected),
            defines=frozenset(defines),
        )

    # ── the endpoints ───────────────────────────────────────────────

    @staticmethod
    def _defined_metrics(payload: dict[str, Any]) -> set[ProtocolMetric]:
        """Which fee-family metrics this entity's methodology defines."""

        methodology = payload.get("methodology")

        if not isinstance(methodology, dict):
            return set()

        return {
            metric
            for metric, key in (
                (ProtocolMetric.FEES, "Fees"),
                (ProtocolMetric.PROTOCOL_REVENUE, "Revenue"),
                (ProtocolMetric.HOLDER_REVENUE, "HoldersRevenue"),
            )
            if isinstance(methodology.get(key), str) and methodology[key].strip()
        }

    def _child_methodology(
        self,
        entity_key: str,
    ) -> dict[ProtocolMetric, str]:
        """The definitions an aggregate entity inherits from its children.

        Composed with each child named, because the books differ: the
        perpetuals venue and the spot order book route their fees under
        separate rules, and flattening them into one sentence would
        invent a mechanism neither describes.
        """

        children = _METHODOLOGY_CHILDREN.get(entity_key, ())

        collected: dict[ProtocolMetric, list[str]] = {}

        for child in children:
            payload = self._get(f"/summary/fees/{child}")

            if payload is None:
                continue

            name = str(payload.get("displayName") or payload.get("name") or child)

            for metric in (
                ProtocolMetric.FEES,
                ProtocolMetric.PROTOCOL_REVENUE,
                ProtocolMetric.HOLDER_REVENUE,
            ):
                text = self._methodology(payload, metric)

                if text:
                    collected.setdefault(metric, []).append(f"{name}: {text}")

        return {metric: " ".join(lines) for metric, lines in collected.items()}

    def _fee_claim(
        self,
        payload: dict[str, Any],
        metric: ProtocolMetric,
        inherited: str | None = None,
    ) -> ProtocolMetricClaim | None:
        value = self._amount(payload.get("total24h"))

        if value is None:
            return None

        return ProtocolMetricClaim(
            metric=metric,
            value=value,
            window="24 hours",
            methodology=self._methodology(payload, metric) or inherited,
            change_24h=self._fraction(payload.get("change_1d")),
        )

    def _tvl_claim(self, entity_key: str) -> ProtocolMetricClaim | None:
        protocol_slug = _PROTOCOL_TVL_SLUGS.get(entity_key)

        if protocol_slug is not None:
            payload = self._get_raw(f"/tvl/{protocol_slug}")

            value = self._amount(payload)

            return (
                None
                if value is None
                else ProtocolMetricClaim(
                    metric=ProtocolMetric.TVL,
                    value=value,
                    window=None,
                    methodology=(
                        "Value of assets held across the protocol's own "
                        "contracts, as the provider computes it."
                    ),
                )
            )

        chain_name = _CHAIN_TVL_NAMES.get(entity_key)

        if chain_name is None:
            return None

        chains = self._get_raw("/v2/chains")

        if not isinstance(chains, list):
            return None

        for chain in chains:
            if isinstance(chain, dict) and chain.get("name") == chain_name:
                value = self._amount(chain.get("tvl"))

                return (
                    None
                    if value is None
                    else ProtocolMetricClaim(
                        metric=ProtocolMetric.TVL,
                        value=value,
                        window=None,
                        methodology=(
                            "Value of assets held in protocols deployed "
                            "on this chain, as the provider computes it."
                        ),
                    )
                )

        return None

    def _venue_claim(
        self,
        venue_slug: str,
        metric: ProtocolMetric,
        path: str,
    ) -> ProtocolMetricClaim | None:
        payload = self._get(
            f"/overview/{path}?excludeTotalDataChart=true"
            "&excludeTotalDataChartBreakdown=true"
        )

        if payload is None:
            return None

        for row in payload.get("protocols") or []:
            if not isinstance(row, dict) or row.get("slug") != venue_slug:
                continue

            value = self._amount(row.get("total24h"))

            if value is None:
                return None

            return ProtocolMetricClaim(
                metric=metric,
                value=value,
                # Open interest is a level the provider happens to
                # publish in a field named for a window. Carrying that
                # window would make a stock read as a flow.
                window=(None if metric is ProtocolMetric.OPEN_INTEREST else "24 hours"),
                methodology=self._methodology(row, metric),
                change_24h=self._fraction(row.get("change_1d")),
            )

        return None

    # ── plumbing ────────────────────────────────────────────────────

    def _get(self, path: str) -> dict[str, Any] | None:
        payload = self._get_raw(path)

        return payload if isinstance(payload, dict) else None

    def _get_raw(self, path: str) -> Any:
        try:
            response = requests.get(
                f"{self.BASE}{path}",
                headers={
                    "accept": "application/json",
                    "user-agent": "movrvest/1.0",
                },
                timeout=self.TIMEOUT,
            )
        except Exception:
            return None

        time.sleep(self.PACE)

        if not response.ok:
            # 402 on the derivatives endpoints: published, and behind a
            # paywall. Absent for this platform, and reported as such.
            return None

        try:
            return response.json()
        except ValueError:
            return None

    @staticmethod
    def _methodology(payload: dict[str, Any], metric: ProtocolMetric) -> str | None:
        """The provider's own sentence for this metric, verbatim."""

        methodology = payload.get("methodology")

        if not isinstance(methodology, dict):
            return None

        text = methodology.get(_METHODOLOGY_KEYS[metric])

        return str(text).strip() if isinstance(text, str) and text.strip() else None

    @staticmethod
    def _amount(value: object) -> float | None:
        """A figure, where the provider reported one; zero is absence."""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) if value else None

        return None

    @staticmethod
    def _fraction(value: object) -> float | None:
        """A percentage movement, carried as a fraction. Zero is real."""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) / 100.0

        return None


class CachedDefiLlamaProvider:
    """The entity's figures once a day, behind the platform's two doors."""

    def __init__(
        self,
        provider: DefiLlamaProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or DefiLlamaProvider()
        self._cache = cache or JsonCache("data/cache/protocol_facts")
        self._acquires = acquires

    @classmethod
    def stored(
        cls,
        cache: JsonCache | None = None,
    ) -> CachedDefiLlamaProvider:
        """The claims already read, and no others."""

        return cls(cache=cache, acquires=False)

    def claims(self, entity_key: str) -> ProtocolClaimSet | None:
        entry = self._cache.read(entity_key)

        held = self._restore(entry, entity_key) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            claims = self._provider.claims(entity_key)
        except Exception:
            return held

        self._cache.write(entity_key, self._encode(claims))

        return claims

    @staticmethod
    def _encode(claims: ProtocolClaimSet) -> dict[str, Any]:
        return {
            "entity_key": claims.entity_key,
            "source": claims.source,
            "observed_at": claims.read.observed_at.isoformat(),
            "defines": sorted(metric.value for metric in claims.defines),
            "claims": [
                {
                    "metric": item.metric.value,
                    "value": item.value,
                    "window": item.window,
                    "methodology": item.methodology,
                    "change_24h": item.change_24h,
                }
                for item in claims.claims
            ],
        }

    @staticmethod
    def _restore(entry: CachedEntry, entity_key: str) -> ProtocolClaimSet | None:
        value = entry.value

        rows = value.get("claims")

        if not isinstance(rows, list) or not rows:
            return None

        claims: list[ProtocolMetricClaim] = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            try:
                metric = ProtocolMetric(str(row.get("metric")))
            except ValueError:
                continue

            amount = row.get("value")

            if not isinstance(amount, (int, float)) or isinstance(amount, bool):
                continue

            change = row.get("change_24h")

            claims.append(
                ProtocolMetricClaim(
                    metric=metric,
                    value=float(amount),
                    window=(
                        str(row["window"])
                        if isinstance(row.get("window"), str)
                        else None
                    ),
                    methodology=(
                        str(row["methodology"])
                        if isinstance(row.get("methodology"), str)
                        else None
                    ),
                    change_24h=(
                        float(change)
                        if isinstance(change, (int, float))
                        and not isinstance(change, bool)
                        else None
                    ),
                )
            )

        if not claims:
            return None

        raw_moment = value.get("observed_at")

        try:
            observed_at = (
                datetime.fromisoformat(raw_moment)
                if isinstance(raw_moment, str)
                else entry.stored_at
            )
        except ValueError:
            observed_at = entry.stored_at

        source = str(value.get("source", DefiLlamaProvider.SOURCE))

        defines: set[ProtocolMetric] = set()

        for name in value.get("defines") or ():
            try:
                defines.add(ProtocolMetric(str(name)))
            except ValueError:
                continue

        return ProtocolClaimSet(
            entity_key=str(value.get("entity_key", entity_key)),
            source=source,
            read=Provenance(source=source, observed_at=observed_at),
            claims=tuple(claims),
            defines=frozenset(defines),
        )
