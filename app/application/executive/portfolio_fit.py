"""How much room this portfolio has for this security."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.asset_class import AssetClass
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class FitTerm:
    """
    One kind of room the policy leaves, as a share and as a sentence.

    Every term words itself, including when there is nothing to measure it
    against. A term that simply vanished from the list would leave the
    average looking like the whole answer, and the reader with no way to
    know which of three questions the policy could actually answer.
    """

    #: The share of that room still free, from 0.0 to 1.0. None where the
    #: policy states nothing this could be measured against.
    room: float | None

    #: The term as the investor reads it, figures included.
    stated: str


@dataclass(frozen=True, slots=True)
class PortfolioFitMeasure:
    """How much room this portfolio has for this security, and on what."""

    #: 0-100, or None when no term could be measured at all.
    score: int | None

    #: Every term the measure considered, measured or not, in order.
    terms: tuple[FitTerm, ...]

    @property
    def stated_terms(self) -> tuple[str, ...]:
        return tuple(term.stated for term in self.terms)


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
    ) -> PortfolioFitMeasure:
        """Fit as a 0-100 score, with every term it was averaged from."""

        terms = (
            self._funding_room(portfolio, policy),
            self._concentration_room(symbol, portfolio, policy),
            self._asset_class_room(asset_class, portfolio, policy),
        )

        rooms = [term.room for term in terms if term.room is not None]

        return PortfolioFitMeasure(
            score=round(sum(rooms) / len(rooms) * 100) if rooms else None,
            terms=terms,
        )

    @staticmethod
    def _funding_room(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> FitTerm:
        """The share of the account that is cash the policy wants deployed."""

        target = policy.target.cash

        if not 0.0 <= target < 100.0:
            return FitTerm(
                room=None,
                stated=(
                    "Funding room is not measured: the policy states no cash "
                    "target to deploy against."
                ),
            )

        cash = portfolio.allocation.cash

        if cash is None:
            return FitTerm(
                room=None,
                stated=(
                    "Funding room is not measured: the broker stated no "
                    "cash figure to deploy against."
                ),
            )

        room = max(0.0, min((cash - target) / (100.0 - target), 1.0))

        return FitTerm(
            room=room,
            stated=(
                f"Funding room {room:.0%} — cash is {cash:.1f}% of the account "
                f"against a {target:.1f}% target."
            ),
        )

    @staticmethod
    def _asset_class_room(
        asset_class: AssetClass | None,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> FitTerm:
        """How much of the policy's ceiling for this asset class is left."""

        if asset_class is not AssetClass.CRYPTO:
            # Crypto is the only class the policy puts a ceiling on. The
            # others have targets, and a target is something to rebalance
            # towards rather than a limit a new position can breach.
            return FitTerm(
                room=None,
                stated=(
                    "Asset-class room is not measured: the policy caps crypto "
                    "only, and the other classes carry targets rather than "
                    "limits a new position could breach."
                ),
            )

        limit = policy.constraints.max_crypto

        if limit <= 0:
            return FitTerm(
                room=None,
                stated="Crypto room is not measured: the policy states no ceiling.",
            )

        unclassified = portfolio.allocation.unclassified

        if unclassified > 0:
            return FitTerm(
                room=None,
                stated=(
                    f"Crypto room is not measured: {unclassified:.1f}% of the "
                    "account is unclassified, so what is already held cannot "
                    "be compared against the ceiling."
                ),
            )

        crypto = portfolio.allocation.crypto

        room = max(0.0, min((limit - crypto) / limit, 1.0))

        return FitTerm(
            room=room,
            stated=(
                f"Crypto room {room:.0%} — crypto is {crypto:.1f}% of the "
                f"account against a {limit:.1f}% ceiling."
            ),
        )

    @staticmethod
    def _concentration_room(
        symbol: str,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
    ) -> FitTerm:
        """How much of the single-position limit this security has left."""

        limit = policy.constraints.max_single_position

        if limit <= 0.0:
            return FitTerm(
                room=None,
                stated=(
                    "Concentration room is not measured: the policy states no "
                    "single-position limit."
                ),
            )

        if portfolio.total_value <= 0.0:
            return FitTerm(
                room=None,
                stated=(
                    "Concentration room is not measured: the account has no "
                    "value to weigh a position against."
                ),
            )

        normalized = symbol.upper().strip()

        held = sum(
            holding.market_value_usd
            for holding in portfolio.holdings
            if holding.symbol.upper().strip() == normalized
        )

        weight = held / portfolio.total_value * 100.0

        room = max(0.0, min((limit - weight) / limit, 1.0))

        return FitTerm(
            room=room,
            stated=(
                f"Concentration room {room:.0%} — {normalized} is {weight:.1f}% "
                f"of the account against a {limit:.1f}% single-position limit."
            ),
        )
