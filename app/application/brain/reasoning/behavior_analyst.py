"""Behavior reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
)
from app.brain import Brain
from app.domain.investment_policy import InvestmentPolicy
from app.domain.portfolio_snapshot import PortfolioSnapshot


class BehaviorAnalyst:
    """Evaluates investor behaviour and potential biases."""

    def assess(
        self,
        source: Brain,
    ) -> BehaviorAssessment:
        portfolio = source.portfolio
        policy = source.investment_policy

        discipline = self._discipline_score(portfolio)
        emotional_risk = self._emotional_risk(portfolio)

        biases: list[str] = []
        positives: list[str] = []
        evidence: list[Evidence] = []

        policy_alignment = self._policy_alignment(
            portfolio,
            policy,
            biases,
            positives,
            evidence,
        )

        if portfolio.allocation.cash is not None and portfolio.allocation.cash > 40:
            biases.append("Possible hesitation to deploy capital")
            evidence.append(
                Evidence(
                    description=(
                        f"Cash allocation is {portfolio.allocation.cash:.1f}%."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.90,
                )
            )
        else:
            positives.append("Capital is largely invested")

        if portfolio.positions >= 10:
            positives.append("Well diversified portfolio")

        if portfolio.largest_position_pct > 25:
            biases.append("Potential concentration bias")
            evidence.append(
                Evidence(
                    description=(
                        f"Largest holding represents "
                        f"{portfolio.largest_position_pct:.1f}% "
                        "of the portfolio."
                    ),
                    source="PortfolioSnapshot",
                    strength=0.85,
                )
            )

        return BehaviorAssessment(
            discipline_score=discipline,
            # Behavioural consistency compares the investor's own actions
            # over time. The journal records what the Artificial CIO decided,
            # not what the investor did with those decisions, so this still
            # reports the neutral midpoint rather than implying an
            # observation that was never made.
            consistency_score=0.50,
            emotional_risk_score=emotional_risk,
            policy_alignment_score=policy_alignment,
            confidence=0.75 if policy is not None else 0.50,
            observed_biases=tuple(biases),
            positive_behaviors=tuple(positives),
            evidence=tuple(evidence),
        )

    def _policy_alignment(
        self,
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy | None,
        biases: list[str],
        positives: list[str],
        evidence: list[Evidence],
    ) -> float:
        """
        Score how far the portfolio sits from its own Investment Policy.

        Only limits the portfolio can actually be measured against are
        scored. The crypto limit is one of them now that holdings carry an
        asset class; while they did not, comparing them to the policy's
        stock, ETF and crypto targets would have reported drift that
        reflected the missing classification rather than the investor.
        """

        if policy is None:
            biases.append("No investment policy is configured")

            return 0.50

        alignment = 1.0

        alignment -= self._concentration_penalty(
            portfolio,
            policy,
            biases,
            positives,
            evidence,
        )

        alignment -= self._cash_penalty(
            portfolio,
            policy,
            biases,
            positives,
            evidence,
        )

        alignment -= self._crypto_penalty(
            portfolio,
            policy,
            biases,
            positives,
            evidence,
        )

        return max(0.0, min(1.0, alignment))

    @staticmethod
    def _crypto_penalty(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        biases: list[str],
        positives: list[str],
        evidence: list[Evidence],
    ) -> float:
        """
        Score the crypto holding against the policy's own ceiling.

        Measured only where there is something to measure. An account whose
        holdings could not all be classified is not scored against this
        limit, because the share below the ceiling would be understated by
        exactly the part nobody could identify.
        """

        limit = policy.constraints.max_crypto

        if limit <= 0 or portfolio.allocation.unclassified > 0:
            return 0.0

        held = portfolio.allocation.crypto

        if held <= limit:
            positives.append("Crypto exposure is within the policy limit")
            return 0.0

        overage = held - limit

        biases.append("Crypto exposure exceeds the policy limit")
        evidence.append(
            Evidence(
                description=(
                    f"Crypto is {held:.1f}% of the portfolio, against a "
                    f"{limit:.1f}% policy limit."
                ),
                source="InvestmentPolicy",
                strength=0.95,
            )
        )

        # A breach of twice the limit exhausts this third of the score.
        return min(0.34, (overage / limit) * 0.34)

    @staticmethod
    def _concentration_penalty(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        biases: list[str],
        positives: list[str],
        evidence: list[Evidence],
    ) -> float:
        limit = policy.constraints.max_single_position

        if limit <= 0:
            return 0.0

        largest = portfolio.largest_position_pct

        if largest <= limit:
            positives.append("Position sizing respects the investment policy")
            return 0.0

        overage = largest - limit

        biases.append("Largest position exceeds the policy limit")
        evidence.append(
            Evidence(
                description=(
                    f"{portfolio.largest_position or 'The largest holding'} is "
                    f"{largest:.1f}% of the portfolio, against a "
                    f"{limit:.1f}% policy limit."
                ),
                source="InvestmentPolicy",
                strength=0.95,
            )
        )

        # A breach of twice the limit exhausts this half of the score.
        return min(0.5, (overage / limit) * 0.5)

    @staticmethod
    def _cash_penalty(
        portfolio: PortfolioSnapshot,
        policy: InvestmentPolicy,
        biases: list[str],
        positives: list[str],
        evidence: list[Evidence],
    ) -> float:
        target = policy.target.cash
        threshold = policy.constraints.rebalance_threshold
        cash = portfolio.allocation.cash

        if cash is None:
            # No drift claim either way. Silence here would read as "within
            # the band", which is a finding about an allocation nobody read.
            biases.append(
                "Cash allocation could not be read, so drift against the "
                "policy band is unmeasured"
            )

            return 0.0

        drift = abs(cash - target)

        if threshold <= 0 or drift <= threshold:
            positives.append("Cash allocation is within its rebalance band")
            return 0.0

        biases.append("Cash allocation has drifted beyond its rebalance band")
        evidence.append(
            Evidence(
                description=(
                    f"Cash is {cash:.1f}% against a "
                    f"{target:.1f}% target, a drift of {drift:.1f} "
                    f"percentage points beyond the {threshold:.1f} point band."
                ),
                source="InvestmentPolicy",
                strength=0.95,
            )
        )

        # A drift of three bands exhausts this half of the score.
        return min(0.5, (drift - threshold) / (threshold * 3) * 0.5)

    def _discipline_score(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        if portfolio.positions >= 10:
            return 0.90
        if portfolio.positions >= 5:
            return 0.70
        return 0.40

    def _emotional_risk(
        self,
        portfolio: PortfolioSnapshot,
    ) -> float:
        cash = portfolio.allocation.cash

        if cash is None:
            # The midpoint of the band this factor can express, and the
            # only value that adds no cash-derived signal in either
            # direction. Named in `_cash_penalty` rather than hidden.
            return 0.50
        if cash > 40:
            return 0.70
        if cash > 20:
            return 0.50
        return 0.20
