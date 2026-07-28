from app.domain.committee_vote import CommitteeVote
from app.services.dossiers.investment_case_builder import (
    InvestmentCaseBuilder,
)


def test_builds_investment_dossier() -> None:
    votes = (
        CommitteeVote(
            committee="Market",
            recommendation="BUY",
            confidence=90,
            weight=0.25,
            rationale="Positive market conditions.",
        ),
    )

    dossier = InvestmentCaseBuilder().build(
        symbol="MSFT",
        name="Microsoft",
        executive_score=91,
        committee_votes=votes,
    )

    assert dossier.symbol == "MSFT"
    assert dossier.name == "Microsoft"
    assert dossier.executive_score == 91
    assert dossier.committee_votes == votes
    assert dossier.generated_at is not None
