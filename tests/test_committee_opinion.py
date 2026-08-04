from dataclasses import FrozenInstanceError

import pytest

from app.domain.committee_opinion import CommitteeOpinion


def test_committee_opinion():
    opinion = CommitteeOpinion(
        member="Momentum",
        vote="BUY",
        confidence=82,
        rationale="Positive momentum.",
    )

    assert opinion.member == "Momentum"
    assert opinion.vote == "BUY"
    assert opinion.confidence == 82
    assert opinion.evidence == ()

    with pytest.raises(FrozenInstanceError):
        opinion.vote = "SELL"
