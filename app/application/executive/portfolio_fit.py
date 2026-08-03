"""How much room this portfolio has for this security."""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_snapshot import PortfolioSnapshot


class PortfolioFit:
    """
    Measure whether a new position in this security would fit the policy.

    Fit is a question about a pair — this security, this portfolio — and it
    used to be answered without reference to the security at all. What was
    scored was the portfolio's diversification and its distance from its own
    policy, which is identical whichever security is being judged, so every
    candidate received the same number and no candidate could pass or fail
    on its own merits.

    Worse, both terms ran backwards. The account was marked down for holding
    nine positions rather than twenty, and marked down again for sitting in
    cash against a 5% target. Both are arguments for buying something. Both
    were being used to refuse to recommend buying anything, and the only
    action that would have improved either was the action being blocked.

    What is measured here is room. Two things the policy states outright:

    Funding room — how much of the account is cash the policy does not want
    held as cash. An account at its cash target has nothing spare, and a new
    position would have to be funded by selling an existing one.

    Concentration room — how much of the single-position limit this security
    has left. A security the investor does not hold has all of it; one
    already at the limit has none, and adding to it would breach the policy.

    Asset-class room — how much of the policy's ceiling for this kind of
    asset is left. Measured only when the security's class is known and the
    account is fully classified, because a ceiling compared against a
    partly-identified portfolio understates what is already held.
    """

    def measure(
        self,
        symbol: str,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        asset_class: AssetClass | None = None,
    ) -> int | None:
        """Fit as a 0-100 score, or None when no term can be measured."""

        rooms = [
            room
            for room in (
                self._funding_room(portfolio, policy),
                self._concentration_room(symbol, portfolio, policy),
                self._asset_class_room(asset_class, portfolio, policy),
            )
            if room is not None
        ]

        if not rooms:
            return None

        return round(sum(rooms) / len(rooms) * 100)

    @staticmethod
    def _funding_room(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> float | None:
        """The share of the account that is cash the policy wants deployed."""

        target = policy.target.cash

        if not 0.0 <= target < 100.0:
            return None

        spare = portfolio.allocation.cash - target

        return max(0.0, min(spare / (100.0 - target), 1.0))

    @staticmethod
    def _asset_class_room(
        asset_class: AssetClass | None,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> float | None:
        """How much of the policy's ceiling for this asset class is left."""

        if asset_class is not AssetClass.CRYPTO:
            # Crypto is the only class the policy puts a ceiling on. The
            # others have targets, and a target is something to rebalance
            # towards rather than a limit a new position can breach.
            return None

        limit = policy.constraints.max_crypto

        if limit <= 0 or portfolio.allocation.unclassified > 0:
            return None

        return max(0.0, min((limit - portfolio.allocation.crypto) / limit, 1.0))

    @staticmethod
    def _concentration_room(
        symbol: str,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> float | None:
        """How much of the single-position limit this security has left."""

        limit = policy.constraints.max_single_position

        if limit <= 0.0:
            return None

        if portfolio.total_value <= 0.0:
            return None

        normalized = symbol.upper().strip()

        held = sum(
            holding.market_value_usd
            for holding in portfolio.holdings
            if holding.symbol.upper().strip() == normalized
        )

        weight = held / portfolio.total_value * 100.0

        return max(0.0, min((limit - weight) / limit, 1.0))
