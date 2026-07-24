from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.proposer import propose_from_prices
from app.audit import recent, record
from app.broker.etoro import EtoroBroker
from app.broker.paper import PaperBroker
from app.config import get_settings
from app.models import PortfolioState, TradeProposal
from app.risk import RiskEngine

app = FastAPI(title="eToro Agentic Trader", version="0.2.0")
settings = get_settings()
risk_engine = RiskEngine(settings)
kill_switch = {"engaged": False}


class SignalRequest(BaseModel):
    symbol: str
    closes: list[float] = Field(min_length=30)
    amount_usd: float = Field(default=50, gt=0)


class ExecuteRequest(BaseModel):
    proposal: TradeProposal
    portfolio: PortfolioState = Field(default_factory=PortfolioState)


def get_broker():
    if settings.trading_mode == "paper":
        return PaperBroker()
    if settings.trading_mode in {"demo", "real"}:
        return EtoroBroker(settings)
    raise RuntimeError("Approval mode does not permit execution")


@app.get("/health")
def health():
    return {
        "ok": True,
        "mode": settings.trading_mode,
        "kill_switch": kill_switch["engaged"],
    }


@app.get("/config")
def config():
    return {
        "mode": settings.trading_mode,
        "live_gate_open": settings.live_gate_open,
        "allowed_symbols": settings.allowed_symbols,
        "crypto_symbols": settings.crypto_symbols,
    }


@app.post("/signals/evaluate")
def evaluate_signal(request: SignalRequest):
    proposal = propose_from_prices(
        request.symbol,
        request.closes,
        request.amount_usd,
    )
    payload = {"proposal": proposal.model_dump(mode="json") if proposal else None}
    record("signal_evaluated", {"symbol": request.symbol, **payload})
    return payload


@app.post("/orders/propose")
def validate_proposal(request: ExecuteRequest):
    decision = risk_engine.evaluate(request.proposal, request.portfolio)
    return {
        "proposal": request.proposal.model_dump(mode="json"),
        "risk": decision.model_dump(),
    }


@app.post("/orders/execute")
async def execute(request: ExecuteRequest):
    if kill_switch["engaged"]:
        raise HTTPException(423, "Kill switch is engaged")

    decision = risk_engine.evaluate(request.proposal, request.portfolio)
    if not decision.allowed or decision.adjusted_amount_usd is None:
        raise HTTPException(400, detail=decision.model_dump())

    try:
        result = await get_broker().execute(
            request.proposal,
            decision.adjusted_amount_usd,
        )
    except Exception as exc:
        record("execution_error", {"error": str(exc)})
        raise HTTPException(502, str(exc)) from exc

    record("order_executed", result.model_dump(mode="json"))
    return result


@app.post("/kill-switch/engage")
def engage():
    kill_switch["engaged"] = True
    return kill_switch


@app.post("/kill-switch/release")
def release():
    kill_switch["engaged"] = False
    return kill_switch


@app.get("/audit")
def audit(limit: int = 100):
    return recent(min(limit, 500))
