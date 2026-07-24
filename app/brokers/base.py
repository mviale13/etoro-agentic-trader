from typing import Protocol

from app.domain.account_snapshot import AccountSnapshot


class AccountBroker(Protocol):
    async def snapshot(self) -> AccountSnapshot:
        ...
