from app.domain.committee_vote import (
    CommitteeVote,
)
from app.domain.market_facts import MarketFacts


class MarketCommittee:
    EQUITY_SYMBOLS = (
        "SPY",
        "QQQ",
        "IWM",
    )

    def vote(
        self,
        facts: MarketFacts,
    ) -> CommitteeVote:
        equity_facts = [
            fact
            for symbol in self.EQUITY_SYMBOLS
            if (fact := facts.quote(symbol)) is not None
        ]

        positive = sum(fact.change_percent > 0 for fact in equity_facts)
        negative = sum(fact.change_percent < 0 for fact in equity_facts)

        evidence = [
            (f"{fact.symbol}: {fact.change_percent:+.2f}%") for fact in equity_facts
        ]

        if facts.vix is not None:
            evidence.append(f"VIX: {facts.vix:.2f}")

        if negative >= 2 and facts.vix is not None and facts.vix > 25:
            return CommitteeVote(
                committee="Market",
                recommendation="WAIT",
                confidence=85,
                weight=0.20,
                rationale=(
                    "Broad equity weakness and "
                    "elevated volatility indicate "
                    "unsupportive market conditions."
                ),
                evidence=tuple(evidence),
            )

        if positive >= 2 and facts.vix is not None and facts.vix < 20:
            return CommitteeVote(
                committee="Market",
                recommendation="BUY",
                confidence=80,
                weight=0.20,
                rationale=(
                    "Broad equity participation and "
                    "contained volatility indicate "
                    "supportive conditions today."
                ),
                evidence=tuple(evidence),
            )

        return CommitteeVote(
            committee="Market",
            recommendation="HOLD",
            confidence=65,
            weight=0.20,
            rationale=("Current market evidence is mixed or incomplete."),
            evidence=tuple(evidence),
        )
