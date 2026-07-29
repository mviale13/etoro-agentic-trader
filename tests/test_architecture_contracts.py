"""Contract tests for the first Sprint 50 architecture slice."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.contracts import Analyst, Committee, Reasoner


@dataclass(frozen=True, slots=True)
class ExampleContext:
    symbol: str


@dataclass(frozen=True, slots=True)
class ExampleReport:
    symbol: str
    score: int


@dataclass(frozen=True, slots=True)
class ExampleDecision:
    recommendation: str


@dataclass(frozen=True, slots=True)
class ExampleReasoning:
    summary: str


class ExampleAnalyst:
    @property
    def name(self) -> str:
        return "example_analyst"

    def analyze(self, context: ExampleContext) -> ExampleReport:
        return ExampleReport(symbol=context.symbol, score=80)


class ExampleCommittee:
    @property
    def name(self) -> str:
        return "example_committee"

    def deliberate(
        self,
        reports: Sequence[ExampleReport],
    ) -> ExampleDecision:
        average = sum(report.score for report in reports) / len(reports)
        recommendation = "INCREASE" if average >= 70 else "HOLD"
        return ExampleDecision(recommendation=recommendation)


class ExampleReasoner:
    @property
    def name(self) -> str:
        return "example_reasoner"

    def reason(self, context: ExampleContext) -> ExampleReasoning:
        return ExampleReasoning(summary=f"Reasoning for {context.symbol}")


def test_analyst_contract_is_structural() -> None:
    analyst = ExampleAnalyst()
    assert isinstance(analyst, Analyst)
    assert analyst.analyze(ExampleContext(symbol="MSFT")).score == 80


def test_committee_contract_is_structural() -> None:
    committee = ExampleCommittee()
    reports = [ExampleReport(symbol="MSFT", score=80)]
    assert isinstance(committee, Committee)
    assert committee.deliberate(reports).recommendation == "INCREASE"


def test_reasoner_contract_is_structural() -> None:
    reasoner = ExampleReasoner()
    assert isinstance(reasoner, Reasoner)
    assert reasoner.reason(ExampleContext(symbol="MSFT")).summary == (
        "Reasoning for MSFT"
    )
