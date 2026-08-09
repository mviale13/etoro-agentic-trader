"""Executive Committee orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.committees.investment_committee import (
    InvestmentCommittee,
)
from app.application.committees.risk_committee import (
    RiskCommittee,
)
from app.brain import Brain
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.finding import FindingLedger


@dataclass(slots=True)
class CommitteeService:
    investment: InvestmentCommittee = field(default_factory=InvestmentCommittee)

    risk: RiskCommittee = field(default_factory=RiskCommittee)

    def review(
        self,
        brain: Brain,
        symbol: str,
        findings: FindingLedger,
    ) -> tuple[CommitteeOpinion, ...]:
        """Both committees review one investment case, not the account.

        Each is handed the same ledger and selects its own remit from
        it. Neither is shown the other's opinion: a committee that
        could see another's position could accommodate it, and the
        agreement an investor is being shown would then be partly an
        artefact of the order they ran in. Disagreement is preserved
        here and resolved one layer up, where it can be recorded.

        The reasoning snapshot no longer reaches this layer. It
        describes the account and the market, which are identical under
        every symbol, and a committee weighing them was answering a
        question about the portfolio in a paragraph about a company.
        """

        return (
            self.investment.review(brain, symbol, findings),
            self.risk.review(brain, symbol, findings),
        )
