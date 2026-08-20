"""Capacity reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.capacity_assessment import (
    CapacityAssessment,
)
from app.brain import Brain
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_snapshot import PortfolioSnapshot


class CapacityAnalyst:
    """
    Measure how much room the account has to act.

    Three terms, each a comparison the policy states outright:

    Funding room — cash above the policy's cash target. An account at its
    target has nothing spare, and a new position would have to be funded by
    selling an existing one.

    Single-position headroom — how far the largest holding sits from the
    single-position limit. Served signed: a holding over its limit is a
    measured breach, not a zero.

    Crypto headroom — how far crypto exposure sits under the policy's
    ceiling, the one asset class the policy limits rather than targets.
    Unmeasured while any of the account is unclassified, because a ceiling
    compared against a partly-identified portfolio understates what is
    already held.
    """

    def assess(
        self,
        source: Brain,
    ) -> CapacityAssessment:
        portfolio = source.portfolio
        policy = source.investment_policy

        unmeasured: list[str] = []

        cash_target, funding_pct, funding_usd = self._funding_room(
            portfolio,
            policy,
            unmeasured,
        )

        limit, largest_pct, headroom = self._single_position_headroom(
            portfolio,
            policy,
            unmeasured,
        )

        crypto_limit, crypto_actual, crypto_headroom = self._crypto_headroom(
            portfolio,
            policy,
            unmeasured,
        )

        return CapacityAssessment(
            cash_actual_pct=portfolio.allocation.cash,
            cash_target_pct=cash_target,
            funding_room_pct=funding_pct,
            funding_room_usd=funding_usd,
            single_position_limit_pct=limit,
            largest_position=portfolio.largest_position or None,
            largest_position_pct=largest_pct,
            single_position_headroom_pct=headroom,
            crypto_limit_pct=crypto_limit,
            crypto_actual_pct=crypto_actual,
            crypto_headroom_pct=crypto_headroom,
            unmeasured=tuple(unmeasured),
        )

    @staticmethod
    def _funding_room(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        unmeasured: list[str],
    ) -> tuple[float | None, float | None, float | None]:
        """Cash above target, in points of the account and in dollars."""

        target = policy.target.cash

        if not 0.0 <= target < 100.0:
            unmeasured.append(
                "The policy does not state a usable cash target, "
                "so funding room cannot be measured."
            )

            return None, None, None

        cash = portfolio.allocation.cash

        if cash is None:
            unmeasured.append(
                "The broker stated no cash figure, so funding room cannot be measured."
            )

            return None, None, None

        spare = max(0.0, cash - target)

        if portfolio.total_value <= 0.0:
            unmeasured.append(
                "The account reports no value, "
                "so funding room cannot be stated in dollars."
            )

            return target, spare, None

        return target, spare, spare / 100.0 * portfolio.total_value

    @staticmethod
    def _single_position_headroom(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        unmeasured: list[str],
    ) -> tuple[float | None, float | None, float | None]:
        """Signed distance between the largest holding and its limit."""

        limit = policy.constraints.max_single_position

        if limit <= 0.0:
            unmeasured.append(
                "The policy sets no single-position limit "
                "to measure concentration headroom against."
            )

            return None, portfolio.largest_position_pct or None, None

        if not portfolio.largest_position:
            # An account with no holdings has the whole limit ahead of it.
            return limit, None, limit

        largest = portfolio.largest_position_pct

        return limit, largest, limit - largest

    @staticmethod
    def _crypto_headroom(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        unmeasured: list[str],
    ) -> tuple[float | None, float | None, float | None]:
        """Signed room under the policy's crypto ceiling."""

        limit = policy.constraints.max_crypto

        if limit <= 0.0:
            unmeasured.append("The policy sets no crypto ceiling to measure against.")

            return None, None, None

        if portfolio.allocation.unclassified > 0.0:
            unmeasured.append(
                f"{portfolio.allocation.unclassified:.1f}% of the account "
                "is unclassified, so crypto exposure cannot be fully "
                "measured against its ceiling."
            )

            return limit, None, None

        crypto = portfolio.allocation.crypto

        return limit, crypto, limit - crypto
