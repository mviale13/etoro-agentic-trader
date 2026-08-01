import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import Settings
from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_position import PortfolioPosition
from app.infrastructure.evidence import VersionedSnapshotStore


class EtoroAccountBroker:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        evidence_store: VersionedSnapshotStore | None = None,
    ) -> None:
        self.settings = settings
        self._client = client
        self._evidence_store = evidence_store or VersionedSnapshotStore()

    def _headers(self) -> dict[str, str]:
        if not self.settings.etoro_api_key or not self.settings.etoro_user_key:
            raise RuntimeError(
                "Missing ETORO_API_KEY or ETORO_USER_KEY in the local .env file"
            )

        return {
            "x-api-key": self.settings.etoro_api_key,
            "x-user-key": self.settings.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
        }

    def _pnl_path(self) -> str:
        if self.settings.trading_mode == "demo":
            return "/api/v1/trading/info/demo/pnl"

        if self.settings.trading_mode == "real":
            return "/api/v1/trading/info/real/pnl"

        raise RuntimeError(
            "Account status requires TRADING_MODE=demo or TRADING_MODE=real"
        )

    async def _fetch_pnl(self) -> tuple[dict[str, Any], float]:
        started = time.perf_counter()
        path = self._pnl_path()
        url = f"{self.settings.etoro_base_url}{path}"
        headers = self._headers()

        if self._client is not None:
            response = await self._client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)

        latency_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()

        body = response.json()

        if not isinstance(body, dict):
            raise RuntimeError("Unexpected eToro P&L response format")

        self._evidence_store.save(
            broker="etoro",
            environment=self.settings.trading_mode,
            endpoint="pnl",
            payload=body,
            metadata={
                "http_method": "GET",
                "http_status": response.status_code,
                "request_path": path,
                "request_id": headers["x-request-id"],
                "latency_ms": round(latency_ms, 3),
                "response_headers": dict(response.headers),
            },
        )

        return body, latency_ms

    @staticmethod
    def _portfolio_payload(body: dict[str, Any]) -> dict[str, Any]:
        expected = {"positions", "ordersForOpen", "orders", "mirrors", "credit"}

        if expected.intersection(body):
            return body

        queue: list[dict[str, Any]] = [
            value for value in body.values() if isinstance(value, dict)
        ]

        while queue:
            candidate = queue.pop(0)

            if expected.intersection(candidate):
                return candidate

            queue.extend(
                value for value in candidate.values() if isinstance(value, dict)
            )

        return body

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _manual_pending_market_orders(
        cls,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        orders = payload.get("ordersForOpen") or []

        return [
            order
            for order in orders
            if isinstance(order, dict)
            and cls._number(order.get("mirrorID", order.get("mirrorId", 0))) == 0
        ]

    @classmethod
    def _build_positions(
        cls,
        payload_positions: list[Any],
    ) -> tuple[PortfolioPosition, ...]:
        """
        Report each holding the broker returned.

        eToro identifies holdings by instrument id; ticker symbols are
        resolved later, during perception.
        """

        positions: list[PortfolioPosition] = []

        for raw in payload_positions:
            if not isinstance(raw, dict):
                continue

            invested = cls._number(raw.get("amount"))
            unrealized = cls._number((raw.get("unrealizedPnL") or {}).get("pnL"))

            exposure = (raw.get("unrealizedPnL") or {}).get("exposureInAccountCurrency")

            market_value = (
                cls._number(exposure) if exposure is not None else invested + unrealized
            )

            positions.append(
                PortfolioPosition(
                    symbol="",
                    quantity=cls._number(raw.get("units")),
                    invested_usd=round(invested, 2),
                    market_value_usd=round(market_value, 2),
                    unrealized_pnl_usd=round(unrealized, 2),
                    instrument_id=int(cls._number(raw.get("instrumentID"))),
                )
            )

        return tuple(positions)

    @classmethod
    def _calculate_values(
        cls,
        payload: dict[str, Any],
    ) -> tuple[float | None, float, float, float | None]:
        positions = [
            item for item in (payload.get("positions") or []) if isinstance(item, dict)
        ]
        orders = [
            item for item in (payload.get("orders") or []) if isinstance(item, dict)
        ]
        mirrors = [
            item for item in (payload.get("mirrors") or []) if isinstance(item, dict)
        ]
        manual_pending = cls._manual_pending_market_orders(payload)

        credit_raw = payload.get("credit")
        credit = None if credit_raw is None else cls._number(credit_raw)

        pending_amount = sum(
            cls._number(order.get("amount")) for order in manual_pending
        )
        pending_amount += sum(cls._number(order.get("amount")) for order in orders)

        cash = None if credit is None else credit - pending_amount

        invested = sum(cls._number(position.get("amount")) for position in positions)
        invested += pending_amount
        invested += sum(
            cls._number(order.get("totalExternalCosts")) for order in manual_pending
        )

        unrealized = sum(
            cls._number((position.get("unrealizedPnL") or {}).get("pnL"))
            for position in positions
        )

        for mirror in mirrors:
            mirror_positions = [
                item
                for item in (mirror.get("positions") or [])
                if isinstance(item, dict)
            ]

            invested += sum(
                cls._number(position.get("amount")) for position in mirror_positions
            )
            invested += cls._number(mirror.get("availableAmount")) - cls._number(
                mirror.get("closedPositionsNetProfit")
            )

            unrealized += sum(
                cls._number((position.get("unrealizedPnL") or {}).get("pnL"))
                for position in mirror_positions
            )
            unrealized += cls._number(mirror.get("closedPositionsNetProfit"))

        equity = None if cash is None else cash + invested + unrealized

        return cash, invested, unrealized, equity

    async def snapshot(self) -> AccountSnapshot:
        body, latency_ms = await self._fetch_pnl()
        payload = self._portfolio_payload(body)

        positions = payload.get("positions") or []
        orders_for_open = payload.get("ordersForOpen") or []
        orders = payload.get("orders") or []
        mirrors = payload.get("mirrors") or []

        cash, invested, unrealized, equity = self._calculate_values(payload)

        return AccountSnapshot(
            broker="eToro",
            mode=self.settings.trading_mode,
            connected=True,
            positions_count=len(positions),
            positions=self._build_positions(positions),
            pending_orders=len(orders_for_open) + len(orders),
            copy_portfolios=len(mirrors),
            latency_ms=round(latency_ms, 1),
            timestamp=datetime.now(UTC),
            cash_usd=cash,
            invested_usd=invested,
            unrealized_pnl_usd=unrealized,
            equity_usd=equity,
        )
