from app.committee.value import ValueCommittee
from app.domain.committee_context import CommitteeContext
from app.domain.valuation_snapshot import ValuationSnapshot


def context(pe: float | None) -> CommitteeContext:
    return CommitteeContext(
        intelligence=None,
        portfolio=None,
        policy=None,
        valuation=ValuationSnapshot(
            forward_pe=pe,
            trailing_pe=pe,
            peg_ratio=1.2,
            dividend_yield=0.01,
        ),
    )


def test_buy_when_forward_pe_is_low():
    opinion = ValueCommittee().evaluate(context(15))

    assert opinion.vote == "BUY"


def test_hold_when_forward_pe_is_reasonable():
    opinion = ValueCommittee().evaluate(context(22))

    assert opinion.vote == "HOLD"


def test_hold_when_forward_pe_is_high():
    opinion = ValueCommittee().evaluate(context(40))

    assert opinion.vote == "HOLD"


def test_hold_when_forward_pe_missing():
    opinion = ValueCommittee().evaluate(context(None))

    assert opinion.vote == "HOLD"
