"""Risk Committee."""

from __future__ import annotations

from app.application.committees.opinion_builder import Input, build
from app.brain import Brain
from app.domain.committee.opinion import CommitteeOpinion
from app.domain.finding import Dimension, FindingLedger

#: One reading, and only one. This committee speaks for what the
#: security's own price history says about holding it.
REMIT = frozenset({Dimension.RISK})


class RiskCommittee:
    """
    Reviews the risk of holding this security.

    It used to review only the account's risk, which needs position
    history nothing records, so it abstained on every symbol —
    including securities whose own volatility and deepest fall had been
    measured from a year of prices.

    Two things it no longer does, both of which it had to be taught.
    It does not return a neutral position when it measured nothing:
    saying *hold* there read as *risk is acceptable*, which is a claim
    about a security nobody had measured. And it does not fall back to
    the account's risk, which is identical under every symbol — a
    committee that answered a question about this security with a fact
    about the portfolio was answering a different question.
    """

    def review(
        self,
        brain: Brain,
        symbol: str,
        findings: FindingLedger,
    ) -> CommitteeOpinion:

        company = brain.security_evidence(symbol)

        signal = company.signals.risk if company is not None else None

        measured = signal is not None and signal.severity is not None

        if not measured:
            return build(
                committee="Risk Committee",
                remit=REMIT,
                ledger=findings,
                abstain_because=(
                    f"The price history for {symbol} is too short to measure "
                    "its risk, so the Risk Committee takes no position. An "
                    "unmeasured risk is never reported as a safe security."
                ),
            )

        return build(
            committee="Risk Committee",
            remit=REMIT,
            ledger=findings,
            inputs=(
                Input(
                    name="price history",
                    value=1,
                ),
            ),
        )
