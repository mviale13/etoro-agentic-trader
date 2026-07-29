from app.application.executive.executive_committee import ExecutiveCommittee


def test_executive_committee_exists() -> None:
    assert ExecutiveCommittee() is not None
