"""US spot-ETF flows for Bitcoin and Ethereum, and who holds the asset.

Two acquisitions, both free and keyless, both measured before being
chosen. The measurement is in
`docs/architecture/CRYPTO_INTELLIGENCE.md`: every specialist route that
publishes flows was tried, and Farside returns 777 KB of HTML while
CoinGlass and the rest want a key. SoSoValue answers a POST and returns
structured daily figures with three hundred days of history.

**A flow is a fact; what it causes is not.** This provider returns
amounts and dates. Whether inflows are *supporting* a price is an
interpretation, it belongs to whoever makes it, and nothing here makes
it.

Two different quantities, deliberately kept apart:

```text
flow      money moving through the vehicle over a day — a rate
holdings  what identifiable balance sheets hold — a stock
```

They answer different questions and this platform has been caught
before by treating a rate and a level as the same kind of thing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import requests

from app.infrastructure.cache.json_cache import JsonCache

TIMEOUT = 25

HEADERS = {
    "User-Agent": "movrvest/1.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

#: SoSoValue's own name for each fund group. Only the two the corpus
#: needs: an asset with no US spot ETF gets nothing rather than an
#: empty reading.
FUND_GROUPS = {
    "BTC": "us-btc-spot",
    "ETH": "us-eth-spot",
}

#: CoinGecko's public-treasury endpoint, per asset.
TREASURY_ASSETS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}


@dataclass(frozen=True, slots=True)
class EtfFlowReading:
    """One day's flow through a group of funds, and what they hold.

    Every field is a figure the source published. The rolling sums are
    this platform's arithmetic over the source's own daily series, and
    are named as sums rather than as trends.
    """

    symbol: str
    group: str

    source: str

    #: The date the flows settled on, which is not the date they were
    #: read. ETF data lags by days and a brief that hid that would be
    #: presenting stale figures as today's.
    as_of: date
    observed_at: datetime

    daily_net_flow: float | None = None
    total_net_assets: float | None = None
    token_holdings: float | None = None

    #: The share of the asset's supply these funds hold, as the source
    #: computes it.
    share_of_supply: float | None = None

    cumulative_net_flow: float | None = None

    #: This platform's sums over the source's daily series.
    flow_5d: float | None = None
    flow_30d: float | None = None

    #: How many of the last thirty published days were inflows.
    inflow_days_30d: int | None = None
    days_counted_30d: int | None = None

    @property
    def is_read(self) -> bool:
        return self.daily_net_flow is not None or self.total_net_assets is not None


@dataclass(frozen=True, slots=True)
class TreasuryHolding:
    """What identifiable public balance sheets hold of one asset."""

    symbol: str
    source: str
    observed_at: datetime

    companies: int
    total_holdings: float
    total_value_usd: float

    #: The source's own view of what share of the asset's market value
    #: that is.
    share_of_market_cap: float | None = None


class EtfFlowProvider:
    """One reading of the ETF flow series and the treasury holdings."""

    SOSOVALUE = "SoSoValue"
    COINGECKO = "CoinGecko"

    METRICS = "https://api.sosovalue.xyz/openapi/v2/etf/currentEtfDataMetrics"
    HISTORY = "https://api.sosovalue.xyz/openapi/v2/etf/historicalInflowChart"
    TREASURY = "https://api.coingecko.com/api/v3/companies/public_treasury"

    def flows(self, symbol: str) -> EtfFlowReading | None:
        """The latest flow reading, or None where no fund group exists.

        None for Hyperliquid is the correct answer and not a gap: there
        is no US spot ETF, so the question does not arise. Reporting an
        empty flow would invent one.
        """

        group = FUND_GROUPS.get(symbol.upper().strip())

        if group is None:
            return None

        metrics = self._post(self.METRICS, {"type": group})

        if not isinstance(metrics, dict):
            return None

        history = self._post(self.HISTORY, {"type": group})

        rolling = self._rolling(history if isinstance(history, list) else [])

        as_of = _date(_field(metrics, "dailyNetInflow", "lastUpdateDate"))

        if as_of is None:
            return None

        return EtfFlowReading(
            symbol=symbol.upper().strip(),
            group=group,
            source=self.SOSOVALUE,
            as_of=as_of,
            observed_at=datetime.now(UTC),
            daily_net_flow=_number(_field(metrics, "dailyNetInflow", "value")),
            total_net_assets=_number(_field(metrics, "totalNetAssets", "value")),
            token_holdings=_number(_field(metrics, "totalTokenHoldings", "value")),
            share_of_supply=_number(
                _field(metrics, "totalNetAssetsPercentage", "value")
            ),
            cumulative_net_flow=_number(_field(metrics, "cumNetInflow", "value")),
            **rolling,
        )

    @staticmethod
    def _rolling(rows: list[Any]) -> dict[str, Any]:
        """Sums over the source's own daily series, newest first.

        Named `flow_5d` rather than `weekly trend`: adding five numbers
        the source published is arithmetic, and calling it a trend would
        be a reading this platform has not earned.
        """

        daily: list[float] = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            value = _number(row.get("totalNetInflow"))

            if value is not None:
                daily.append(value)

        if not daily:
            return {}

        # The series arrives newest-first; the head is the recent window.
        window = daily[:30]

        return {
            "flow_5d": sum(daily[:5]) if len(daily) >= 5 else None,
            "flow_30d": sum(window) if len(window) >= 5 else None,
            "inflow_days_30d": sum(1 for value in window if value > 0),
            "days_counted_30d": len(window),
        }

    def treasuries(self, symbol: str) -> TreasuryHolding | None:
        """What public companies hold, as one source counts them."""

        asset = TREASURY_ASSETS.get(symbol.upper().strip())

        if asset is None:
            return None

        payload = self._get(f"{self.TREASURY}/{asset}")

        if not isinstance(payload, dict):
            return None

        holdings = _number(payload.get("total_holdings"))
        value = _number(payload.get("total_value_usd"))
        companies = payload.get("companies")

        if holdings is None or value is None or not isinstance(companies, list):
            return None

        return TreasuryHolding(
            symbol=symbol.upper().strip(),
            source=self.COINGECKO,
            observed_at=datetime.now(UTC),
            companies=len(companies),
            total_holdings=holdings,
            total_value_usd=value,
            share_of_market_cap=_number(payload.get("market_cap_dominance")),
        )

    # ── the wire ────────────────────────────────────────────────────

    @staticmethod
    def _post(url: str, body: dict[str, str]) -> Any:
        response = requests.post(url, json=body, timeout=TIMEOUT, headers=HEADERS)

        response.raise_for_status()

        payload = response.json()

        return payload.get("data") if isinstance(payload, dict) else None

    @staticmethod
    def _get(url: str) -> Any:
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": HEADERS["User-Agent"]},
        )

        response.raise_for_status()

        return response.json()


class CachedEtfFlowProvider:
    """Flows once a day, behind the platform's two doors."""

    #: 1 — the shape S5.4 introduced.
    SCHEMA = 1

    def __init__(
        self,
        provider: EtfFlowProvider | None = None,
        cache: JsonCache | None = None,
        acquires: bool = True,
    ) -> None:
        self._provider = provider or EtfFlowProvider()
        self._cache = cache or JsonCache(
            "data/cache/etf_flows",
            schema=self.SCHEMA,
        )
        self._acquires = acquires

    @classmethod
    def stored(cls, cache: JsonCache | None = None) -> CachedEtfFlowProvider:
        """What has already been read, and nothing else."""

        return cls(cache=cache, acquires=False)

    def flows(self, symbol: str) -> EtfFlowReading | None:
        key = f"flows.{symbol.upper().strip()}"

        entry = self._cache.read(key)

        held = _decode_flow(entry.value) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            reading = self._provider.flows(symbol)
        except Exception:
            return held

        if reading is not None:
            self._cache.write(key, _encode_flow(reading))

        return reading

    def treasuries(self, symbol: str) -> TreasuryHolding | None:
        key = f"treasury.{symbol.upper().strip()}"

        entry = self._cache.read(key)

        held = _decode_treasury(entry.value) if entry is not None else None

        if held is not None and entry is not None:
            if not self._acquires or entry.is_from_today():
                return held

        if not self._acquires:
            return None

        try:
            reading = self._provider.treasuries(symbol)
        except Exception:
            return held

        if reading is not None:
            self._cache.write(key, _encode_treasury(reading))

        return reading


# ── the store ───────────────────────────────────────────────────────


def _encode_flow(reading: EtfFlowReading) -> dict[str, Any]:
    return {
        "symbol": reading.symbol,
        "group": reading.group,
        "source": reading.source,
        "as_of": reading.as_of.isoformat(),
        "observed_at": reading.observed_at.isoformat(),
        "daily_net_flow": reading.daily_net_flow,
        "total_net_assets": reading.total_net_assets,
        "token_holdings": reading.token_holdings,
        "share_of_supply": reading.share_of_supply,
        "cumulative_net_flow": reading.cumulative_net_flow,
        "flow_5d": reading.flow_5d,
        "flow_30d": reading.flow_30d,
        "inflow_days_30d": reading.inflow_days_30d,
        "days_counted_30d": reading.days_counted_30d,
    }


def _decode_flow(row: Any) -> EtfFlowReading | None:
    if not isinstance(row, dict):
        return None

    try:
        return EtfFlowReading(
            symbol=str(row["symbol"]),
            group=str(row["group"]),
            source=str(row["source"]),
            as_of=date.fromisoformat(str(row["as_of"])),
            observed_at=datetime.fromisoformat(str(row["observed_at"])),
            daily_net_flow=_number(row.get("daily_net_flow")),
            total_net_assets=_number(row.get("total_net_assets")),
            token_holdings=_number(row.get("token_holdings")),
            share_of_supply=_number(row.get("share_of_supply")),
            cumulative_net_flow=_number(row.get("cumulative_net_flow")),
            flow_5d=_number(row.get("flow_5d")),
            flow_30d=_number(row.get("flow_30d")),
            inflow_days_30d=(
                int(row["inflow_days_30d"])
                if row.get("inflow_days_30d") is not None
                else None
            ),
            days_counted_30d=(
                int(row["days_counted_30d"])
                if row.get("days_counted_30d") is not None
                else None
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _encode_treasury(holding: TreasuryHolding) -> dict[str, Any]:
    return {
        "symbol": holding.symbol,
        "source": holding.source,
        "observed_at": holding.observed_at.isoformat(),
        "companies": holding.companies,
        "total_holdings": holding.total_holdings,
        "total_value_usd": holding.total_value_usd,
        "share_of_market_cap": holding.share_of_market_cap,
    }


def _decode_treasury(row: Any) -> TreasuryHolding | None:
    if not isinstance(row, dict):
        return None

    try:
        return TreasuryHolding(
            symbol=str(row["symbol"]),
            source=str(row["source"]),
            observed_at=datetime.fromisoformat(str(row["observed_at"])),
            companies=int(row["companies"]),
            total_holdings=float(row["total_holdings"]),
            total_value_usd=float(row["total_value_usd"]),
            share_of_market_cap=_number(row.get("share_of_market_cap")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _field(payload: dict[str, Any], name: str, key: str) -> Any:
    value = payload.get(name)

    return value.get(key) if isinstance(value, dict) else None


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
