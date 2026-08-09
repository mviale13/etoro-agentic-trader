"""What the company's own statements measure, from consensus figures.

The statement stream's answer to `BusinessUnderstanding`, and the same
layer of the same architecture pointed at a second domain:

```text
CompanyKnowledgeConsensus            FinancialStatementConsensus × 3
          ↓                                      ↓
BusinessUnderstanding                 FinancialUnderstanding    ← this module
          ↓                                      ↓
PlaybookSelector → analysts            the financial analysts
```

The three rules that make the narrative layer trustworthy are the three
rules here, unchanged and for unchanged reasons:

- **Completely deterministic.** No model is asked and nothing is
  re-read. The same consensus in produces the same measures out. This
  is an arithmetic layer, not another reading.
- **Every number traces to two checked cells.** A margin is not a fact
  a filer states; it is this platform dividing one figure it read back
  out of a table by another figure it read back out of the same table.
  What travels with every measure is the figures it was computed from,
  each carrying the filer's own row label, column header and cell
  address — so an investor checks the arithmetic against the document
  rather than trusting it.
- **It never infers, and never compensates.** Where the consensus says
  *not established*, this says *not established*, in the consensus's own
  words. A statement that printed no gross profit line leaves gross
  margin absent; nothing reconstructs it from revenue and an expense
  the platform did not read as cost of revenue.

The fourth rule belongs to this domain in particular. **Nothing here is
scored, ranked or judged.** A current ratio of 0.8 is reported as 0.8;
whether that is comfortable or alarming is a rule table's business, and
rule tables live in the analysts one layer above. Facts, never
conclusions — invariant 5, at the seam where it is easiest to break.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.agreement import Agreement
from app.domain.financial_statements import StatementKind
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import ReportedFigure


class FinancialMeasure(StrEnum):
    """One quantity this platform computes from established figures.

    Every member is here because a named consumer asks for it, and the
    consumers are the four financial analysts whose rule tables already
    exist. A measure invented ahead of the rule table that scores it
    would be the taxonomy-first move this platform keeps shut out.

    `LIABILITIES_TO_EQUITY` is deliberately not called debt-to-equity.
    A filer prints "Total liabilities" as a line of its balance sheet
    and mostly does not print "total debt" at all, so the ratio this
    platform can evidence relates liabilities to equity — a different
    and larger quantity than the borrowings-only ratio the name
    "debt-to-equity" denotes. Naming it for the figure a provider would
    have supplied, rather than for the figures actually divided, is how
    a restatement gets back in wearing the right label.
    """

    GROSS_MARGIN = "gross_margin"
    OPERATING_MARGIN = "operating_margin"
    NET_MARGIN = "net_margin"

    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"

    CURRENT_RATIO = "current_ratio"
    LIABILITIES_TO_EQUITY = "liabilities_to_equity"

    OPERATING_CASH_FLOW = "operating_cash_flow"
    FREE_CASH_FLOW = "free_cash_flow"


#: What each measure is, in words a refusal and a surface can both carry.
MEASURE_NAMES: dict[FinancialMeasure, str] = {
    FinancialMeasure.GROSS_MARGIN: "Gross margin",
    FinancialMeasure.OPERATING_MARGIN: "Operating margin",
    FinancialMeasure.NET_MARGIN: "Net margin",
    FinancialMeasure.REVENUE_GROWTH: "Revenue growth",
    FinancialMeasure.EARNINGS_GROWTH: "Earnings growth",
    FinancialMeasure.CURRENT_RATIO: "Current ratio",
    FinancialMeasure.LIABILITIES_TO_EQUITY: "Liabilities to equity",
    FinancialMeasure.OPERATING_CASH_FLOW: "Operating cash flow",
    FinancialMeasure.FREE_CASH_FLOW: "Free cash flow",
}


class MeasureUnit(StrEnum):
    """What a measure's number means, so no surface has to guess.

    A margin and a current ratio are both dimensionless and read
    completely differently — 0.42 is 42% in one and 0.42 times in the
    other. A cash flow is neither: it is a quantity at the scale its
    caption states, which is why `EstablishedMeasure` keeps the caption.
    """

    #: A fraction, read as a percentage.
    FRACTION = "fraction"

    #: A multiple, read as "times".
    MULTIPLE = "multiple"

    #: A quantity of money, at the scale the caption states.
    CURRENCY = "currency"


#: How each measure's number is to be read.
MEASURE_UNITS: dict[FinancialMeasure, MeasureUnit] = {
    FinancialMeasure.GROSS_MARGIN: MeasureUnit.FRACTION,
    FinancialMeasure.OPERATING_MARGIN: MeasureUnit.FRACTION,
    FinancialMeasure.NET_MARGIN: MeasureUnit.FRACTION,
    FinancialMeasure.REVENUE_GROWTH: MeasureUnit.FRACTION,
    FinancialMeasure.EARNINGS_GROWTH: MeasureUnit.FRACTION,
    FinancialMeasure.CURRENT_RATIO: MeasureUnit.MULTIPLE,
    FinancialMeasure.LIABILITIES_TO_EQUITY: MeasureUnit.MULTIPLE,
    FinancialMeasure.OPERATING_CASH_FLOW: MeasureUnit.CURRENCY,
    FinancialMeasure.FREE_CASH_FLOW: MeasureUnit.CURRENCY,
}


@dataclass(frozen=True, slots=True)
class EstablishedMeasure:
    """One measure, computed from checked figures or absent with its reason.

    Field names mirror the consensus's deliberately: a measure reads the
    same whether it was established or not, and a consumer handles both
    without knowing which it was given.
    """

    measure: FinancialMeasure

    #: The number, or None with the reason worded beside it.
    value: float | None

    #: The checked figures the arithmetic consumed, in the order it
    #: consumed them. Empty exactly where the value is absent. This is
    #: what makes the measure checkable: every one of them carries the
    #: filer's row label, column header, printed text and cell address.
    basis: tuple[ReportedFigure, ...] = ()

    #: The arithmetic as an investor would check it against the filing.
    stated: str = ""

    #: The narrowest agreement among the consensus claims this measure
    #: consumed — a measure is exactly as established as the weakest
    #: figure beneath it. None where nothing was established.
    support: Agreement | None = None

    #: Why there is no number, in the consensus's own words where the
    #: gap is the consensus's, and in this layer's words where the
    #: arithmetic itself was refused. Two different facts.
    absent_because: str | None = None

    @property
    def is_established(self) -> bool:
        """Whether this platform computed the measure from checked figures."""

        return self.value is not None

    @property
    def unit(self) -> MeasureUnit:
        """How this measure's number is to be read."""

        return MEASURE_UNITS[self.measure]

    @property
    def label(self) -> str:
        """What to call this measure to an investor."""

        return MEASURE_NAMES[self.measure]


@dataclass(frozen=True, slots=True)
class FinancialUnderstanding:
    """What the filer's own statements measure, and how firmly.

    Everything here is derived from `FinancialStatementConsensus` objects
    by arithmetic. Nothing is read, nothing is inferred, and every
    absence is a consensus's own absence or a refused computation, each
    carrying which of the two it is.
    """

    symbol: str

    #: The document everything traces to, as an investor would cite it.
    source: str

    reading: Provenance

    #: The width beneath the whole, taken at its narrowest: a
    #: understanding is quorate only where every statement it consumed
    #: is, and the count reported is the smallest of theirs. Carried so
    #: no consumer can forget what the measures rest on.
    quorate: bool
    observation_count: int
    quorum: int

    #: Which statements this platform has consensus for. A measure whose
    #: statement is missing is absent for that reason, worded — which is
    #: a different fact from a statement that was read and printed no
    #: such line.
    statements: tuple[StatementKind, ...]

    #: One entry per measure, always: an absent measure is present as a
    #: worded absence, so a reader never infers whether a missing entry
    #: was refused, unestablished, or never attempted.
    measures: tuple[EstablishedMeasure, ...]

    def of(self, measure: FinancialMeasure) -> EstablishedMeasure | None:
        """This platform's answer for one measure."""

        for established in self.measures:
            if established.measure is measure:
                return established

        return None

    @property
    def established(self) -> tuple[EstablishedMeasure, ...]:
        """The measures computed from checked figures."""

        return tuple(measure for measure in self.measures if measure.is_established)

    @property
    def not_established(self) -> tuple[EstablishedMeasure, ...]:
        """The measures that are absent, each carrying its reason."""

        return tuple(measure for measure in self.measures if not measure.is_established)

    @property
    def narrow_support(self) -> tuple[EstablishedMeasure, ...]:
        """The established measures whose narrowest support fell short."""

        return tuple(
            measure
            for measure in self.established
            if measure.support is not None and not measure.support.settled
        )
