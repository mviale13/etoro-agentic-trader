from dataclasses import dataclass
from enum import StrEnum


class AnalystKey(StrEnum):
    """Stable identifiers for analysts available to research strategies."""

    GROWTH = "growth"
    PROFITABILITY = "profitability"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    TREND = "trend"


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    """Declarative plan describing what should be researched and by whom.

    A research strategy creates this plan after interpreting a company profile.
    The plan defines the research objective, the questions to investigate,
    and the specialist analysts required to perform the analysis.

    It contains no execution logic.
    """

    objective: str
    questions: tuple[str, ...]
    analyst_keys: tuple[AnalystKey, ...]

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("Research plan must define an objective")

        if not self.questions:
            raise ValueError("Research plan must contain at least one question")

        if any(not question.strip() for question in self.questions):
            raise ValueError("Research plan questions must not be blank")

        if not self.analyst_keys:
            raise ValueError("Research plan must assign at least one analyst")

        if len(set(self.analyst_keys)) != len(self.analyst_keys):
            raise ValueError("Research plan must not assign duplicate analysts")
