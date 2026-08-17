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
from app.domain.statement_language import EstablishedLanguage
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


class FinancialEvidenceStanding(StrEnum):
    """Why this platform holds, or does not hold, a financial understanding.

    The structured form of a distinction the composing service already
    drew in prose and nothing downstream could read. *Never read* and
    *read, then withdrawn by an audit* are different facts about this
    platform, and a consumer that could not tell them apart treated a
    withdrawal as an absence — which let a provider's three proxies
    score a company whose every statement reading had been audited away.

    The states are exhaustive over that service's own branches, so a
    consumer switches on this member rather than reading a sentence.
    """

    #: A `FinancialUnderstanding` was derived. Everything else here is a
    #: reason there is none.
    ESTABLISHED = "established"

    #: Readings are held and **none of them carries authority**: an
    #: offline audit of the filing withdrew every one. The evidence is
    #: still stored, still readable, and counts for nothing until a
    #: funded re-reading replaces it.
    WITHDRAWN_BY_AUDIT = "withdrawn by audit"

    #: No statement has ever been read for this security.
    NEVER_READ = "never read"

    #: Authoritative readings are held and no understanding can be
    #: derived from them — today, only a company observed across two
    #: filings, whose consensuses `measure` refuses to mix.
    UNMEASURABLE = "unmeasurable"


@dataclass(frozen=True, slots=True)
class IncomparableTopLine:
    """A consolidated top line this platform read and cannot rule on.

    The worded half of an accepted refusal. Where a filer strikes its
    consolidated total *after* financing cost — the shape every bank
    prints — this platform establishes the figure and has no
    profitability ruler for it: every threshold it applies compares a
    margin against gross revenue, and a denominator with a bank's
    largest single cost already deducted is not that quantity.

    So the figure is carried, with its evidence, and the absence of a
    ruler is **stated rather than left to look like missing evidence**.
    Invariant 10 in its semantic form: an established number is
    authority to report the number, never authority to invent what the
    number means. Nothing here is a score, a band, a threshold or a
    verdict, and no arithmetic is performed on the figure.
    """

    #: The filer's own row label, verbatim.
    label: str

    #: The figure as the filer printed it, verbatim. A string, because
    #: this layer reports the cell and computes nothing from it.
    printed: str

    #: The checked cell and its row, carried exactly as an established
    #: measure carries its basis — so an investor checks the claim
    #: against the document rather than trusting it.
    basis: tuple[ReportedFigure, ...] = ()

    #: The document this was read from, as an investor would cite it.
    source: str = ""

    #: The narrowest agreement beneath the figure.
    support: Agreement | None = None

    def stated(self) -> str:
        """Why the figure is held and no verdict follows from it."""

        cited = self.basis[0].stated() if self.basis else f'"{self.label}"'

        return (
            f"This platform read the company's consolidated top line — "
            f"{cited} — and it is struck after financing cost: the "
            "statement prints a net interest income subtotal above it, so "
            "interest expense is already deducted from the total. Every "
            "profitability threshold this platform applies compares a "
            "margin against gross revenue, and no comparable ruler for a "
            "top line struck after financing cost has been established. "
            "So no margin is computed from it, no profitability verdict "
            "is reached and no quality band is claimed. That is a limit "
            "of this platform's rulers, not a finding about the company."
        )


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

    #: Which financial language the income statement establishes, from
    #: the lines the filer printed. Reported, and consumed by nothing:
    #: `model_for` still derives the financial model from the business
    #: playbook, and this observation is not wired to it. What it would
    #: take to earn that connection is recorded in
    #: `docs/architecture/FINANCIAL_LANGUAGE_CORPUS.md`.
    #:
    #: None where no income-statement consensus was given, which is a
    #: different fact from a statement that was read and established
    #: neither marker.
    language: EstablishedLanguage | None = None

    #: The consolidated top line this platform established and has no
    #: profitability ruler for, where the statements establish one.
    #:
    #: Reported, and **consumed by no measure, factor, threshold or
    #: band**: it exists so that a company whose top line was read can be
    #: told apart from one whose statements printed nothing, and both
    #: from one this platform can rule on. `measures` above is untouched
    #: by it and every margin it carries stays absent for the reason its
    #: own consensus gave.
    #:
    #: None where the statements establish a gross total — the ordinary
    #: case, in which the existing ruler applies and there is nothing to
    #: refuse — and None where nothing was established at all.
    incomparable_top_line: IncomparableTopLine | None = None

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
