import uuid

import httpx

from app.config import Settings
from app.models import ExecutionResult, TradeProposal


class EtoroBroker:
    def __init__(self, settings: Settings):
        self.s = settings

    def headers(self) -> dict[str, str]:
        if not self.s.etoro_api_key or not self.s.etoro_user_key:
            raise RuntimeError("Missing eToro API credentials")
        return {
            "x-api-key": self.s.etoro_api_key,
            "x-user-key": self.s.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
            "content-type": "application/json",
        }

    async def resolve_instrument(self, symbol: str) -> int:
        url = f"{self.s.etoro_base_url}/api/v1/market-data/search"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                url,
                params={"internalSymbolFull": symbol},
                headers=self.headers(),
            )
            response.raise_for_status()
            body = response.json()

        candidates = body.get("items") or body.get("data") or body.get("instruments") or []
        for item in candidates:
            candidate = str(
                item.get("internalSymbolFull") or item.get("symbol") or ""
            ).upper()
            if candidate == symbol.upper():
                value = item.get("InstrumentID") or item.get("instrumentId")
                if value is not None:
                    return int(value)
        raise RuntimeError(f"Unable to resolve instrument ID for {symbol}")

    def order_endpoint(self) -> str:
        if self.s.trading_mode == "demo":
            return "/api/v1/trading/execution/demo/orders"
        if self.s.trading_mode == "real":
            if not self.s.live_gate_open:
                raise RuntimeError("Live trading safety gate is closed")
            return "/api/v1/trading/execution/real/orders"
        raise RuntimeError("eToro execution only supports demo or real mode")

    async def execute(self, proposal: TradeProposal, amount_usd: float) -> ExecutionResult:
        instrument_id = proposal.instrument_id or await self.resolve_instrument(proposal.symbol)
        payload = {
            "instrumentId": instrument_id,
            "amount": amount_usd,
            "leverage": proposal.leverage,
            "direction": proposal.side.value,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.s.etoro_base_url}{self.order_endpoint()}",
                json=payload,
                headers=self.headers(),
            )
            response.raise_for_status()
            body = response.json()

        adjusted = proposal.model_copy(
            update={"amount_usd": amount_usd, "instrument_id": instrument_id}
        )
        return ExecutionResult(
            status="submitted",
            broker=f"etoro-{self.s.trading_mode}",
            proposal=adjusted,
            broker_response=body,
        )
