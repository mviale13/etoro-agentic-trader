"""What this platform understands about one company, from what it has read.

The consumption seam for the knowledge graph. Two layers were built and
measured over several slices — `BusinessUnderstanding`, derived from
narrative consensus, and `FinancialUnderstanding`, derived from
statement consensus — and until now the only way to see either was a
developer command. This composes them for the surfaces an investor
actually looks at.

Three properties, and each one is a rule rather than an implementation
detail:

- **It never acquires.** Both halves are read from the stores through
  the services' read-only doors. A page view must not fetch a filing or
  ask a model: that would put a spend behind a page load and make the
  dashboard the thing that decides when this platform pays. Acquisition
  stays where it has always been — explicit, and invoked by an operator.
- **It never decides.** Nothing here scores, ranks or recommends, and
  no analyst consumes it. It is the platform explaining what it knows,
  beside a recommendation that was reached without it.
- **It never compensates.** Where a half is missing, it is missing, with
  the reason worded. A company whose filing has never been read is
  reported as not understood rather than described from anything else.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.business_understanding import BusinessUnderstanding
from app.domain.financial_understanding import FinancialUnderstanding
from app.services.company_knowledge_service import CompanyKnowledgeService
from app.services.financial_engine import measure
from app.services.financial_statement_service import FinancialStatementService
from app.services.understanding_engine import understand


@dataclass(frozen=True, slots=True)
class CompanyUnderstanding:
    """Both understandings of one company, each present or worded absent.

    Deliberately two independent halves rather than one merged view.
    They rest on different documents' sections, reach quorum
    separately, and fail separately: a company whose segments are
    established and whose statements are not is a real state, and
    flattening the pair would hide which half is missing.
    """

    symbol: str

    business: BusinessUnderstanding | None
    business_absent_because: str | None

    financial: FinancialUnderstanding | None
    financial_absent_because: str | None

    @property
    def is_understood(self) -> bool:
        """Whether this platform has read anything about the company."""

        return self.business is not None or self.financial is not None


class CompanyUnderstandingService:
    """Both understandings, from stored evidence only."""

    def __init__(
        self,
        knowledge: CompanyKnowledgeService | None = None,
        statements: FinancialStatementService | None = None,
    ) -> None:
        self._knowledge = knowledge or CompanyKnowledgeService()
        self._statements = statements or FinancialStatementService()

    def understanding(self, symbol: str) -> CompanyUnderstanding:
        """What is understood about this company, without reading anything."""

        normalized = symbol.upper().strip()

        business, business_absent = self._business(normalized)
        financial, financial_absent = self._financial(normalized)

        return CompanyUnderstanding(
            symbol=normalized,
            business=business,
            business_absent_because=business_absent,
            financial=financial,
            financial_absent_because=financial_absent,
        )

    def _business(self, symbol: str) -> tuple[BusinessUnderstanding | None, str | None]:
        outcome = self._knowledge.established(symbol)

        if outcome.knowledge is None:
            return None, outcome.absent_because

        return understand(outcome.knowledge), None

    def _financial(
        self, symbol: str
    ) -> tuple[FinancialUnderstanding | None, str | None]:
        held = self._statements.established(symbol)

        if not held:
            withdrawn = self._statements.withdrawn(symbol)

            if withdrawn:
                # Read, and then unread by an audit of the filing. Saying
                # "never read" here would hide a withdrawal behind the
                # wording for a company nobody has looked at.
                counted = sum(withdrawn.values())
                names = ", ".join(
                    statement.value.replace("_", " ") for statement in withdrawn
                )

                return None, (
                    f"{symbol}'s {names} has been read, and an offline "
                    f"audit of the filing withdrew all {counted} of those "
                    "readings: the figures were taken from cells the filer "
                    "heads differently. The readings are still stored and "
                    "none of them is counted. Reading the statement again "
                    "is what restores authority, and is an explicit spend "
                    "— `movrvest observe-statements` takes it."
                )

            return None, (
                f"No financial statement has been read for {symbol}. "
                "Reading one is an explicit spend, and no surface takes "
                "it — `movrvest observe-statements` does."
            )

        # `measure` refuses a mixed-document mapping outright, which is
        # right for it and would be a crash here: the three statements
        # are three quorums that happen to share a key, and a company
        # observed across two filings holds consensuses of both. The
        # refusal is reported rather than raised.
        try:
            return measure(symbol, held), None
        except ValueError as refused:
            return None, str(refused)
