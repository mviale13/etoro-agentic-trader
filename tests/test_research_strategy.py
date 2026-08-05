"""The plan the analysts are run from is built from the playbook itself."""

from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.services.research_strategy import PlaybookResearchStrategy


def test_the_plan_is_the_playbook_and_cannot_drift_from_it() -> None:
    """
    The playbook is what the investor is shown; the plan is what runs.

    Deriving one from the other is what stops them disagreeing. A dossier
    saying a bank is read without a cash-flow analyst, while the executor
    ran one anyway, would be the platform describing an analysis it did
    not perform.
    """

    playbook = PLAYBOOKS[PlaybookKind.BANK]

    plan = PlaybookResearchStrategy(playbook).create_plan()

    assert plan.analyst_keys == playbook.analysts
    assert plan.questions == playbook.priorities
    assert plan.objective == playbook.explanation


def test_a_playbook_that_asks_no_analysts_produces_a_plan_that_asks_none() -> None:
    """
    A digital asset publishes no accounts, and the plan says exactly that.

    This used to be impossible: a plan was required to name at least one
    analyst, so a security with nothing to analyse could not be described
    and was simply skipped instead.
    """

    plan = PlaybookResearchStrategy(PLAYBOOKS[PlaybookKind.DIGITAL_ASSET]).create_plan()

    assert plan.analyst_keys == ()
    assert plan.questions
