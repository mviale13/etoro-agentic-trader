"""Report what the configured eToro credentials can reach."""

from app.brokers.etoro_identity import EtoroIdentityBroker
from app.config import Settings


class CredentialsCommand:
    async def run(self) -> int:
        settings = Settings()

        grant = await EtoroIdentityBroker(settings).fetch()

        print()
        print("MOVRvest — eToro credentials")
        print("══════════════════════════════════════")
        print()
        print(f"Permissions     : {grant.stated}")
        print(f"Write scopes    : {len(grant.write_scopes)} of {len(grant.scopes)}")
        print(f"Real account    : {grant.real_account_id or 'not reported'}")
        print(f"Demo account    : {grant.demo_account_id or 'not reported'}")
        print(f"Trading mode    : {settings.trading_mode}")
        print()

        if grant.can_trade_real:
            # Stated every time, not once. The platform never calls a
            # state-changing route, but a key that could is a standing
            # fact about the account, not a one-off notice.
            print("This key can place real-money orders.")
            print("Nothing in MOVRvest places orders; the permission exists anyway.")
            print()

        return 0


async def run() -> int:
    return await CredentialsCommand().run()
