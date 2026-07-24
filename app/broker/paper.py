from app.models import ExecutionResult, TradeProposal


class PaperBroker:
    async def execute(self, proposal: TradeProposal, amount_usd: float) -> ExecutionResult:
        adjusted = proposal.model_copy(update={"amount_usd": amount_usd})
        return ExecutionResult(
            status="filled-paper",
            broker="paper",
            proposal=adjusted,
            broker_response={"simulated": True, "filled_amount_usd": amount_usd},
        )
