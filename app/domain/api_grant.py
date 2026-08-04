"""What the platform's own credentials are allowed to do."""

from __future__ import annotations

from dataclasses import dataclass

#: The suffix eToro puts on every permission that can change something.
#:
#: Capability is read off this rather than off a list of known scope
#: names. The published documentation names the trading scopes
#: `etoro-public:real:write` and `etoro-public:demo:write`; the live API
#: returns `etoro-public:trade.real:write` and `etoro-public:trade.demo:write`,
#: alongside a dozen others the documentation does not mention at all.
#: Matching a known list failed open — a key able to trade the real account
#: was reported read-only, which is the most dangerous direction for that
#: mistake to run. Anything ending in `:write` is a write.
WRITE_SUFFIX = ":write"

#: The scope observed to grant real-money trading.
REAL_TRADING_SCOPE = "etoro-public:trade.real:write"

#: The same, on the simulated account.
DEMO_TRADING_SCOPE = "etoro-public:trade.demo:write"


@dataclass(frozen=True, slots=True)
class ApiGrant:
    """
    What the configured credentials may reach, as eToro reports it.

    The platform reads. Nothing in it calls a state-changing route — but a
    key carrying write scope means the permission exists, and a permission
    that exists is one a future bug can reach. Knowing what is granted is
    the difference between "we do not trade" as a property of the code and
    as a property of the credentials.

    Only identifiers and scopes are kept. The response also carries a name,
    a date of birth and a gender, which the raw archive preserves and no
    reasoning here needs.
    """

    scopes: tuple[str, ...] = ()

    gcid: int | None = None
    real_account_id: int | None = None
    demo_account_id: int | None = None

    def permits(self, scope: str) -> bool:
        return scope in self.scopes

    @property
    def write_scopes(self) -> tuple[str, ...]:
        """Every granted permission that can change something."""

        return tuple(scope for scope in self.scopes if scope.endswith(WRITE_SUFFIX))

    @property
    def can_trade_real(self) -> bool:
        """Whether these credentials could place an order with real money."""

        return self.permits(REAL_TRADING_SCOPE)

    @property
    def can_trade_demo(self) -> bool:
        return self.permits(DEMO_TRADING_SCOPE)

    @property
    def is_read_only(self) -> bool:
        """True only when nothing granted can change anything."""

        return bool(self.scopes) and not self.write_scopes

    @property
    def stated(self) -> str:
        """
        What these credentials can do, in a line.

        Real-money trading is named first and explicitly. The remaining
        write permissions are counted rather than dismissed: this platform
        does not know what all of them reach, and summarising them as
        harmless would be a claim it cannot support.
        """

        if not self.scopes:
            return "no scopes reported"

        writes = self.write_scopes

        if not writes:
            return "read-only"

        if self.can_trade_real:
            return (
                f"can place real-money orders, and holds {len(writes)} "
                "write permissions in total"
            )

        if self.can_trade_demo:
            return (
                f"can trade the demo account, and holds {len(writes)} "
                "write permissions in total"
            )

        return f"holds {len(writes)} write permissions"

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, object],
    ) -> ApiGrant:
        """
        Read the grant out of `GET /api/v1/me`.

        Absent fields stay absent. A missing `scopes` array is not read as
        "no permissions" — it means eToro did not say, and a credential
        whose reach is unknown is not reported as harmless.
        """

        raw = payload.get("scopes")

        scopes = (
            tuple(item for item in raw if isinstance(item, str))
            if isinstance(raw, list)
            else ()
        )

        return cls(
            scopes=scopes,
            gcid=cls._identifier(payload.get("gcid")),
            real_account_id=cls._identifier(payload.get("realCid")),
            demo_account_id=cls._identifier(payload.get("demoCid")),
        )

    @staticmethod
    def _identifier(value: object) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None
