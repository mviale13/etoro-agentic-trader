from app.brokers.base import AccountBroker
from app.domain.account_snapshot import AccountSnapshot


class AccountService:
    def __init__(self, broker: AccountBroker) -> None:
        self.broker = broker

    async def snapshot(self) -> AccountSnapshot:
        return await self.broker.snapshot()

    async def health(self) -> bool:
        try:
            snapshot = await self.snapshot()
        except Exception:
            return False
        return snapshot.connected
