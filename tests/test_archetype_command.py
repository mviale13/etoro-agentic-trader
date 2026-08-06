"""`movrvest archetype` explains an absence as fully as an answer."""

import asyncio

import pytest

from app.commands import archetype as command
from app.domain.company_knowledge import RevenueModel
from app.services.company_knowledge_service import KnowledgeOutcome, KnowledgeState
from tests.test_archetype_engine import company, segment


class KnowledgeStub:
    """The knowledge service, answering however a reading needs it to."""

    def __init__(self, outcome: KnowledgeOutcome) -> None:
        self._outcome = outcome

    async def knowledge(self, symbol: str) -> KnowledgeOutcome:
        return self._outcome


@pytest.fixture
def _no_reading(monkeypatch: pytest.MonkeyPatch):
    """
    Nothing here fetches a filing or calls a model.

    Structural rather than incidental: the command's own dependency is
    replaced, so a test cannot pass by happening not to reach the
    network. Each test installs the outcome it needs.
    """

    def install(outcome: KnowledgeOutcome) -> None:
        monkeypatch.setattr(
            command, "CompanyKnowledgeService", lambda: KnowledgeStub(outcome)
        )

    return install


def test_a_security_with_no_filing_read_is_told_so_and_offered_no_industry(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    The substitution this whole layer exists to stop making. A company
    whose report has not been read has no archetype, and the honest
    answer is that — never the sector its data provider reports.
    """

    _no_reading(
        KnowledgeOutcome(
            state=KnowledgeState.UNAVAILABLE,
            absent_because="No provider holds an annual report for ACME.",
        )
    )

    exit_code = asyncio.run(command.run("acme"))
    printed = capsys.readouterr().out

    assert exit_code == 1
    assert "ACME — not classified" in printed
    assert "No provider holds an annual report for ACME." in printed
    assert "no industry is substituted for it" in printed


def test_an_undecided_archetype_shows_the_reason_and_every_missing_dimension(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Meta's shape. A reader who sees "not classified" needs to know
    whether the gap is in the filing or in this platform's reading of
    it, and only one of those is worth acting on.
    """

    _no_reading(
        KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=company(
                "META",
                segment(
                    "Family of Apps",
                    share=0.99,
                    row=1,
                    undescribed="quotes words the document prints under 'Reality Labs'",
                ),
                segment(
                    "Reality Labs", share=0.01, row=2, undescribed="404 characters"
                ),
            ),
        )
    )

    exit_code = asyncio.run(command.run("META"))
    printed = capsys.readouterr().out

    assert exit_code == 0
    assert "META — Not classified" in printed
    assert "not established:" in printed
    assert "Family of Apps — way of earning" in printed
    assert "quotes words the document prints under 'Reality Labs'" in printed

    # The measurement that did survive is still reported: a missing
    # description is not evidence against a proven size.
    assert "measured: 100%" in printed


def test_a_decided_archetype_shows_the_rule_that_decided_it(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    NVIDIA's shape. The answer comes first, for a reader who trusts it;
    the rule and the coverage it read come next, for one who does not.
    """

    _no_reading(
        KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=company(
                "NVDA",
                segment(
                    "Compute & Networking",
                    share=0.90,
                    row=1,
                    earns=(RevenueModel.MANUFACTURING, RevenueModel.LICENSING),
                ),
                segment(
                    "Graphics", share=0.10, row=2, earns=(RevenueModel.MANUFACTURING,)
                ),
            ),
        )
    )

    exit_code = asyncio.run(command.run("NVDA"))
    printed = capsys.readouterr().out

    assert exit_code == 0
    assert "NVDA — Manufacturer" in printed
    assert "one-way-of-earning-leads" in printed
    assert "manufacturing: segments worth 100% of the revenue total" in printed
    assert "via Compute & Networking, Graphics" in printed


def test_segment_figures_above_the_consolidated_total_are_explained(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    Disney's segments sum to 102% of the total they are divided by,
    because segment figures include revenue the segments billed each
    other. Unexplained, a coverage above 100% reads as a bug.
    """

    _no_reading(
        KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=company(
                "DIS",
                segment(
                    "Entertainment", share=0.45, row=1, earns=(RevenueModel.LICENSING,)
                ),
                segment("Sports", share=0.19, row=2, earns=(RevenueModel.LICENSING,)),
                segment(
                    "Experiences", share=0.38, row=3, earns=(RevenueModel.LICENSING,)
                ),
            ),
        )
    )

    asyncio.run(command.run("DIS"))
    printed = capsys.readouterr().out

    assert "above 100%" in printed
    assert "billed each other" in printed


def test_coverage_is_never_worded_as_a_share_of_revenue(
    _no_reading,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    "Segments worth 90% of revenue license as well as manufacture" is
    supportable. "90% of revenue comes from licensing" is not, and no
    filing establishes it.

    The distinction is one relabelling away from being lost — a surface
    that calls this a revenue mix asserts a measurement nobody printed —
    so the wording is held by a test rather than by a docstring.
    """

    _no_reading(
        KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=company(
                "NVDA",
                segment(
                    "Compute",
                    share=0.90,
                    row=1,
                    earns=(RevenueModel.MANUFACTURING, RevenueModel.LICENSING),
                ),
                segment(
                    "Graphics", share=0.10, row=2, earns=(RevenueModel.MANUFACTURING,)
                ),
            ),
        )
    )

    asyncio.run(command.run("NVDA"))
    printed = capsys.readouterr().out.lower()

    assert "coverage" in printed
    assert "not how much revenue comes from it" in printed

    for forbidden in ("revenue mix", "revenue share", "of revenue comes from"):
        assert forbidden not in printed
